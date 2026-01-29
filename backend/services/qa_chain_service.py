"""问答链服务模块"""
import traceback
from flask import current_app, has_app_context
from langchain.chains import RetrievalQA, LLMChain, ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain as LLMChainForDocs
from .llm_service import llm_service
from .memory_service import memory_service
from .retriever_service import retriever_service
from .cache_service import get_video_info, get_course_info, get_video_keywords, get_course_keywords, get_video_summary
from .agent_qa_service import agent_qa_service


class NumberedStuffDocumentsChain(StuffDocumentsChain):
    """自定义文档组合链，支持文档编号"""
    
    def _get_inputs(self, docs, **kwargs):
        # 为文档添加编号
        formatted_docs = []
        for i, doc in enumerate(docs, 1):
            formatted_doc = f"教学片段{i}: {doc.page_content}"
            formatted_docs.append(formatted_doc)
        
        document_string = self.document_separator.join(formatted_docs)
        inputs = {self.document_variable_name: document_string}
        inputs.update(kwargs)
        return inputs


class QAChainService:
    """问答链服务"""
    
    def __init__(self):
        self.agent_mode = False  # 控制是否使用Agent模式
        
    def set_agent_mode(self, enabled: bool):
        """设置Agent模式开关"""
        self.agent_mode = enabled
        
    def create_qa_chain(self, video_id, course_id, index, history=None, streaming_callback=None, use_agent=None, video_contexts=None, course_contexts=None, document_contexts=None, user_id=None):
        """创建问答链（支持Agent模式和多资源contexts）"""
        # 始终使用Agent模式，传递上下文字符串而不是原始ID
        return self._create_agent_qa(video_id, course_id, history, streaming_callback, video_contexts, course_contexts, document_contexts, user_id)

    
    def _create_agent_qa(self, video_id, course_id, history=None, streaming_callback=None, video_contexts=None, course_contexts=None, document_contexts=None, user_id=None):
        """创建Agent化的问答系统"""
        # 使用提供的contexts
        video_context = '|||'.join(video_contexts) if video_contexts else None
        course_context = '|||'.join(course_contexts) if course_contexts else None
        document_context = '|||'.join(document_contexts) if document_contexts else None
            
        if not has_app_context():
            from app import create_app
            app = create_app()
            with app.app_context():
                return agent_qa_service.create_qa_agent(video_context, course_context, document_context, history, streaming_callback, user_id)
        else:
            return agent_qa_service.create_qa_agent(video_context, course_context, document_context, history, streaming_callback, user_id)
    

    
    def query_with_agent(self, agent_executor, question: str, history: list = None):
        """使用Agent执行查询（支持历史记录）"""
        if history:
            return agent_qa_service.query_with_history(agent_executor, question, history)
        else:
            return agent_qa_service.query(agent_executor, question)


    def _build_context_info(self, video_id, course_id):
        """构建上下文信息"""
        context = {}
        
        try:
            # 获取视频信息
            if video_id:
                video_title, video_course_id = get_video_info(video_id)
                if video_title:
                    context['video_title'] = video_title
                    # 如果没有明确指定课程ID，使用视频所属的课程ID
                    if not course_id and video_course_id:
                        course_id = video_course_id
                  # 获取视频知识点
                video_keywords = get_video_keywords(video_id, limit=20)
                video_summary = get_video_summary(video_id)
                if video_summary:
                    context['video_summary'] = video_summary
                if video_keywords:
                    context['video_keywords'] = [kw['name'] for kw in video_keywords]

            # 获取课程信息
            if course_id:
                course_name = get_course_info(course_id)
                if course_name:
                    context['course_name'] = course_name
                
                # 获取课程知识点
                course_keywords = get_course_keywords(course_id, limit=10)
                if course_keywords:
                    # 按重要性分类知识点
                    core_concepts = [kw['name'] for kw in course_keywords if kw['category'] == 'core_concept']
                    main_modules = [kw['name'] for kw in course_keywords if kw['category'] == 'main_module']
                    specific_points = [kw['name'] for kw in course_keywords if kw['category'] == 'specific_point']
                    
                    context['course_keywords'] = {
                        'core_concepts': core_concepts[:3],  # 取前3个一级知识点
                        'main_modules': main_modules[:4],    # 取前4个二级知识点
                        'specific_points': specific_points[:5]  # 取前5个三级知识点
                    }
                    
        except Exception as e:
            if has_app_context():
                current_app.logger.warning(f"构建上下文信息时出错: {str(e)}")
        
        return context

    def _build_video_context_string(self, video_id):
        """构建视频上下文字符串，包含视频的详细元数据"""
        try:
            context_parts = [f"VIDEO_ID:{video_id}"]
            
            # 获取视频基本信息
            video_title, video_course_id = get_video_info(video_id)
            if video_title:
                context_parts.append(f"TITLE:{video_title}")
            if video_course_id:
                context_parts.append(f"BELONGS_TO_COURSE:{video_course_id}")
            
            # 获取视频摘要
            video_summary = get_video_summary(video_id)
            if video_summary:
                # 限制摘要长度，避免上下文过长
                summary = video_summary[:500] + "..." if len(video_summary) > 500 else video_summary
                context_parts.append(f"SUMMARY:{summary}")
            
            # 获取视频关键词
            video_keywords = get_video_keywords(video_id, limit=15)
            if video_keywords:
                keywords = [kw['name'] for kw in video_keywords]
                context_parts.append(f"KEYWORDS:{','.join(keywords)}")
            
            return "|".join(context_parts)
            
        except Exception as e:
            if has_app_context():
                current_app.logger.warning(f"构建视频上下文字符串时出错: {str(e)}")
            return f"VIDEO_ID:{video_id}"  # 出错时返回基本信息
    
    def _build_course_context_string(self, course_id):
        """构建课程上下文字符串，包含课程的详细元数据"""
        try:
            context_parts = [f"COURSE_ID:{course_id}"]
            
            # 获取课程基本信息
            course_name = get_course_info(course_id)
            if course_name:
                context_parts.append(f"NAME:{course_name}")
            
            # 获取课程关键词并分类
            course_keywords = get_course_keywords(course_id, limit=20)
            if course_keywords:
                # 按重要性分类关键词
                core_concepts = [kw['name'] for kw in course_keywords if kw['category'] == 'core_concept']
                main_modules = [kw['name'] for kw in course_keywords if kw['category'] == 'main_module']
                specific_points = [kw['name'] for kw in course_keywords if kw['category'] == 'specific_point']
                
                if core_concepts:
                    context_parts.append(f"CORE_CONCEPTS:{','.join(core_concepts[:5])}")
                if main_modules:
                    context_parts.append(f"MAIN_MODULES:{','.join(main_modules[:5])}")
                if specific_points:
                    context_parts.append(f"SPECIFIC_POINTS:{','.join(specific_points[:8])}")
            
            return "|".join(context_parts)
            
        except Exception as e:
            if has_app_context():
                current_app.logger.warning(f"构建课程上下文字符串时出错: {str(e)}")
            return f"COURSE_ID:{course_id}"  # 出错时返回基本信息

    def _build_video_chat_prompt(self, context_info):
        """构建视频聊天的prompt模板"""
        prompt_parts = [
            "你是一名专业的教育内容讲解助手，正在为学生解答关于特定视频内容的问题。"
        ]
        
        # 添加视频上下文信息
        if 'video_title' in context_info:
            prompt_parts.append(f"\n当前视频: {context_info['video_title']}")
        if 'video_summary' in context_info:
            prompt_parts.append(f"视频摘要: {context_info['video_summary']}")

        if 'course_name' in context_info:
            prompt_parts.append(f"所属课程: {context_info['course_name']}")
        
        if 'video_keywords' in context_info and context_info['video_keywords']:
            keywords_str = "、".join(context_info['video_keywords'])
            prompt_parts.append(f"视频关键概念: {keywords_str}")
        

        # 添加检索文档和回答指引
        prompt_parts.extend([
            "\n以下是检索到的相关教学文档:",
            "{context}",
            "\n回答指引:",
            "- 当引用上述教学片段中的信息时，请使用[数字]格式进行标注，例如\"答案XXXX[1]\"",
            "- 数字对应教学片段在上下文中的出现顺序（从1开始）",
            "- 根据视频的具体内容和关键概念来回答问题，但是不必用括号标注对于关键概念的引用",
            "- 如果问题与当前视频内容相关，请重点关注视频相关的信息",
            "- 请确保引用标注与文档顺序严格对应，不要混淆编号",
            "\n用户问题: {question}",
            "\n请基于上述文档和视频上下文信息回答问题，并正确标注引用来源："
        ])
        
        return "\n".join(prompt_parts)




# 全局问答链服务实例
qa_chain_service = QAChainService()
