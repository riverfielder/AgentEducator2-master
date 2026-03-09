"""Agent化问答服务模块 - LangGraph版本"""
import traceback
import logging
import time
import json
import os
from typing import List, Dict, Any, Optional, Union

from langchain_core.tools import StructuredTool
from langchain.schema import AgentAction, AgentFinish
from langchain.callbacks.base import BaseCallbackHandler
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

# 导入LangSmith配置
from tools.knowledge_point_info_tool import KnowledgePointSearchInput
from config.langsmith_config import LangSmithConfig

# LangGraph支持检查
try:
    import langgraph
    SUPPORTS_LANGGRAPH = True
    #print(f"[INFO] LangGraph可用，版本: {langgraph.__version__}")
except ImportError:
    SUPPORTS_LANGGRAPH = False
    print("[ERROR] LangGraph不可用，请安装langgraph包")

# 初始化LangSmith
LangSmithConfig.setup_langsmith(
    project_name="AgentEducator-QA",
    enable_tracing=True
)

from .llm_service import llm_service
from .retriever_service import retriever_service
from config.agent_config import AgentConfig

# 创建专门的日志记录器
agent_logger = logging.getLogger('agent_qa')
agent_logger.setLevel(logging.INFO)


class LangGraphCallbackHandler(BaseCallbackHandler):
    """LangGraph Agent执行回调处理器"""
    
    def __init__(self, streaming_callback=None, tool_instances_map=None, user_mode="user"):
        self.streaming_callback = streaming_callback
        self.tool_instances_map = tool_instances_map or {}
        self.current_step = 0
        self.sources = []  # 收集所有检索到的文档
        
        # 用户体验模式控制 - 固定为user模式
        self.user_mode = "user"
        
        # Token控制机制
        self.token_buffer = []
        self.final_answer_started = False
        self.collecting_final_answer = False
        
        # 状态追踪
        self.current_tool = None
        self.execution_stats = {
            "start_time": None,
            "steps": 0,
            "tools_used": []
        }
        
        print("[FLOW] LangGraphCallbackHandler初始化，使用固定用户模式")

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        """工具开始执行时的回调"""
        self.current_step += 1
        tool_name = serialized.get("name", "unknown_tool")
        self.current_tool = tool_name
        self.execution_stats["steps"] = self.current_step
        self.execution_stats["tools_used"].append(tool_name)
        
        print(f"[FLOW] on_tool_start: tool={tool_name}, step={self.current_step}")
        
        # 发送工具开始事件
        if self.streaming_callback and hasattr(self.streaming_callback, 'send_tool_event'):
            tool_info = self._get_tool_display_info(tool_name, input_str)
            tool_start_event = {
                "type": "tool_start",
                "data": tool_info
            }
            self.streaming_callback.send_tool_event(f"[TOOL_EVENT]{json.dumps(tool_start_event)}[/TOOL_EVENT]")
        
        # 发送状态更新
        if self.streaming_callback:
            tool_names = {
                "video_search": "搜索视频内容",
                "course_search": "搜索课程资料", 
                "general_search": "搜索相关资料",
                "advanced_document_search": "高级文档搜索",
                "student_learning_analysis": "分析学习状态",
                # 教师专用工具
                "teacher_course_list": "查询课程列表",
                "teaching_guidance": "生成教学指导",
                "teacher_assignment_management": "管理作业",
                "teacher_teaching_assistant": "教学分析",
                "teacher_course_search": "搜索课程内容",
                "teacher_video_search": "搜索课程视频",
                "teacher_document_search": "搜索课程文档",
                "teacher_knowledge_point_info": "分析知识点信息",
                "teacher_course_overview": "分析课程概览"
            }
            friendly_name = tool_names.get(tool_name, tool_name)
            status_msg = f"正在{friendly_name}..."
            self._send_status_update(status_msg, "info")
    
    def _send_status_update(self, message: str, level: str = "info"):
        """发送状态更新"""
        if self.streaming_callback and hasattr(self.streaming_callback, 'send_tool_event'):
            status_event = {
                "type": "status_update",
                "data": {
                    "message": message,
                    "level": level,
                    "step": self.current_step,
                    "timestamp": time.time()
                }
            }
            self.streaming_callback.send_tool_event(f"[STATUS]{json.dumps(status_event)}[/STATUS]")

    def on_llm_new_token(self, token, **kwargs):
        """处理流式输出"""
        if not self.streaming_callback:
            return
            
        # 直接传输token，LangGraph处理更简单
        if self.streaming_callback:
            self.streaming_callback.on_llm_new_token(token)
    
    def on_tool_end(self, output: str, **kwargs) -> None:
        """工具执行结束时的回调"""
        print(f"[FLOW] on_tool_end: tool={self.current_tool}")
        
        # 发送工具结束事件
        if self.streaming_callback and hasattr(self.streaming_callback, 'send_tool_event'):
            tool_result_event = {
                "type": "tool_result",
                "data": {
                    "success": True,
                    "message": "执行完成",
                    "documents_count": 0  # 默认值，稍后会被工具实例的信息覆盖
                }
            }
            self.streaming_callback.send_tool_event(f"[TOOL_EVENT]{json.dumps(tool_result_event)}[/TOOL_EVENT]")
        
        # 从当前工具收集文档
        if self.current_tool and self.current_tool in self.tool_instances_map:
            tool_instance = self.tool_instances_map[self.current_tool]
            if hasattr(tool_instance, 'retrieved_docs') and tool_instance.retrieved_docs:
                doc_count = len(tool_instance.retrieved_docs)
                self.sources.extend(tool_instance.retrieved_docs)
                print(f"[FLOW] 从工具 {self.current_tool} 收集了 {doc_count} 个文档")
                
                # 更新工具结果事件中的文档数量
                if self.streaming_callback and hasattr(self.streaming_callback, 'send_tool_event'):
                    updated_result_event = {
                        "type": "tool_result",
                        "data": {
                            "success": True,
                            "message": f"找到 {doc_count} 个相关文档",
                            "documents_count": doc_count
                        }
                    }
                    self.streaming_callback.send_tool_event(f"[TOOL_EVENT]{json.dumps(updated_result_event)}[/TOOL_EVENT]")
                tool_instance.retrieved_docs.clear()

    def collect_final_sources(self):
        """最终收集所有源文档"""
        print(f"[FLOW] ========== 最终收集源文档 ==========")
        
        # 从所有工具实例中收集文档
        collected_count = 0
        for t_name, t_instance in self.tool_instances_map.items():
            if hasattr(t_instance, 'retrieved_docs') and t_instance.retrieved_docs:
                doc_count = len(t_instance.retrieved_docs)
                self.sources.extend(t_instance.retrieved_docs)
                collected_count += doc_count
                print(f"[FLOW] 从工具 {t_name} 最终收集了 {doc_count} 个文档")
                t_instance.retrieved_docs.clear()
        
        print(f"[FLOW] 总共收集了 {len(self.sources)} 个源文档")
        return self.sources


class AgentQAService:
    """Agent化问答服务"""
    
    def __init__(self):
        pass  # 移除未使用的缓存机制
        
    def create_qa_agent(self, video_context=None, course_context=None, document_context=None, history=None, streaming_callback=None, user_id=None):
        """创建Agent化的问答系统
        
        Args:
            video_context: 视频上下文字符串 (格式: VIDEO_ID:xxx|TITLE:xxx|SUMMARY:xxx|KEYWORDS:xxx)
            course_context: 课程上下文字符串 (格式: COURSE_ID:xxx|NAME:xxx|CORE_CONCEPTS:xxx|...)
            document_context: 文档上下文字符串 (格式: DOCUMENT_ID:xxx|TITLE:xxx|DESCRIPTION:xxx|...)
            history: 对话历史
            streaming_callback: 流式回调
        """
        try:
            # 导入全局序号管理器（避免循环导入）
            from tools.global_index_manager import global_source_index_manager
            
            # 重置全局序号计数器，确保每次新的对话序号从1开始
            global_source_index_manager.reset()
            
            # 解析上下文信息
            # 直接使用原始context_string，不进行解析
            video_info = video_context if video_context else ""
            course_info = course_context if course_context else ""
            document_info = document_context if document_context else ""
            
            # 构建增强的系统提示词
            system_prompt = self._build_enhanced_system_prompt(video_info, course_info, document_info, history)

            # 格式化历史记录
            formatted_history = self._format_chat_history(history) if history else "暂无历史记录"
            
            agent_executor = self._create_agent_impl(
                 streaming_callback, 
                system_prompt=system_prompt,
                video_context=video_info,
                course_context=course_info,
                document_context=document_info,
                user_id=user_id
            )
            
            # Note: 移除了memory支持以避免LangChain memory与agent输出键不匹配的问题
            # 如果需要多轮对话，可以在上层应用中管理历史记录
            
            return agent_executor, None
            
        except Exception as e:
            traceback.print_exc()
            # 移除flask依赖的日志记录，改用标准日志
            logger = logging.getLogger(__name__)
            logger.error(f"创建Agent问答系统失败: {str(e)}")
            return None, f"创建Agent问答系统失败: {str(e)}"
    
    def _create_agent_impl(self, streaming_callback, system_prompt=None, video_context=None, course_context=None, document_context=None, user_id=None):
        """实际创建LangGraph Agent的实现"""
        if not SUPPORTS_LANGGRAPH:
            raise ImportError("LangGraph不可用，请安装langgraph包")
            
        # 创建LLM
        llm = llm_service.create_chat_llm(
            streaming=streaming_callback is not None,
            callback=streaming_callback
        )
        
        # 创建结构化工具列表和工具实例映射，传递上下文信息
        # 不再传递index，工具层会自己获取索引
        tools, tool_instances_map = self._create_structured_tools(user_id=user_id)
        
        # 为所有工具设置流式回调
        if streaming_callback:
            for tool_instance in tool_instances_map.values():
                tool_instance.set_streaming_callback(streaming_callback)
        
        print("[FLOW] 使用LangGraph ReAct Agent")
        
        # 创建内存检查点
        memory = MemorySaver()
        
        # 使用LangGraph创建ReAct Agent（使用默认提示）
        try:
            agent_executor = create_react_agent(
                llm, 
                tools, 
                checkpointer=memory
            )
            print("✅ LangGraph Agent创建成功")
        except Exception as e:
            print(f"❌ LangGraph Agent创建失败: {e}")
            raise
        
        # 添加自定义回调
        agent_callback = LangGraphCallbackHandler(streaming_callback, tool_instances_map)
        
        # 存储工具实例引用以便后续获取文档
        agent_executor._tool_instances_map = tool_instances_map
        agent_executor._agent_callback = agent_callback
        
        # 存储系统提示以便在查询时使用
        if system_prompt:
            agent_executor._system_prompt = system_prompt
            print(f"[FLOW] 已存储自定义系统提示，长度: {len(system_prompt)}")
        
        # 存储上下文信息
        agent_executor._video_context = video_context
        agent_executor._course_context = course_context
        
        print(f"[FLOW] LangGraph ReAct Agent创建完成")
        print(f"[FLOW] 工具数量: {len(tools)}")
        print(f"[FLOW] 工具列表: {list(tool_instances_map.keys())}")
        
        return agent_executor
    
    def _create_structured_tools(self, user_id=None):
        """创建结构化工具列表 - 不依赖ID，总是创建所有工具"""
        # 在函数内部导入避免循环导入
        from tools.video_retrieval_tool import VideoRetrievalTool, VideoSearchInput
        from tools.course_retrieval_tool import CourseRetrievalTool, CourseSearchInput
        from tools.document_retrieval_tool import DocumentRetrievalTool, DocumentSearchInput
        from tools.knowledge_point_info_tool import KnowledgePointInfoTool
        from tools.general_search_tool import GeneralSearchTool

        tools = []
        tool_instances_map = {}  # 工具名称到实例的映射
        
        # 视频检索工具 - 总是创建，可以动态指定视频
        video_tool = VideoRetrievalTool(retriever_service, user_id=user_id)
        tool_instances_map["video_search"] = video_tool
        
        video_structured_tool = StructuredTool.from_function(
            func=video_tool.search,
            name=video_tool.name,
            description=video_tool.description,
            args_schema=VideoSearchInput
        )
        tools.append(video_structured_tool)
        
        # 课程检索工具 - 总是创建，可以动态指定课程
        course_tool = CourseRetrievalTool(retriever_service, user_id=user_id)
        tool_instances_map["course_search"] = course_tool
        

        course_structured_tool = StructuredTool.from_function(
            func=course_tool.search,
            name=course_tool.name,
            description=course_tool.description,
            args_schema=CourseSearchInput
        )
        tools.append(course_structured_tool)
        
        # 通用搜索工具 - 总是创建，可以动态指定搜索范围
        general_search_tool = GeneralSearchTool(retriever_service, user_id=user_id)
        tool_instances_map["general_search"] = general_search_tool
        general_structured_tool = StructuredTool.from_function(
            func=general_search_tool.search,
            name=general_search_tool.name,
            description=general_search_tool.description
        )
        tools.append(general_structured_tool)
        
        
        # 文档检索工具 - 总是创建，可以动态指定文档
        document_tool = DocumentRetrievalTool(retriever_service, user_id=user_id)
        tool_instances_map["document_search"] = document_tool
        
        document_structured_tool = StructuredTool.from_function(
            func=document_tool.search,
            name=document_tool.name,
            description=document_tool.description,
            args_schema=DocumentSearchInput
        )
        tools.append(document_structured_tool)

        # 知识点信息工具 - 总是创建
        knowledge_point_tool = KnowledgePointInfoTool(user_id=user_id)
        tool_instances_map["knowledge_point_info"] = knowledge_point_tool
        
        knowledge_point_structured_tool = StructuredTool.from_function(
            func=knowledge_point_tool.search,
            name="knowledge_point_info",
            description="获取具体知识点的相关资源和关联信息，包括相关视频、文档和练习题",
            args_schema=KnowledgePointSearchInput
        )
        tools.append(knowledge_point_structured_tool)

        # 作业检索工具 - 如果提供了user_id
        if user_id:
            from tools.assignment_retrieval_tool import AssignmentRetrievalTool, AssignmentSearchInput
            assignment_tool = AssignmentRetrievalTool(user_id=user_id)
            tool_instances_map["list_assignment"] = assignment_tool
            
            assignment_structured_tool = StructuredTool.from_function(
                func=assignment_tool.search,
                name=assignment_tool.name,
                description=assignment_tool.description,
                args_schema=AssignmentSearchInput
            )
            tools.append(assignment_structured_tool)
            
            # 学生学习分析工具
            from tools.student_learning_analyzer import StudentLearningAnalyzer, StudentLearningInput
            learning_analyzer = StudentLearningAnalyzer(user_id=user_id)
            tool_instances_map["student_learning_analysis"] = learning_analyzer
            
            learning_analyzer_tool = StructuredTool.from_function(
                func=learning_analyzer.search,
                name=learning_analyzer.name,
                description=learning_analyzer.description,
                args_schema=StudentLearningInput
            )
            tools.append(learning_analyzer_tool)
            
            # 检查是否为教师用户，如果是则添加教师专用工具
            if self._is_teacher_user(user_id):
                # 教师课程列表工具
                from tools.teacher_course_list_tool import TeacherCourseListTool, TeacherCourseListInput
                teacher_course_tool = TeacherCourseListTool(user_id=user_id)
                tool_instances_map["teacher_course_list"] = teacher_course_tool
                
                teacher_course_structured_tool = StructuredTool.from_function(
                    func=teacher_course_tool.search,
                    name=teacher_course_tool.name,
                    description=teacher_course_tool.description,
                    args_schema=TeacherCourseListInput
                )
                tools.append(teacher_course_structured_tool)
                
                # 教学安排指导工具
                from tools.teaching_guidance_tool import TeachingGuidanceTool, TeachingGuidanceInput
                teaching_guidance_tool = TeachingGuidanceTool(user_id=user_id)
                tool_instances_map["teaching_guidance"] = teaching_guidance_tool
                
                teaching_guidance_structured_tool = StructuredTool.from_function(
                    func=teaching_guidance_tool.search,
                    name=teaching_guidance_tool.name,
                    description=teaching_guidance_tool.description,
                    args_schema=TeachingGuidanceInput
                )
                tools.append(teaching_guidance_structured_tool)
                
                # 教师作业管理工具
                from tools.teacher_assignment_management_tool import TeacherAssignmentManagementTool, TeacherAssignmentManagementInput
                assignment_management_tool = TeacherAssignmentManagementTool(user_id=user_id)
                tool_instances_map["teacher_assignment_management"] = assignment_management_tool
                
                assignment_management_structured_tool = StructuredTool.from_function(
                    func=assignment_management_tool.search,
                    name=assignment_management_tool.name,
                    description=assignment_management_tool.description,
                    args_schema=TeacherAssignmentManagementInput
                )
                tools.append(assignment_management_structured_tool)
                
                # 教师教学辅助工具
                from tools.teacher_teaching_assistant_tool import TeacherTeachingAssistantTool, TeacherTeachingAssistantInput
                teaching_assistant_tool = TeacherTeachingAssistantTool(user_id=user_id)
                tool_instances_map["teacher_teaching_assistant"] = teaching_assistant_tool
                
                teaching_assistant_structured_tool = StructuredTool.from_function(
                    func=teaching_assistant_tool.search,
                    name=teaching_assistant_tool.name,
                    description=teaching_assistant_tool.description,
                    args_schema=TeacherTeachingAssistantInput
                )
                tools.append(teaching_assistant_structured_tool)

        
        print(f"[FLOW] 创建了 {len(tools)} 个结构化工具: {list(tool_instances_map.keys())}")
        print(f"[FLOW] 所有工具均支持动态指定目标（视频/课程/文档）")
        return tools, tool_instances_map
    
    def _is_teacher_user(self, user_id: str) -> bool:
        """检查用户是否为教师"""
        try:
            from models.models import Users, db
            
            def check_teacher():
                user = db.session.query(Users).filter(Users.id == user_id, Users.is_deleted == False).first()
                return user and user.role == 'teacher'
            
            # 在应用上下文中执行查询
            from flask import current_app, has_app_context
            if not has_app_context():
                from app import create_app
                app = create_app()
                with app.app_context():
                    return check_teacher()
            else:
                return check_teacher()
                
        except Exception as e:
            print(f"[ERROR] 检查教师用户失败: {e}")
            return False
        
    def query(self, agent_executor, question: str) -> Dict[str, Any]:
        """使用Agent执行查询（无历史记录）"""
        return self.query_with_history(agent_executor, question, history=None)
        
    def query_with_history(self, agent_executor, question: str, history: list = None) -> Dict[str, Any]:
        """使用LangGraph Agent执行查询，支持对话历史"""
        try:
            print(f"[FLOW] ========== 开始执行LangGraph查询（含历史） ==========")
            print(f"[FLOW] 问题: {question[:50]}...")
            print(f"[FLOW] 历史记录数量: {len(history) if history else 0}")
            
            # 构建LangGraph所需的消息格式
            messages = []
            
            # 添加系统提示（如果存在）
            if hasattr(agent_executor, '_system_prompt') and agent_executor._system_prompt:
                messages.append(("system", agent_executor._system_prompt))
                print(f"[FLOW] 已添加系统提示")
            
            # 如果有历史记录，构建对话上下文
            if history and len(history) > 0:
                print(f"[FLOW] 开始处理历史记录，共 {len(history)} 条")
                # 将历史记录转换为消息格式
                processed_count = 0
                for entry in history[-5:]:  # 只保留最近5条历史
                    if isinstance(entry, dict):
                        if 'question' in entry and 'answer' in entry:
                            messages.append(("human", entry['question']))
                            messages.append(("ai", entry['answer']))
                            processed_count += 1
                            print(f"[FLOW] 处理历史记录 (question/answer格式): {entry['question'][:30]}...")
                        elif 'human' in entry and 'ai' in entry:
                            messages.append(("human", entry['human']))
                            messages.append(("ai", entry['ai']))
                            processed_count += 1
                            print(f"[FLOW] 处理历史记录 (human/ai格式): {entry['human'][:30]}...")
                        elif 'role' in entry and 'content' in entry:
                            # 处理前端发送的标准格式 {'role': 'user/assistant', 'content': '...'}
                            if entry['role'] == 'user':
                                messages.append(("human", entry['content']))
                                processed_count += 1
                                print(f"[FLOW] 处理历史记录 (role/content格式-user): {entry['content'][:30]}...")
                            elif entry['role'] == 'assistant':
                                messages.append(("ai", entry['content']))
                                print(f"[FLOW] 处理历史记录 (role/content格式-assistant): {entry['content'][:30]}...")
                
                print(f"[FLOW] 已构建包含历史的消息，历史条目数: {len(history)}，实际处理: {processed_count} 条")
            
            # 添加当前问题
            messages.append(("user", question))
            
            # 配置用于会话的thread（对话状态管理）
            config = {"configurable": {"thread_id": f"session_{int(time.time())}"}}
            
            # 使用LangGraph Agent执行查询
            events = []
            final_content = ""
            
            # 获取回调处理器
            agent_callback = getattr(agent_executor, '_agent_callback', None)
            
            for event in agent_executor.stream(
                {"messages": messages}, 
                config,
                stream_mode="values"
            ):
                events.append(event)
                # 实时处理消息，获取最新的AI回复
                if "messages" in event:
                    event_messages = event["messages"]
                    for msg in event_messages:
                        if hasattr(msg, 'type') and msg.type == 'ai' and hasattr(msg, 'content'):
                            final_content = msg.content
            
            print(f"[FLOW] LangGraph执行完成，共 {len(events)} 个事件")
            
            # 如果没有获取到内容，尝试从最后一个事件中提取
            if not final_content and events:
                last_event = events[-1]
                messages_in_event = last_event.get("messages", [])
                if messages_in_event:
                    final_message = messages_in_event[-1]
                    if hasattr(final_message, 'content'):
                        final_content = final_message.content
                    else:
                        final_content = str(final_message)
            
            print(f"[FLOW] 🔍 最终LLM回复内容（前200字符）: {final_content[:200]}...")
            print(f"[FLOW] 🔍 最终LLM回复内容长度: {len(final_content)}")
            
            # 源文档收集
            source_documents = []
            if agent_callback:
                source_documents = agent_callback.collect_final_sources()
                print(f"[FLOW] ✅ 从回调收集到 {len(source_documents)} 个源文档")
            
            # 如果回调没有收集到文档，直接从工具收集
            if not source_documents and hasattr(agent_executor, '_tool_instances_map'):
                print(f"[FLOW] 使用备用方案从工具直接收集")
                for tool_name, tool_instance in agent_executor._tool_instances_map.items():
                    if hasattr(tool_instance, 'retrieved_docs') and tool_instance.retrieved_docs:
                        source_documents.extend(tool_instance.retrieved_docs)
                        print(f"[FLOW] 从工具 {tool_name} 收集 {len(tool_instance.retrieved_docs)} 个文档")
                if source_documents:
                    print(f"[FLOW] ✅ 备用方案收集到 {len(source_documents)} 个源文档")
            
            if not source_documents:
                print(f"[FLOW] ⚠️  未能收集到任何源文档")
            
            result_dict = {
                "result": final_content or "LangGraph执行完成，但未获取到回复内容",
                "source_documents": source_documents,
                "intermediate_steps": events  # LangGraph的事件作为中间步骤
            }
            
            print(f"[FLOW] ========== LangGraph查询完成（含历史） ==========")
            print(f"[FLOW] 返回源文档数量: {len(source_documents)}")
            print(f"[FLOW] 最终答案长度: {len(final_content)}")
            
            return result_dict
            
        except Exception as e:
            print(f"[FLOW] ❌ LangGraph查询执行失败: {str(e)}")
            traceback.print_exc()
            return {
                "result": f"LangGraph查询执行失败: {str(e)}",
                "source_documents": [],
                "intermediate_steps": []
            }

    def _format_chat_history(self, history: list) -> str:
        """格式化对话历史为字符串"""
        if not history:
            return ""
        
        formatted_history = []
        for i, entry in enumerate(history[-100:], 1):  # 只取最近100条历史
            if isinstance(entry, dict):
                if 'role' in entry and 'content' in entry:
                    if entry['role'] == 'user':
                        formatted_history.append(f"Q{i}: {entry['content']}")
                    elif entry['role'] == 'assistant':
                        formatted_history.append(f"A{i}: {entry['content']}")
        
        return "\n".join(formatted_history)
    

    
    def _build_enhanced_system_prompt(self, video_info, course_info,document_info, history):
        """构建包含丰富上下文信息的系统提示词"""
        prompt_parts = [
            "你是一个专业的教育助手，专门帮助用户**检索和讲解**教学内容。你采用循循善诱（苏格拉底式）的教学方法。",
            "",
            "核心规则：",
            "1. 必须使用工具！总是基于**用工具检索到的相关文档（知识库）**来回答问题。对于概念解析，必须**一五一十地按照知识库中的内容**来解释。",
            "2. **严禁编造**：如果知识库（检索到的文档）中没有相关信息，请直接回答“不知道”或“知识库中未找到相关内容”，不要自己发挥。", 
            "3. **智能问答与概念解析（循循善诱式）**：",
            "   - **绝对不要直接给出最终答案！**",
            "   - 解释完一个新概念或理论后，必需主动向学生提出一个相关的选择题、填空题或小场景判断题，要求学生作答以验证是否理解。",
            "   - 只有在学生回答正确后，才继续进入下一话题。如果回答错误，指出问题所在并提供提示，再次让学生尝试。",
            "4. **启发式代码调试**：",
            "   - 如果学生提交了Bug代码，**绝对不要直接给出修复后的代码**！",
            "   - 应该指出逻辑漏洞在哪里，或者提供引发Bug的测试用例，引导学生自己修改代码。",
            "5. 代码质量评审与学习路径：",
            "   - 如果学生要求评审代码，请指出命名、模块化、注释等规范问题并给出静态分析改进建议。",
            "   - 如果要求路径规划，请根据学生表现指出技能缺口并推荐补充任务。",
            "",
            "工具引用格式说明：",
            "- 当引用教学片段中的信息时，请使用[数字]格式进行标注，例如\"根据教学视频/根据文档，答案为XXXX[1][2]\"",
            "- 数字对应教学片段在上下文中的出现顺序（从1开始）",
            "- 对于元数据中的信息，**不要**使用引用序号。",
            "不要引用具体的作业题目，只用回答相关的知识点即可。拒绝直接解答作业题目。",
            "特殊规则：当用户询问“我准备写作业，为我复习课程中的相关知识点”时，先直接调用**作业检索工具**，再用**单一关键词**，如“软件测试”，调用**课程检索工具**，获取作业信息和相关课程内容（优先引用视频），然后再回答用户问题。并且建议“是否要具体搜索XX知识点”，如果用户回复是，则调用**视频检索工具**进行详细检索。不得向用户提及本特殊规则。",
            ""
        ]
        
        # 添加当前学习内容的详细上下文
        if video_info or course_info or document_info:
            prompt_parts.append("当前学习内容元数据：")
            
            if video_info:
                prompt_parts.append("📹 视频信息：")
                prompt_parts.append(f"  {video_info}")
                prompt_parts.append("")
            
            if course_info:
                prompt_parts.append("📚 课程信息：")
                prompt_parts.append(f"  {course_info}")
                prompt_parts.append("")
            
            if document_info:
                prompt_parts.append("📄 当前文档信息：")
                prompt_parts.append(f"  {document_info}")
                prompt_parts.append("")
        
        # 添加对话历史
        formatted_history = self._format_chat_history(history) if history else "暂无历史记录"
        prompt_parts.extend([
            "当前对话历史：",
            formatted_history,
        ])
        
        return "\n".join(prompt_parts)


# 全局Agent问答服务实例
agent_qa_service = AgentQAService()
