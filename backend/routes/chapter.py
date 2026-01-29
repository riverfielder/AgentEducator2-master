from flask import Blueprint, request, jsonify
from models.models import db, CourseChapter, Course, Video, Document
from utils.auth import token_required, is_teacher_or_admin
from utils.result import Result
import uuid
from datetime import datetime
from sqlalchemy import func

chapter_bp = Blueprint('chapter', __name__)

@chapter_bp.route('/<course_id>', methods=['GET'])
@token_required
def get_course_chapters(course_id):
    """获取课程的所有章节"""
    try:
        # 验证课程是否存在
        course = Course.query.get(course_id)
        if not course or course.is_deleted:
            return jsonify(Result.error(404, "课程不存在"))
        
        # 获取章节列表，按照order_index排序
        chapters = CourseChapter.query.filter_by(
            course_id=course_id, 
            is_deleted=False
        ).order_by(CourseChapter.order_index.asc()).all()
        
        chapter_list = []
        for chapter in chapters:
            chapter_list.append(chapter.to_dict())
        
        return jsonify(Result.success({
            'list': chapter_list,
            'total': len(chapter_list)
        }, "获取章节列表成功"))
        
    except Exception as e:
        print(f"获取章节列表错误: {e}")
        return jsonify(Result.error(500, "获取章节列表失败"))

@chapter_bp.route('', methods=['POST'])
@token_required
def create_chapter():
    """创建新章节"""
    try:
        # 检查权限：只有教师和管理员可以创建章节
        if not is_teacher_or_admin(request.user.get('user_id')):
            return jsonify(Result.error(403, "权限不足，只有教师和管理员可以创建章节"))
        
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['courseId', 'title', 'chapterNumber']
        for field in required_fields:
            if field not in data:
                return jsonify(Result.error(400, f"缺少必填字段：{field}"))
        
        # 验证课程是否存在
        course = Course.query.get(data['courseId'])
        if not course or course.is_deleted:
            return jsonify(Result.error(404, "课程不存在"))
        
        # 检查章节编号是否重复
        existing_chapter = CourseChapter.query.filter_by(
            course_id=data['courseId'],
            chapter_number=data['chapterNumber'],
            is_deleted=False
        ).first()
        
        if existing_chapter:
            return jsonify(Result.error(400, "章节编号已存在"))
        
        # 自动设置order_index
        max_order = db.session.query(func.max(CourseChapter.order_index)).filter_by(
            course_id=data['courseId'], 
            is_deleted=False
        ).scalar() or 0
        
        # 创建新章节
        new_chapter = CourseChapter(
            id=str(uuid.uuid4()),
            course_id=data['courseId'],
            title=data['title'],
            description=data.get('description', ''),
            chapter_number=data['chapterNumber'],
            order_index=max_order + 1,
            create_time=datetime.now(),
            update_time=datetime.now(),
            is_deleted=False
        )
        
        db.session.add(new_chapter)
        db.session.commit()
        
        return jsonify(Result.success(new_chapter.to_dict(), "章节创建成功"))
        
    except Exception as e:
        db.session.rollback()
        print(f"创建章节错误: {e}")
        return jsonify(Result.error(500, "创建章节失败"))

@chapter_bp.route('/<chapter_id>', methods=['PUT'])
@token_required
def update_chapter(chapter_id):
    """更新章节信息"""
    try:
        # 检查权限
        if not is_teacher_or_admin(request.user.get('user_id')):
            return jsonify(Result.error(403, "权限不足"))
        
        data = request.get_json()
        
        # 查找章节
        chapter = CourseChapter.query.get(chapter_id)
        if not chapter or chapter.is_deleted:
            return jsonify(Result.error(404, "章节不存在"))
        
        # 如果要更新章节编号，检查是否重复
        if 'chapterNumber' in data and data['chapterNumber'] != chapter.chapter_number:
            existing_chapter = CourseChapter.query.filter_by(
                course_id=chapter.course_id,
                chapter_number=data['chapterNumber'],
                is_deleted=False
            ).filter(CourseChapter.id != chapter_id).first()
            
            if existing_chapter:
                return jsonify(Result.error(400, "章节编号已存在"))
        
        # 更新字段
        if 'title' in data:
            chapter.title = data['title']
        if 'description' in data:
            chapter.description = data['description']
        if 'chapterNumber' in data:
            chapter.chapter_number = data['chapterNumber']
        
        chapter.update_time = datetime.now()
        
        db.session.commit()
        
        return jsonify(Result.success(chapter.to_dict(), "章节更新成功"))
        
    except Exception as e:
        db.session.rollback()
        print(f"更新章节错误: {e}")
        return jsonify(Result.error(500, "更新章节失败"))

@chapter_bp.route('/<chapter_id>', methods=['DELETE'])
@token_required
def delete_chapter(chapter_id):
    """删除章节（软删除）"""
    try:
        # 检查权限
        if not is_teacher_or_admin(request.user.get('user_id')):
            return jsonify(Result.error(403, "权限不足"))
        
        # 查找章节
        chapter = CourseChapter.query.get(chapter_id)
        if not chapter or chapter.is_deleted:
            return jsonify(Result.error(404, "章节不存在"))
        
        # 软删除章节
        chapter.is_deleted = True
        chapter.update_time = datetime.now()
        
        # 将该章节下的视频和文档的chapter_id设为NULL
        Video.query.filter_by(chapter_id=chapter_id).update({'chapter_id': None})
        Document.query.filter_by(chapter_id=chapter_id).update({'chapter_id': None})
        
        db.session.commit()
        
        return jsonify(Result.success(None, "章节删除成功"))
        
    except Exception as e:
        db.session.rollback()
        print(f"删除章节错误: {e}")
        return jsonify(Result.error(500, "删除章节失败"))

@chapter_bp.route('/assign-resource', methods=['POST'])
@token_required
def assign_resource_to_chapter():
    """将资源分配到章节"""
    try:
        # 检查权限
        if not is_teacher_or_admin(request.user.get('user_id')):
            return jsonify(Result.error(403, "权限不足"))
        
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['resourceId', 'resourceType']
        for field in required_fields:
            if field not in data:
                return jsonify(Result.error(400, f"缺少必填字段：{field}"))
        
        resource_id = data['resourceId']
        resource_type = data['resourceType']  # 'video' 或 'document'
        chapter_id = data.get('chapterId')  # 可以为None，表示取消分配
        
        # 根据资源类型更新相应的表
        if resource_type == 'video':
            # 更新视频的chapter_id
            video = Video.query.get(resource_id)
            if not video or video.is_deleted:
                return jsonify(Result.error(404, "视频不存在"))
            
            video.chapter_id = chapter_id
            db.session.commit()
            
        elif resource_type == 'document':
            # 更新文档的chapter_id
            document = Document.query.get(resource_id)
            if not document or document.is_deleted:
                return jsonify(Result.error(404, "文档不存在"))
            
            document.chapter_id = chapter_id
            db.session.commit()
            
        else:
            return jsonify(Result.error(400, "不支持的资源类型"))
        
        return jsonify(Result.success(None, "资源分配成功"))
        
    except Exception as e:
        db.session.rollback()
        print(f"分配资源错误: {e}")
        return jsonify(Result.error(500, "分配资源失败"))

@chapter_bp.route('/<chapter_id>/resources', methods=['GET'])
@token_required
def get_chapter_resources(chapter_id):
    """获取章节下的所有资源"""
    try:
        # 验证章节是否存在
        chapter = CourseChapter.query.get(chapter_id)
        if not chapter or chapter.is_deleted:
            return jsonify(Result.error(404, "章节不存在"))
        
        # 获取该章节下的视频
        videos = Video.query.filter_by(
            chapter_id=chapter_id, 
            is_deleted=False
        ).order_by(Video.upload_time.desc()).all()
        
        # 获取该章节下的文档
        documents = Document.query.filter_by(
            chapter_id=chapter_id, 
            is_deleted=False
        ).order_by(Document.upload_time.desc()).all()
        
        # 构建资源列表
        resources = []
        
        for video in videos:
            resources.append({
                'id': video.id,
                'type': 'video',
                'title': video.title,
                'description': video.description,
                'uploadTime': video.upload_time.isoformat() if video.upload_time else None,
                'duration': video.duration,
                'coverUrl': video.cover_url
            })
        
        for document in documents:
            resources.append({
                'id': document.id,
                'type': 'document',
                'title': document.title,
                'description': document.description,
                'uploadTime': document.upload_time.isoformat() if document.upload_time else None,
                'fileSize': document.file_size,
                'fileType': document.file_type
            })
        
        return jsonify(Result.success({
            'chapter': chapter.to_dict(),
            'resources': resources,
            'total': len(resources)
        }, "获取章节资源成功"))
        
    except Exception as e:
        print(f"获取章节资源错误: {e}")
        return jsonify(Result.error(500, "获取章节资源失败"))