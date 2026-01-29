"""流式响应处理服务模块"""
import json
import logging
import traceback
from queue import Queue
from threading import Thread
from flask import current_app
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from .llm_service import llm_service
from .memory_service import memory_service                

from .callbacks import CustomStreamingCallback, StatusNotifier
from .chat_service import chat_service
from .qa_chain_service import qa_chain_service
from .source_service import source_service


class StreamingService:
    """流式响应处理服务"""
    def create_agent_stream_generator(self, query, session_id, history, video_contexts=None, course_contexts=None, document_contexts=None, user_id=None):
        """创建Agent模式的流式生成器"""
        queue = Queue()
        answer_content = ""
        sources = []
        
        def generate():
            nonlocal answer_content, sources
            
            callback = CustomStreamingCallback(queue)
            callback.answer_content = answer_content  # 同步引用
            
            app = current_app._get_current_object()
            
            def process_query():
                nonlocal answer_content, sources
                try:
                    # 状态通知
                    notifier = StatusNotifier(queue)
                    notifier.notify_analysis_start()
                    
                    # 创建Agent - 支持多资源context
                    agent_executor, error = qa_chain_service.create_qa_chain(
                        None, None, None, history, callback, use_agent=True,
                        video_contexts=video_contexts, course_contexts=course_contexts, 
                        document_contexts=document_contexts, user_id=user_id
                    )
                    
                    if error:
                        raise Exception(error)
                    
                    notifier.notify_generation_start()
                    # 使用Agent执行查询（传递历史记录）
                    result = qa_chain_service.query_with_agent(agent_executor, query, history)
                    
                    # 确保回调内容被获取
                    if callback.answer_content:
                        answer_content = callback.answer_content
                    else:
                        answer_content = result.get("result", "")
                        # 如果没有流式输出，直接发送完整结果
                        queue.put(answer_content)
                    # 处理源文档（如果有）
                    if result.get("source_documents"):
                        sources = source_service.process_source_documents(
                            result["source_documents"], app
                        )
                    # 处理Agent的中间步骤信息
                    intermediate_steps = result.get("intermediate_steps", [])
                    if intermediate_steps:
                        # 可以在这里处理Agent的推理步骤
                        logger = logging.getLogger(__name__)
                        logger.info(f"Agent执行了 {len(intermediate_steps)} 个步骤")
                    
                    queue.put("[END]")
                    
                    # 保存AI回复
                    with app.app_context():
                        if chat_service.save_message_to_db(session_id, 'assistant', answer_content):
                            current_app.logger.info(f"Agent模式回复已保存，token数: {callback.token_count}")
                    
                    queue.put(json.dumps({
                        "sources": sources, 
                        "session": {"sessionId": str(session_id)},
                        "stats": {"tokens": callback.token_count, "agent_steps": len(intermediate_steps)},
                        "mode": "agent"
                    }))
                    
                except Exception as e:
                    with app.app_context():
                        current_app.logger.error(f"Agent模式处理失败: {str(e)}")
                        print(traceback.format_exc())
                    
                    # 保存错误回复
                    if answer_content.strip():
                        error_content = answer_content + f"\n\n[Agent处理过程中出现错误: {str(e)}]"
                        with app.app_context():
                            chat_service.save_message_to_db(session_id, 'assistant', error_content)
                    
                    queue.put(f"Agent处理请求失败: {str(e)}")
                    queue.put("[END]")
                    queue.put(json.dumps({
                        "sources": [], 
                        "session": {"sessionId": str(session_id)},
                        "error": str(e),
                        "mode": "agent"
                    }))
            
            Thread(target=process_query, daemon=True).start()
            
            while True:
                token = queue.get()
                if token == "[END]":
                    sources_json = queue.get()
                    yield f"data: {sources_json}\n\n"
                    break
                
                # 处理换行符和特殊字符
                if token == "\n":
                    yield "data: \n\n"
                else:
                    if '\n' in token:
                        parts = token.split('\n')
                        for i, part in enumerate(parts):
                            if i > 0:
                                yield "data: \n\n"
                            if part:
                                safe_part = part.replace('\r', '\\r')
                                yield f"data: {safe_part}\n\n"
                    else:
                        safe_token = token.replace('\r', '\\r')
                        yield f"data: {safe_token}\n\n"
        
        return generate
    
    def create_teacher_agent_stream_generator(self, query, teacher_id, qa_mode, references, session_id=None, is_new_session=False, history=None):
        """创建教师端Agent流式生成器"""
        queue = Queue()
        answer_content = ""
        sources = []
        
        def generate():
            nonlocal answer_content, sources
            
            callback = CustomStreamingCallback(queue)
            callback.answer_content = answer_content
            
            app = current_app._get_current_object()
            
            def process_teacher_query():
                nonlocal answer_content, sources
                try:
                    from services.teacher_agent_service import teacher_agent_service
                    
                    # 状态通知
                    notifier = StatusNotifier(queue)
                    notifier.notify_analysis_start()
                    
                    print(f"🎓 教师端流式处理开始: teacher_id={teacher_id}, qa_mode={qa_mode}")
                    
                    # 在流式服务内部创建Agent，传递正确的回调（与学生端保持一致）
                    current_agent_executor, error = teacher_agent_service.create_teacher_agent(
                        teacher_id=teacher_id,
                        qa_mode=qa_mode,
                        references=references,
                        streaming_callback=callback  # 关键：在创建时就传递回调
                    )
                    
                    if error:
                        raise Exception(error)
                    
                    print(f"[FLOW] 教师端Agent创建成功，设置了流式回调")
                    
                    notifier.notify_generation_start()
                    
                    # 使用教师端Agent执行查询，传递历史记录（与学生端保持一致）
                    result = teacher_agent_service.query_teacher_agent(
                        current_agent_executor, query, history=history or []
                    )
                    
                    # 确保回调内容被获取
                    if callback.answer_content:
                        answer_content = callback.answer_content
                    else:
                        answer_content = result.get("result", "")
                        # 如果没有流式输出，直接发送完整结果
                        queue.put(answer_content)
                    
                    # 处理源文档（如果有）
                    if result.get("source_documents"):
                        sources = source_service.process_source_documents(
                            result["source_documents"], app
                        )
                    
                    # 处理教师端特定的元数据
                    teacher_metadata = result.get("teacher_metadata", {})
                    
                    queue.put("[END]")
                    
                    # 保存教师端AI回复
                    with app.app_context():
                        if session_id and chat_service.save_message_to_db(session_id, 'assistant', answer_content):
                            current_app.logger.info(f"教师端回复已保存，teacher_id={teacher_id}")
                    
                    queue.put(json.dumps({
                        "sources": sources,
                        "session": {"sessionId": str(session_id)} if session_id else {},
                        "stats": {"tokens": callback.token_count},
                        "mode": "teacher_agent",
                        "teacher_metadata": teacher_metadata
                    }))
                    
                except Exception as e:
                    with app.app_context():
                        current_app.logger.error(f"教师端Agent处理失败: {str(e)}")
                        print(traceback.format_exc())
                    
                    # 保存错误回复
                    if answer_content.strip():
                        error_content = answer_content + f"\n\n[教师端处理过程中出现错误: {str(e)}]"
                        with app.app_context():
                            if session_id:
                                chat_service.save_message_to_db(session_id, 'assistant', error_content)
                    
                    queue.put(f"教师端处理请求失败: {str(e)}")
                    queue.put("[END]")
                    queue.put(json.dumps({
                        "sources": [],
                        "session": {"sessionId": str(session_id)} if session_id else {},
                        "error": str(e),
                        "mode": "teacher_agent"
                    }))
            
            Thread(target=process_teacher_query, daemon=True).start()
            
            while True:
                token = queue.get()
                if token == "[END]":
                    sources_json = queue.get()
                    yield f"data: {sources_json}\n\n"
                    break
                
                # 处理换行符和特殊字符
                if token == "\n":
                    yield "data: \n\n"
                else:
                    if '\n' in token:
                        parts = token.split('\n')
                        for i, part in enumerate(parts):
                            if i > 0:
                                yield "data: \n\n"
                            if part:
                                safe_part = part.replace('\r', '\\r')
                                yield f"data: {safe_part}\n\n"
                    else:
                        safe_token = token.replace('\r', '\\r')
                        yield f"data: {safe_token}\n\n"
        
        return generate


# 全局流式服务实例
streaming_service = StreamingService()
