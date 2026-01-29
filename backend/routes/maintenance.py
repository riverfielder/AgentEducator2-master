"""
系统维护API接口
提供数据清理和维护功能
"""

from flask import Blueprint, request, jsonify, current_app
from utils.auth import token_required
from utils.result import Result
from models.models import Users
from services.deletion_service import DeletionService

maintenance_bp = Blueprint('maintenance', __name__)

@maintenance_bp.route('/clean-orphaned-data', methods=['POST'])
@token_required
def clean_orphaned_data():
    """
    清理所有孤立数据（仅管理员可用）
    """
    try:
        # 检查管理员权限
        user_id = request.user.get('user_id')
        user = Users.query.get(user_id)
        
        if not user or user.role != 'admin':
            return jsonify(Result.error(403, "需要管理员权限"))
        
        # 执行清理
        deletion_service = DeletionService()
        result = deletion_service.clean_all_orphaned_data()
        
        return jsonify(Result.success(result, "孤立数据清理完成"))
        
    except Exception as e:
        current_app.logger.error(f"清理孤立数据失败: {str(e)}")
        return jsonify(Result.error(500, f"清理失败: {str(e)}"))

@maintenance_bp.route('/force-delete-video/<uuid:video_id>', methods=['DELETE'])
@token_required
def force_delete_video(video_id):
    """
    强制删除视频（仅管理员可用）
    无视权限检查，强制级联删除
    """
    try:
        # 检查管理员权限
        user_id = request.user.get('user_id')
        user = Users.query.get(user_id)
        
        if not user or user.role != 'admin':
            return jsonify(Result.error(403, "需要管理员权限"))
        
        # 获取删除选项
        hard_delete = request.args.get('hard_delete', 'true').lower() == 'true'
        
        # 执行强制删除
        deletion_service = DeletionService()
        result = deletion_service.delete_video_cascade(str(video_id), hard_delete)
        
        return jsonify(Result.success(result, "视频强制删除完成"))
        
    except Exception as e:
        current_app.logger.error(f"强制删除视频失败: {str(e)}")
        return jsonify(Result.error(500, f"删除失败: {str(e)}"))

@maintenance_bp.route('/force-delete-course/<uuid:course_id>', methods=['DELETE'])
@token_required
def force_delete_course(course_id):
    """
    强制删除课程（仅管理员可用）
    无视权限检查，强制级联删除
    """
    try:
        # 检查管理员权限
        user_id = request.user.get('user_id')
        user = Users.query.get(user_id)
        
        if not user or user.role != 'admin':
            return jsonify(Result.error(403, "需要管理员权限"))
        
        # 获取删除选项
        hard_delete = request.args.get('hard_delete', 'true').lower() == 'true'
        
        # 执行强制删除
        deletion_service = DeletionService()
        result = deletion_service.delete_course_cascade(str(course_id), hard_delete)
        
        return jsonify(Result.success(result, "课程强制删除完成"))
        
    except Exception as e:
        current_app.logger.error(f"强制删除课程失败: {str(e)}")
        return jsonify(Result.error(500, f"删除失败: {str(e)}"))

@maintenance_bp.route('/deletion-preview/<uuid:video_id>', methods=['GET'])
@token_required
def preview_video_deletion(video_id):
    """
    预览视频删除将影响的数据（不实际删除）
    """
    try:
        # 检查管理员权限
        user_id = request.user.get('user_id')
        user = Users.query.get(user_id)
        
        if not user or user.role != 'admin':
            return jsonify(Result.error(403, "需要管理员权限"))
        
        # 使用删除服务预览影响
        deletion_service = DeletionService()
        preview_data = deletion_service.preview_video_deletion(str(video_id))
        
        return jsonify(Result.success(preview_data, "预览数据获取成功"))
        
    except Exception as e:
        current_app.logger.error(f"预览视频删除失败: {str(e)}")
        return jsonify(Result.error(500, f"预览失败: {str(e)}"))

@maintenance_bp.route('/admin/videos', methods=['GET'])
@token_required
def get_all_videos_for_admin():
    """
    获取所有视频列表（仅管理员可用）
    """
    try:
        # 检查管理员权限
        user_id = request.user.get('user_id')
        user = Users.query.get(user_id)
        
        if not user or user.role != 'admin':
            return jsonify(Result.error(403, "需要管理员权限"))
        
        from models.models import Video, Course
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 50, type=int)  # 管理员默认显示更多
        search = request.args.get('search', '', type=str)
        
        # 构建查询 - 管理员可以看到所有视频
        query = Video.query.filter_by(is_deleted=False)
        
        # 如果有搜索条件
        if search:
            query = query.filter(Video.title.like(f'%{search}%'))
        
        # 关联课程和教师信息
        query = query.join(Course, Video.course_id == Course.id)\
                    .join(Users, Course.teacher_id == Users.user_id)
        
        # 计算总数
        total = query.count()
        
        # 分页查询
        videos = query.order_by(Video.upload_time.desc())\
                     .offset((page - 1) * size)\
                     .limit(size)\
                     .all()
        
        # 构建返回数据
        video_list = []
        for video in videos:
            course = Course.query.get(video.course_id)
            teacher = Users.query.get(course.teacher_id) if course else None
            
            video_list.append({
                "id": video.id,
                "title": video.title,
                "description": video.description,
                "thumbnail_url": video.cover_url,
                "duration": video.duration,
                "course_id": video.course_id,
                "course_name": course.name if course else "未知课程",
                "teacher_name": teacher.username if teacher else "未知教师",
                "upload_time": video.upload_time,
                "status": video.status
            })
        
        return jsonify(Result.success({
            "data": video_list,
            "total": total,
            "page": page,
            "size": size
        }, "获取视频列表成功"))
        
    except Exception as e:
        current_app.logger.error(f"获取视频列表失败: {str(e)}")
        return jsonify(Result.error(500, f"获取失败: {str(e)}"))

@maintenance_bp.route('/admin/courses', methods=['GET'])
@token_required 
def get_all_courses_for_admin():
    """
    获取所有课程列表（仅管理员可用）
    """
    try:
        # 检查管理员权限
        user_id = request.user.get('user_id')
        user = Users.query.get(user_id)
        
        if not user or user.role != 'admin':
            return jsonify(Result.error(403, "需要管理员权限"))
        
        from models.models import Course
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 50, type=int)  # 管理员默认显示更多
        search = request.args.get('search', '', type=str)
        
        # 构建查询 - 管理员可以看到所有课程
        query = Course.query.filter_by(is_deleted=False)
        
        # 如果有搜索条件
        if search:
            query = query.filter(Course.name.like(f'%{search}%'))
        
        # 关联教师信息
        query = query.join(Users, Course.teacher_id == Users.user_id)
        
        # 计算总数
        total = query.count()
        
        # 分页查询
        courses = query.order_by(Course.create_time.desc())\
                      .offset((page - 1) * size)\
                      .limit(size)\
                      .all()
        
        # 构建返回数据
        course_list = []
        for course in courses:
            teacher = Users.query.get(course.teacher_id)
            
            # 统计课程下的视频数量
            video_count = Video.query.filter_by(course_id=course.id, is_deleted=False).count()
            
            course_list.append({
                "id": course.id,
                "name": course.name,
                "description": course.description,
                "image_url": course.image_url,
                "teacher_id": course.teacher_id,
                "teacher_name": teacher.username if teacher else "未知教师",
                "video_count": video_count,
                "status": course.status,
                "create_time": course.create_time,
                "is_public": course.is_public
            })
        
        return jsonify(Result.success({
            "data": course_list,
            "total": total,
            "page": page,
            "size": size
        }, "获取课程列表成功"))
        
    except Exception as e:
        current_app.logger.error(f"获取课程列表失败: {str(e)}")
        return jsonify(Result.error(500, f"获取失败: {str(e)}"))

@maintenance_bp.route('/system-stats', methods=['GET'])
@token_required
def get_system_stats():
    """
    获取系统统计信息（仅管理员可用）
    """
    try:
        # 检查管理员权限
        user_id = request.user.get('user_id')
        user = Users.query.get(user_id)
        
        if not user or user.role != 'admin':
            return jsonify(Result.error(403, "需要管理员权限"))
        
        # 这里应该实现真实的统计逻辑
        # 目前返回模拟数据
        stats = {
            "orphaned_data_count": 0,
            "total_storage_mb": 0,
            "video_storage_mb": 0,
            "index_storage_mb": 0,
            "document_storage_mb": 0,
            "other_storage_mb": 0,
            "total_videos": Video.query.filter_by(is_deleted=False).count(),
            "total_courses": Course.query.filter_by(is_deleted=False).count(),
            "total_users": Users.query.count()
        }
        
        return jsonify(Result.success(stats, "获取系统统计成功"))
        
    except Exception as e:
        current_app.logger.error(f"获取系统统计失败: {str(e)}")
        return jsonify(Result.error(500, f"获取失败: {str(e)}"))
