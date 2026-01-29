# -*- coding: utf-8 -*-
"""
全局搜索API路由
提供跨视频、文档、课程的全局搜索功能
支持知识点搜索和全文搜索
"""

from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import or_, and_, func, desc
from models.models import (
    db, Video, Document, Course, Keyword, VideoKeyword, DocumentKeyword,
    CourseKeyword, VideoSummary, DocumentSummary, VideoKeyframe
)
from utils.auth import token_required
from utils.result import Result
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
global_search_bp = Blueprint('global_search', __name__)


@global_search_bp.route('/api/global-search', methods=['GET'])
@token_required
def global_search():
    """
    全局搜索API
    
    支持搜索范围：
    - videos: 视频
    - documents: 文档
    - courses: 课程
    - keywords: 知识点
    
    支持搜索类型：
    - keyword_search: 知识点搜索（默认）
    - fulltext_search: 全文搜索
    
    Query参数：
    - q: 搜索关键词（必填）
    - scope: 搜索范围，逗号分隔，如 "videos,documents,courses,keywords"（可选，默认全部）
    - search_type: 搜索类型 "keyword_search" 或 "fulltext_search"（可选，默认keyword_search）
    - course_id: 限制在特定课程内搜索（可选）
    - page: 页码（可选，默认1）
    - page_size: 每页大小（可选，默认20）
    - limit: 每个类型的最大结果数（可选，默认10）
    """
    try:
        # 获取查询参数
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify(Result.error(400, "搜索关键词不能为空"))
        results = {}
        total_count = 0        
        scope = request.args.get('scope', 'videos,documents,courses,keywords')
        search_type = request.args.get('search_type', 'keyword_search')
        course_id = request.args.get('course_id')
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        # 解析搜索范围
        search_scopes = [s.strip() for s in scope.split(',')]
        
        # 验证搜索类型
        if search_type not in ['keyword_search', 'fulltext_search']:
            return jsonify(Result.error(400, "搜索类型必须是 keyword_search 或 fulltext_search"))
        
        # 验证课程ID格式
        if course_id:
            try:
                course_uuid = uuid.UUID(course_id)
            except ValueError:
                return jsonify(Result.error(400, "课程ID格式不正确"))
        
        # 初始化结果变量
        results = {}
        total_count = 0
        
        # 搜索课程
        if 'courses' in search_scopes:
            course_results, course_count = search_courses(
                query, search_type, limit
            )
            results['courses'] = course_results
            total_count += course_count
        
        # 搜索视频
        if 'videos' in search_scopes:
            video_results, video_count = search_videos(
                query, search_type, course_id, limit
            )
            results['videos'] = video_results
            total_count += video_count
        
        # 搜索文档
        if 'documents' in search_scopes:
            document_results, document_count = search_documents(
                query, search_type, course_id, limit
            )
            results['documents'] = document_results
            total_count += document_count
        

        
        # 搜索知识点
        if 'keywords' in search_scopes:
            keyword_results, keyword_count = search_keywords(
                query, course_id, limit
            )
            results['keywords'] = keyword_results
            total_count += keyword_count
        
        return jsonify(Result.success({
            'results': results,
            'total_count': total_count,
            'query': query,
            'search_type': search_type,
            'scope': search_scopes,
            'course_id': course_id
        }, "搜索完成"))
        
    except Exception as e:
        logger.error(f"全局搜索失败: {str(e)}")
        return jsonify(Result.error(500, f"搜索失败: {str(e)}"))


def search_videos(query, search_type, course_id=None, limit=10):
    """
    搜索视频
    
    Args:
        query: 搜索关键词
        search_type: 搜索类型
        course_id: 课程ID限制
        limit: 结果数量限制
    
    Returns:
        tuple: (视频结果列表, 总数量)
    """
    try:
        base_query = Video.query.filter_by(is_deleted=False)
        
        # 课程限制
        if course_id:
            base_query = base_query.filter_by(course_id=uuid.UUID(course_id))
        
        if search_type == 'keyword_search':
            # 知识点搜索：通过VideoKeyword关联搜索
            video_ids_subquery = db.session.query(VideoKeyword.video_id).join(
                Keyword, VideoKeyword.keyword_id == Keyword.id
            ).filter(
                Keyword.name.contains(query)
            ).subquery()
            
            videos_query = base_query.filter(
                or_(
                    Video.title.contains(query),
                    Video.description.contains(query),
                    Video.id.in_(video_ids_subquery)
                )
            )
        else:
            # 全文搜索：搜索标题、描述、摘要、ASR文本
            videos_query = base_query.outerjoin(VideoSummary).outerjoin(VideoKeyframe).filter(
                or_(
                    Video.title.contains(query),
                    Video.description.contains(query),
                    VideoSummary.main_points.contains(query),
                    VideoKeyframe.asr_text.contains(query)
                )
            )
        
        # 获取总数
        total_count = videos_query.count()
        
        # 获取结果
        videos = videos_query.join(Course).order_by(
            desc(Video.upload_time)
        ).limit(limit).all()
        
        results = []
        for video in videos:
            # 获取相关知识点
            keywords = db.session.query(Keyword.name).join(
                VideoKeyword, Keyword.id == VideoKeyword.keyword_id
            ).filter(VideoKeyword.video_id == video.id).limit(5).all()
            
            results.append({
                'id': str(video.id),
                'title': video.title,
                'description': video.description,
                'cover_url': video.cover_url,
                'duration': video.duration,
                'upload_time': video.upload_time.isoformat() if video.upload_time else None,
                'course_id': str(video.course_id),
                'course_name': video.course.name,
                'keywords': [k[0] for k in keywords],
                'type': 'video'
            })
        
        return results, total_count
        
    except Exception as e:
        logger.error(f"搜索视频失败: {str(e)}")
        return [], 0


def search_documents(query, search_type, course_id=None, limit=10):
    """
    搜索文档
    
    Args:
        query: 搜索关键词
        search_type: 搜索类型
        course_id: 课程ID限制
        limit: 结果数量限制
    
    Returns:
        tuple: (文档结果列表, 总数量)
    """
    try:
        base_query = Document.query.filter_by(is_deleted=False)
        
        # 课程限制
        if course_id:
            base_query = base_query.filter_by(course_id=uuid.UUID(course_id))
        
        if search_type == 'keyword_search':
            # 知识点搜索：通过DocumentKeyword关联搜索
            document_ids_subquery = db.session.query(DocumentKeyword.document_id).join(
                Keyword, DocumentKeyword.keyword_id == Keyword.id
            ).filter(
                Keyword.name.contains(query)
            ).subquery()
            
            documents_query = base_query.filter(
                or_(
                    Document.title.contains(query),
                    Document.id.in_(document_ids_subquery)
                )
            )
        else:
            # 全文搜索：搜索标题和摘要内容
            documents_query = base_query.outerjoin(DocumentSummary).filter(
                or_(
                    Document.title.contains(query),
                    DocumentSummary.whole_summary.contains(query),
                    DocumentSummary.main_points.contains(query)
                )
            )
        
        # 获取总数
        total_count = documents_query.count()
        
        # 获取结果
        documents = documents_query.join(Course).order_by(
            desc(Document.upload_time)
        ).limit(limit).all()
        
        results = []
        for document in documents:
            # 获取相关知识点
            keywords = db.session.query(Keyword.name).join(
                DocumentKeyword, Keyword.id == DocumentKeyword.keyword_id
            ).filter(DocumentKeyword.document_id == document.id).limit(5).all()
            
            results.append({
                'id': str(document.id),
                'title': document.title,
                'file_type': document.file_type,
                'file_size': document.file_size,
                'upload_time': document.upload_time.isoformat() if document.upload_time else None,
                'course_id': str(document.course_id),
                'course_name': document.course.name,
                'keywords': [k[0] for k in keywords],
                'type': 'document'
            })
        
        return results, total_count
        
    except Exception as e:
        logger.error(f"搜索文档失败: {str(e)}")
        return [], 0


def search_courses(query, search_type, limit=10):
    """
    搜索课程
    
    Args:
        query: 搜索关键词
        search_type: 搜索类型
        limit: 结果数量限制
    
    Returns:
        tuple: (课程结果列表, 总数量)
    """
    try:
        if search_type == 'keyword_search':
            # 知识点搜索：通过CourseKeyword关联搜索
            course_ids_subquery = db.session.query(CourseKeyword.course_id).join(
                Keyword, CourseKeyword.keyword_id == Keyword.id
            ).filter(
                Keyword.name.contains(query)
            ).subquery()
            
            courses_query = Course.query.filter_by(is_deleted=False).filter(
                or_(
                    Course.name.contains(query),
                    Course.description.contains(query),
                    Course.id.in_(course_ids_subquery)
                )
            )
        else:
            # 全文搜索：搜索课程名称和描述
            courses_query = Course.query.filter_by(is_deleted=False).filter(
                or_(
                    Course.name.contains(query),
                    Course.description.contains(query)
                )
            )
        
        # 获取总数
        total_count = courses_query.count()
        
        # 获取结果
        courses = courses_query.order_by(
            desc(Course.create_time)
        ).limit(limit).all()
        
        results = []
        for course in courses:
            # 获取相关知识点
            keywords = db.session.query(Keyword.name).join(
                CourseKeyword, Keyword.id == CourseKeyword.keyword_id
            ).filter(CourseKeyword.course_id == course.id).limit(5).all()
            
            # 统计课程资源
            video_count = Video.query.filter_by(
                course_id=course.id, is_deleted=False
            ).count()
            document_count = Document.query.filter_by(
                course_id=course.id, is_deleted=False
            ).count()
            
            # 处理时间戳转换为ISO格式
            start_date_iso = None
            if course.start_date:
                try:
                    start_date_iso = datetime.fromtimestamp(course.start_date).isoformat()
                except (ValueError, TypeError):
                    start_date_iso = None
            
            end_date_iso = None
            if course.end_date:
                try:
                    end_date_iso = datetime.fromtimestamp(course.end_date).isoformat()
                except (ValueError, TypeError):
                    end_date_iso = None
            
            results.append({
                'id': str(course.id),
                'name': course.name,
                'code': course.code,
                'description': course.description,
                'image_url': course.image_url,
                'start_date': start_date_iso,
                'end_date': end_date_iso,
                'teacher_name': course.teacher.username if course.teacher else None,
                'student_count': course.student_count,
                'video_count': video_count,
                'document_count': document_count,
                'keywords': [k[0] for k in keywords],
                'type': 'course'
            })
        
        return results, total_count
        
    except Exception as e:
        logger.error(f"搜索课程失败: {str(e)}")
        return [], 0


def search_keywords(query, course_id=None, limit=10):
    """
    搜索知识点
    
    Args:
        query: 搜索关键词
        course_id: 课程ID限制
        limit: 结果数量限制
    
    Returns:
        tuple: (知识点结果列表, 总数量)
    """
    try:
        base_query = Keyword.query
        
        # 课程限制
        if course_id:
            course_keyword_ids = db.session.query(CourseKeyword.keyword_id).filter_by(
                course_id=uuid.UUID(course_id)
            ).subquery()
            base_query = base_query.filter(Keyword.id.in_(course_keyword_ids))
        
        # 搜索知识点名称和描述
        keywords_query = base_query.filter(
            or_(
                Keyword.name.contains(query),
                Keyword.description.contains(query)
            )
        )
        
        # 获取总数
        total_count = keywords_query.count()
        
        # 获取结果
        keywords = keywords_query.order_by(
            Keyword.name
        ).limit(limit).all()
        
        results = []
        for keyword in keywords:
            # 统计相关资源
            video_count = VideoKeyword.query.filter_by(keyword_id=keyword.id).count()
            document_count = DocumentKeyword.query.filter_by(keyword_id=keyword.id).count()
            course_count = CourseKeyword.query.filter_by(keyword_id=keyword.id).count()
            
            results.append({
                'id': str(keyword.id),
                'name': keyword.name,
                'category': keyword.category,
                'description': keyword.description,
                'video_count': video_count,
                'document_count': document_count,
                'course_count': course_count,
                'type': 'keyword'
            })
        
        return results, total_count
        
    except Exception as e:
        logger.error(f"搜索知识点失败: {str(e)}")
        return [], 0

