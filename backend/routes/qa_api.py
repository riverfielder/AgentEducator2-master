"""重构后的QA API路由模块 - 只处理HTTP请求和响应"""
import time
import traceback
from flask import Blueprint, request, jsonify, current_app, Response, stream_with_context
from utils.auth import token_required
from utils.result import Result
from models.models import Course, Document, DocumentSummary, db
from services.chat_service import chat_service

from services.course_access_service import course_access_service
from services.streaming_service import streaming_service
from services.cache_service import get_video_info
from services.qa_chain_service import qa_chain_service
from config.agent_config import AgentConfig

qa_bp = Blueprint('qa', __name__)


@qa_bp.route('/ask-stream', methods=['POST'])
@token_required
def ask_question_stream():
    """处理流式问答请求（重构版）"""
    try:
        start_time = time.time()
        
        # 解析请求参数
        request_data = _parse_request_data()
        if isinstance(request_data, tuple):  # 错误响应
            return request_data[0]
        
        # 所有请求都使用Agent模式
        result = _handle_agent_mode(request_data, start_time)
        
        # 检查返回值类型
        if isinstance(result, tuple) and len(result) == 2:
            first_element, second_element = result
            
            # 检查第一个元素的类型来判断是否是错误响应
            # UUID对象有hex属性，jsonify响应有status_code属性
            if hasattr(first_element, 'status_code'):
                # 这是一个Flask响应对象（错误情况）
                return first_element
            elif hasattr(first_element, 'hex'):
                # 这是一个UUID对象（正常情况）
                session_id, error = first_element, second_element
            else:
                # 其他情况，按错误处理
                return jsonify(Result.error(500, "处理请求时发生未知错误"))
            
            if error:
                return jsonify(Result.error(500, error))
        else:
            return jsonify(Result.error(500, "处理请求时发生未知错误"))
        
        # 获取存储的contexts
        stored_contexts = get_contexts_for_session(session_id)
        video_contexts = stored_contexts.get('video_contexts', [])
        course_contexts = stored_contexts.get('course_contexts', [])
        document_contexts = stored_contexts.get('document_contexts', [])
        
        #获取用户的user_id
        user_id = request.user.get('user_id')
        # 使用Agent模式流式生成器
        generate = streaming_service.create_agent_stream_generator(
            request_data['query'],
            session_id,
            request_data['history'],
            video_contexts=video_contexts,
            course_contexts=course_contexts,
            document_contexts=document_contexts,
            user_id=user_id
        )
        
        # 返回流式响应
        resp = Response(
            stream_with_context(generate()),
            content_type='text/event-stream'
        )
        resp.headers['X-Session-Id'] = str(session_id)
        resp.headers['Cache-Control'] = 'no-cache'
        resp.headers['Connection'] = 'keep-alive'
        
        total_time = time.time() - start_time
        current_app.logger.info(f"请求处理完成，总耗时: {total_time:.2f}s")
        
        return resp
        
    except Exception as e:
        current_app.logger.error(f"处理请求失败: {str(e)}")
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify(Result.error(500, f"处理请求失败: {str(e)}"))


def _parse_request_data():
    """解析请求数据 - 简化版，只支持ID数组"""
    data = request.get_json()
    if not data:
        return jsonify(Result.error(400, "缺少请求数据")), None
        
    query = data.get('query')
    if not query:
        return jsonify(Result.error(400, "问题不能为空")), None
    
    # 只接收ID数组
    video_ids = _parse_id_input(data.get('videoIds', []))
    course_ids = _parse_id_input(data.get('courseIds', []))
    document_ids = _parse_id_input(data.get('documentIds', []))
    
    session_id = data.get('sessionId')    
    is_new_session = data.get('isNewSession', False)
    history = data.get('history', [])
    user_id = request.user.get('user_id')
    
    return {
        'query': query,
        'video_ids': video_ids,
        'course_ids': course_ids,
        'document_ids': document_ids,
        'session_id': session_id,
        'is_new_session': is_new_session,
        'history': history,
        'user_id': user_id
    }


def _parse_id_input(input_data):
    """解析ID输入，支持数组和逗号分隔的字符串
    
    Args:
        input_data: 可能是数组、字符串、或None
        
    Returns:
        list: 解析后的ID列表
    """
    if not input_data:
        return []
    
    if isinstance(input_data, list):
        # 如果是数组，直接返回（过滤空值）
        return [str(id_val).strip() for id_val in input_data if id_val and str(id_val).strip()]
    
    if isinstance(input_data, str):
        # 如果是字符串，按逗号分割
        return [id_val.strip() for id_val in input_data.split(',') if id_val.strip()]
    
    # 其他类型，尝试转换为字符串处理
    return [str(input_data).strip()] if str(input_data).strip() else []





def _handle_agent_mode(request_data, start_time):
    """处理Agent模式 - 简化版，只处理ID数组"""
    video_ids = request_data.get('video_ids', [])
    course_ids = request_data.get('course_ids', [])
    document_ids = request_data.get('document_ids', [])
    
    # 获取所有资源的context
    video_contexts, course_contexts, document_contexts = _get_resources_context(
        video_ids, course_ids, document_ids
    )
    
    # 创建会话标题
    title = _create_session_title(video_contexts, course_contexts, document_contexts, request_data['query'])
    
    # 创建会话
    session_id = chat_service.create_or_get_session(
        request_data['session_id'],
        request_data['user_id'],
        title,
        is_new_session=request_data['is_new_session']
    )
    
    # 保存用户问题
    chat_service.save_message_to_db(session_id, 'user', request_data['query'])
    
    # 将contexts存储到session_id中，供streaming_service使用
    _store_contexts_for_session(session_id, video_contexts, course_contexts, document_contexts)
    
    return session_id, None





def _store_contexts_for_session(session_id, video_contexts, course_contexts, document_contexts):
    """为session存储contexts，供后续使用"""
    # 这里可以使用Redis、内存缓存或其他方式存储
    # 为了简单起见，我们使用一个简单的内存字典
    if not hasattr(_store_contexts_for_session, 'contexts_cache'):
        _store_contexts_for_session.contexts_cache = {}
    
    _store_contexts_for_session.contexts_cache[str(session_id)] = {
        'video_contexts': video_contexts,
        'course_contexts': course_contexts,
        'document_contexts': document_contexts
    }


def get_contexts_for_session(session_id):
    """获取session的contexts"""
    if hasattr(_store_contexts_for_session, 'contexts_cache'):
        return _store_contexts_for_session.contexts_cache.get(str(session_id), {})
    return {}


def _get_resources_context(video_ids, course_ids, document_ids):
    """获取多个资源的文本context
    
    Args:
        video_ids: 视频ID列表
        course_ids: 课程ID列表
        document_ids: 文档ID列表
        
    Returns:
        tuple: (video_contexts, course_contexts, document_contexts)
    """
    video_contexts = []
    course_contexts = []
    document_contexts = []
    
    # 获取视频contexts
    for video_id in video_ids:
        try:
            video_context = _get_single_video_context(video_id)
            if video_context:
                video_contexts.append(video_context)
        except Exception as e:
            print(f"获取视频 {video_id} context失败: {e}")
    
    # 获取课程contexts
    for course_id in course_ids:
        try:
            course_context = _get_single_course_context(course_id)
            if course_context:
                course_contexts.append(course_context)
        except Exception as e:
            print(f"获取课程 {course_id} context失败: {e}")
    
    # 获取文档contexts
    for document_id in document_ids:
        try:
            document_context = _get_single_document_context(document_id)
            if document_context:
                document_contexts.append(document_context)
        except Exception as e:
            print(f"获取文档 {document_id} context失败: {e}")
    
    return video_contexts, course_contexts, document_contexts


def _get_single_video_context(video_id):
    """获取单个视频的context，包含课程和章节信息"""
    from services.cache_service import get_video_info, get_video_keywords, get_video_summary
    from models.models import Video, Course, CourseChapter
    
    video_title, course_id = get_video_info(video_id)
    if not video_title:
        return None
    
    video_keywords = get_video_keywords(video_id, limit=10)
    video_summary = get_video_summary(video_id)
    
    # 获取课程和章节信息
    video = Video.query.filter_by(id=video_id, is_deleted=False).first()
    course_name = ''
    chapter_title = ''
    
    if video:
        if video.course:
            course_name = video.course.name
        if video.chapter:
            chapter_title = video.chapter.title
    
    keywords_str = ','.join([kw['name'] for kw in video_keywords]) if video_keywords else ''
    
    context_parts = [
        f"VIDEO_ID:{video_id}",
        f"TITLE:{video_title}",
        f"SUMMARY:{video_summary or ''}",
        f"KEYWORDS:{keywords_str}",
        f"COURSE_ID:{course_id or ''}",
        f"COURSE_NAME:{course_name}",
        f"CHAPTER_TITLE:{chapter_title}"
    ]
    
    return '|'.join(context_parts)


def _get_single_course_context(course_id):
    """获取单个课程的context，包含课程基本信息和关键词"""
    from services.cache_service import get_course_info, get_course_keywords
    from models.models import Course
    
    course_name = get_course_info(course_id)
    if not course_name:
        return None
    
    # 获取课程详细信息
    course = Course.query.filter_by(id=course_id, is_deleted=False).first()
    course_description = course.description if course and course.description else ''
    course_code = course.code if course and course.code else ''
    
    course_keywords = get_course_keywords(course_id, limit=15)
    
    # 按类别分组关键词
    categorized_keywords = {}
    if course_keywords:
        for kw in course_keywords:
            category = kw.get('category', 'other')
            if category not in categorized_keywords:
                categorized_keywords[category] = []
            categorized_keywords[category].append(kw['name'])
    
    # 构建关键词字符串
    keywords_parts = []
    for category, keywords in categorized_keywords.items():
        keywords_str = ','.join(keywords)
        keywords_parts.append(f"{category}:{keywords_str}")
    
    keywords_full = '|'.join(keywords_parts)
    
    # 构建context字符串
    context_parts = [
        f"COURSE_ID:{course_id}",
        f"NAME:{course_name}",
        f"CODE:{course_code}",
        f"DESCRIPTION:{course_description}",
        f"KEYWORDS:{keywords_full}"
    ]
    
    return '|'.join(context_parts)


def _get_single_document_context(document_id):
    """获取单个文档的context，包含摘要、主要要点、课程和章节信息，返回字符串"""
    try:
        from models.models import Document, DocumentSummary, Course, CourseChapter
        # 获取文档基本信息
        document = Document.query.filter_by(id=document_id, is_deleted=False).first()
        if not document:
            return None
        
        # 获取文档摘要
        summary = DocumentSummary.query.filter_by(document_id=document_id).first()
        summary_text = summary.whole_summary if summary and hasattr(summary, 'whole_summary') else ''
        main_points = summary.main_points if summary and hasattr(summary, 'main_points') else ''
        
        # 获取课程和章节信息
        course_name = ''
        chapter_title = ''
        
        if document.course:
            course_name = document.course.name
        if document.chapter:
            chapter_title = document.chapter.title
        
        # 拼接摘要和要点
        summary_full = summary_text + (main_points if main_points else '')
        
        # 构建context字符串
        context_parts = [
            f"DOCUMENT_ID:{document.id}",
            f"TITLE:{document.title}",
            #f"DESCRIPTION:{document.description or ''}",
            #f"SUMMARY:{summary_full}",
            #f"MAIN_POINTS:{main_points}",
            f"COURSE_ID:{document.course_id}",
            f"COURSE_NAME:{course_name}",
            f"CHAPTER_TITLE:{chapter_title}"
        ]
        
        return '|'.join(context_parts)
    except Exception as e:
        print(f"获取文档context失败: {e}")
        return None


def _create_session_title(video_contexts, course_contexts, document_contexts, query):
    """根据资源contexts创建会话标题"""
    resource_parts = []
    
    if video_contexts:
        video_titles = []
        for context in video_contexts[:2]:  # 最多显示2个视频标题
            parts = context.split('|')
            for part in parts:
                if part.startswith('TITLE:'):
                    video_titles.append(part[6:])  # 去掉 'TITLE:' 前缀
                    break
        if video_titles:
            resource_parts.append(f"视频:{','.join(video_titles)}")
    
    if course_contexts:
        course_names = []
        for context in course_contexts[:2]:  # 最多显示2个课程名称
            parts = context.split('|')
            for part in parts:
                if part.startswith('NAME:'):
                    course_names.append(part[5:])  # 去掉 'NAME:' 前缀
                    break
        if course_names:
            resource_parts.append(f"课程:{','.join(course_names)}")
    
    if document_contexts:
        document_titles = []
        for context in document_contexts[:2]:  # 最多显示2个文档标题
            print(f"处理文档context: {context}")
            parts = context.split('|')
            for part in parts:
                if part.startswith('TITLE:'):
                    document_titles.append(part[6:])  # 去掉 'TITLE:' 前缀
                    break
        if document_titles:
            resource_parts.append(f"文档:{','.join(document_titles)}")
    
    if resource_parts:
        resource_str = ' | '.join(resource_parts)
        return f"关于 {resource_str} - {query[:20]}{'...' if len(query) > 20 else ''}"
    else:
        return f"智能对话 - {query[:20]}{'...' if len(query) > 20 else ''}"
