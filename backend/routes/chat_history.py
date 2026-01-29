import os
from flask import Blueprint, request, jsonify, g
from models.models import db, ChatSession, ChatMessage
from utils.auth import token_required
from utils.result import Result
import uuid

# 创建蓝图
chat_history_bp = Blueprint('chat_history', __name__)

@chat_history_bp.route('/list', methods=['GET'])
@token_required
def list_chat_sessions():
    """获取用户的聊天会话列表"""
    try:
        # 获取分页参数
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
        video_id = request.args.get('videoId')
        course_id = request.args.get('courseId')
        include_all = request.args.get('includeAll', 'false').lower() == 'true'  # 新增参数，AI助手界面会传入此参数
        
        # 构建查询条件
        query = ChatSession.query.filter_by(user_id=request.user.get('user_id'), is_deleted=False)
        
        # 根据参数过滤不同类型的对话
        if video_id:
            # 如果传递了video_id，只返回该视频相关的对话
            try:
                video_uuid = uuid.UUID(video_id)
                query = query.filter_by(video_id=video_uuid)
            except ValueError:
                return jsonify(Result.error(400, "视频ID格式不正确"))
                
        elif course_id:
            # 如果传递了course_id，只返回该课程相关的对话
            try:
                course_uuid = uuid.UUID(course_id)
                query = query.filter_by(course_id=course_uuid)
            except ValueError:
                return jsonify(Result.error(400, "课程ID格式不正确"))
                
        elif not include_all:
            # 如果没有传递video_id和course_id，且不是includeAll模式，说明是普通界面调用
            # 只返回通用模式的对话（video_id和course_id都为null）
            query = query.filter_by(video_id=None, course_id=None)
            
        # 如果include_all为true，则不添加额外过滤条件，返回所有类型的对话
            
        # 按最后更新时间降序排序
        query = query.order_by(ChatSession.updated_at.desc())
        
        # 获取总数
        total = query.count()
        
        # 分页
        sessions = query.offset((page - 1) * size).limit(size).all()
        
        # 格式化结果，添加类型信息和相关数据
        result_list = []
        for session in sessions:
            session_dict = session.to_dict()
            
            # 判断对话类型并添加相关信息
            if session.video_id and session.course_id:
                session_dict['type'] = 'video'
                session_dict['video_info'] = {
                    'id': str(session.video.id),
                    'title': session.video.title,
                    'cover_url': session.video.cover_url
                } if session.video else None
                session_dict['course_info'] = {
                    'id': str(session.course.id),
                    'name': session.course.name,
                    'code': session.course.code
                } if session.course else None
            elif session.course_id and not session.video_id:
                session_dict['type'] = 'course'
                session_dict['course_info'] = {
                    'id': str(session.course.id),
                    'name': session.course.name,
                    'code': session.course.code
                } if session.course else None
            else:
                session_dict['type'] = 'general'
                
            result_list.append(session_dict)
        
        return jsonify(Result.success({
            'list': result_list,
            'total': total,
            'page': page,
            'size': size
        }, '获取聊天历史列表成功'))
        
    except Exception as e:
        return jsonify(Result.error(500, f'获取聊天历史列表失败: {str(e)}'))

@chat_history_bp.route('/detail/<session_id>', methods=['GET'])
@token_required
def get_chat_session_detail(session_id):
    """获取指定聊天会话的详细消息记录"""
    try:
        # 获取会话信息，确保只能查看自己的会话
        session = ChatSession.query.filter_by(id=session_id, user_id=request.user.get('user_id'), is_deleted=False).first()
        if not session:
            return jsonify(Result.error(404, '聊天会话不存在或无权访问'))
            
        # 获取所有消息，按时间顺序排序
        messages = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.created_at).all()
        
        # 格式化结果
        message_list = [message.to_dict() for message in messages]
        session_info = session.to_dict()
        
        # 如果会话有视频，添加视频信息
        if session.video:
            session_info['video_info'] = {
                'id': session.video.id,
                'title': session.video.title,
                'cover_url': os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{session.video.cover_url}" or session.video.cover_url,
            }
            
        # 如果会话有课程，添加课程信息
        if session.course:
            session_info['course_info'] = {
                'id': session.course.id,
                'name': session.course.name,
                'code': session.course.code
            }
            
        return jsonify(Result.success({
            'session': session_info,
            'messages': message_list
        }, '获取聊天历史详情成功'))
        
    except Exception as e:
        return jsonify(Result.error(500, f'获取聊天历史详情失败: {str(e)}'))

@chat_history_bp.route('/create', methods=['POST'])
@token_required
def create_chat_session():
    """创建新的聊天会话"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(Result.error(400, '缺少请求数据'))
            
        # 获取必要参数
        title = data.get('title', '新建会话')
        video_id = data.get('videoId')
        course_id = data.get('courseId')
        user_id = request.user.get('user_id')
        
        # 转换ID格式
        try:
            video_uuid = uuid.UUID(video_id) if video_id else None
            course_uuid = uuid.UUID(course_id) if course_id else None
        except ValueError:
            return jsonify(Result.error(400, "ID格式不正确"))
        
        # 创建新会话
        session = ChatSession(
            user_id=user_id,
            video_id=video_uuid,
            course_id=course_uuid,
            title=title
        )
        
        db.session.add(session)
        db.session.commit()
        
        return jsonify(Result.success(session.to_dict(), '创建聊天会话成功'))
        
    except Exception as e:
        db.session.rollback()
        return jsonify(Result.error(500, f'创建聊天会话失败: {str(e)}'))

@chat_history_bp.route('/update/<session_id>', methods=['PUT'])
@token_required
def update_chat_session(session_id):
    """更新聊天会话信息（如标题、资源IDs）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(Result.error(400, '缺少请求数据'))
        user_id = request.user.get('user_id')
        # 获取会话，确保只能修改自己的会话
        session = ChatSession.query.filter_by(id=session_id, user_id=user_id, is_deleted=False).first()
        if not session:
            return jsonify(Result.error(404, '聊天会话不存在或无权访问'))
            
        # 更新标题
        if 'title' in data:
            session.title = data['title']
        
        # 更新资源IDs
        if 'video_ids' in data:
            session.set_video_ids(data['video_ids'])
        if 'course_ids' in data:
            session.set_course_ids(data['course_ids'])
        if 'document_ids' in data:
            session.set_document_ids(data['document_ids'])
        
        # 从sources中添加资源IDs
        if 'sources' in data:
            session.add_resource_ids_from_sources(data['sources'])
            
        db.session.commit()
        
        return jsonify(Result.success(session.to_dict(), '更新聊天会话成功'))
        
    except Exception as e:
        db.session.rollback()
        return jsonify(Result.error(500, f'更新聊天会话失败: {str(e)}'))

@chat_history_bp.route('/delete/<session_id>', methods=['DELETE'])
@token_required
def delete_chat_session(session_id):
    """删除聊天会话（软删除会话和相关消息）"""
    try:
        # 获取会话，确保只能删除自己的会话
        session = ChatSession.query.filter_by(id=session_id, user_id=request.user.get('user_id'), is_deleted=False).first()
        if not session:
            return jsonify(Result.error(404, '聊天会话不存在或无权访问'))
        
        # 删除该会话下的所有消息（物理删除）
        ChatMessage.query.filter_by(session_id=session_id).delete()
        
        # 软删除会话
        session.is_deleted = True
        
        db.session.commit()
        
        return jsonify(Result.success(None, '删除聊天会话成功'))
        
    except Exception as e:
        db.session.rollback()
        return jsonify(Result.error(500, f'删除聊天会话失败: {str(e)}'))