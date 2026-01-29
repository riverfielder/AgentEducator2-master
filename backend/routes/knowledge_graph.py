"""
知识图谱相关API路由
"""

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
import uuid
from datetime import datetime

from utils.auth import token_required
from models.models import (
    Video, db, Course, Keyword, VideoKeyword, CourseKeyword, DocumentKeyword,KeywordRelation, KnowledgeGraphProcessingTask,Document
)
from services.knowledge_graph_service import get_query_service
import logging

logger = logging.getLogger(__name__)

knowledge_graph_bp = Blueprint('knowledge_graph', __name__)



@knowledge_graph_bp.route('/api/knowledge-graph/generate', methods=['POST'])
@token_required
def generate_knowledge_graph():
    """触发知识图谱生成"""
    try:
        data = request.get_json()
        course_id = data.get('courseId')
        force_regenerate = data.get('forceRegenerate', False)
        #force_regenerate = True
        incremental = data.get('incremental', True)  # 默认启用增量处理
        
        if not course_id:
            return jsonify({
                'code': 400,
                'msg': '课程ID不能为空',
                'data': None
            }), 400
        
        # 验证课程是否存在
        course = Course.query.get(course_id)
        if not course:
            return jsonify({
                'code': 404,
                'msg': '课程不存在',
                'data': None
            }), 404
          # 检查是否有正在进行的任务
        existing_task = KnowledgeGraphProcessingTask.query.filter_by(
            course_id=course_id,
            status='processing'
        ).first()
        
        if existing_task and not force_regenerate:
            return jsonify({
                'code': 409,
                'msg': '该课程的知识图谱正在生成中',
                'data': existing_task.to_dict()
            }), 409
        elif force_regenerate:
            # 如果有正在进行的任务且force_regenerate为True，更新任务状态
            #删除对应课程的知识点和关系数据
            # 获取该课程下的所有视频ID列表
            video_ids = [row[0] for row in db.session.query(Video.id).filter(Video.course_id == course_id).all()]
            
            # 获取该课程下的所有视频知识点ID
            video_keyword_ids = [row[0] for row in db.session.query(VideoKeyword.keyword_id).filter(VideoKeyword.video_id.in_(video_ids)).all()]
            
            # 获取该课程下的所有文档知识点ID
            document_keyword_ids = [row[0] for row in db.session.query(DocumentKeyword.keyword_id).join(Document).filter(Document.course_id == course_id).all()]
            
            # 合并所有知识点ID
            all_keyword_ids = list(set(video_keyword_ids + document_keyword_ids))
            
            # 删除知识点关系
            if all_keyword_ids:
                db.session.query(KeywordRelation).filter(
                    (KeywordRelation.source_keyword_id.in_(all_keyword_ids)) | 
                    (KeywordRelation.target_keyword_id.in_(all_keyword_ids))
                ).delete(synchronize_session=False)
                
                # 将涉及的知识点等级重置为specific_point
                db.session.query(Keyword).filter(
                    Keyword.id.in_(all_keyword_ids)
                ).update(
                    {Keyword.category: 'specific_point'},
                    synchronize_session=False
                )

            db.session.commit()
        
        # 异步触发知识图谱生成
        from utils.knowledge_graph_processing_pool import knowledge_graph_processing_pool
        from tasks.knowledge_graph_processor import process_knowledge_graph_task
          # 创建知识图谱处理任务
        task_id = f"kg-task-{uuid.uuid4().hex[:8]}"
        task_type = 'full_knowledge_graph' if force_regenerate or not incremental else 'incremental_knowledge_graph'
        task = KnowledgeGraphProcessingTask(
            course_id=course_id,
            task_type=task_type,
            status="pending",
            start_time=datetime.now()
        )
        db.session.add(task)
        db.session.commit()
          # 提交任务到线程池处理，不阻塞HTTP响应
        print((
            current_app._get_current_object(), 
            course_id, 
            process_knowledge_graph_task,
            force_regenerate,
            incremental
        ))
        pool_task_id, stop_flag = knowledge_graph_processing_pool.submit_task(
            current_app._get_current_object(), 
            course_id, 
            process_knowledge_graph_task,
            force_regenerate,
            incremental
        )
        
        # 更新任务ID（如果线程池生成了新的ID）
        if task.id != pool_task_id:
            # 这里使用数据库自动生成的UUID作为task_id
            pass
        
        return jsonify({
            'code': 200,
            'msg': '知识图谱生成任务已启动',
            'data': {
                "taskId": str(task.id),
                "pendingTasks": knowledge_graph_processing_pool.get_pending_tasks_count(),
                "activeTasks": knowledge_graph_processing_pool.get_active_tasks_count()
            }
        })
            
    except Exception as e:
        
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/course/<course_id>', methods=['GET'])
@token_required
def get_course_knowledge_graph(course_id):
    """获取课程知识图谱"""
    try:
        # 验证课程是否存在
        course = Course.query.get(course_id)
        if not course:
            return jsonify({
                'code': 404,
                'msg': '课程不存在',
                'data': None
            }), 404
        
        # 获取课程知识点
        course_keywords = db.session.query(
            Keyword, CourseKeyword
        ).join(CourseKeyword).filter(
            CourseKeyword.course_id == course_id
        ).all()
        
        # 构建节点数据
        nodes = []
        node_categories = []
        category_map = {}
        
        # 添加分类到map
        categories = ['core_concept', 'main_module', 'specific_point']
        category_names = ['一级知识点', '二级知识点', '三级知识点']
        
        for i, (cat, name) in enumerate(zip(categories, category_names)):
            category_map[cat] = i
            node_categories.append({'name': name})
        
        # 构建节点
        keyword_id_map = {}
        for keyword, course_keyword in course_keywords:
            # 根据视频数量和权重计算节点大小
            symbol_size = max(30, min(80, 30 + course_keyword.video_count * 5 + course_keyword.avg_weight * 20))
            
            node = {
                'id': str(keyword.id),
                'name': keyword.name,
                'category': category_map.get(keyword.category, 2),
                'symbolSize': symbol_size,
                'video_count': course_keyword.video_count,
                'avg_weight': round(course_keyword.avg_weight, 2),
                'description': keyword.description or f"{keyword.name}相关知识点"
            }
            nodes.append(node)
            keyword_id_map[keyword.id] = keyword.name
        
        # 获取知识点关系
        keyword_ids = list(keyword_id_map.keys())
        relations = KeywordRelation.query.filter(
            KeywordRelation.source_keyword_id.in_(keyword_ids),
            KeywordRelation.target_keyword_id.in_(keyword_ids)
        ).all()
        
        # 构建边数据
        links = []
        for relation in relations:
            link = {
                'source': str(relation.source_keyword_id),
                'target': str(relation.target_keyword_id),
                'relation_type': relation.relation_type,
                'strength': relation.strength,
                'description': relation.description,
                'lineStyle': {
                    'width': max(1, relation.strength * 3),  # 根据强度设置线宽
                    'opacity': max(0.3, relation.strength)   # 根据强度设置透明度
                }
            }
            links.append(link)
        
        # 构建返回数据
        graph_data = {
            'nodes': nodes,
            'links': links,
            'categories': node_categories,
            'course_info': {
                'id': str(course.id),
                'name': course.name,
                'description': course.description
            },
            'statistics': {
                'total_keywords': len(nodes),
                'total_relations': len(links),
                'core_concepts': len([n for n in nodes if n['category'] == 0]),
                'main_modules': len([n for n in nodes if n['category'] == 1]),
                'specific_points': len([n for n in nodes if n['category'] == 2])
            }
        }
        
        return jsonify({
            'code': 200,
            'msg': '获取知识图谱成功',
            'data': graph_data
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500


@knowledge_graph_bp.route('/api/knowledge-graph/search-keywords', methods=['GET'])
@token_required
def search_keywords_simple():
    """搜索关键词（简单版）"""
    try:
        keyword = request.args.get('keyword', '').strip()
        if not keyword:
            return jsonify({
                'code': 400,
                'msg': '关键词不能为空',
                'data': []
            }), 400
        keywords = Keyword.query.filter(
            Keyword.name.like(f'%{keyword}%')
        ).limit(10).all()
        result = []
        for kw in keywords:
            result.append({
                'id': kw.id,
                'name': kw.name,
                'description': kw.description,
                'category': kw.category
            })
        return jsonify({
            'code': 200,
            'msg': '搜索成功',
            'data': result
        })
    except Exception as e:
        logger.error(f'搜索关键词失败: {str(e)}')
        return jsonify({
            'code': 500,
            'msg': f'搜索失败: {str(e)}',
            'data': []
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/platform', methods=['GET'])
@token_required
def get_platform_knowledge_graph():
    """获取平台级知识图谱"""
    try:
        # 批量查询所有需要的数据
        # 1. 获取所有知识点
        all_keywords = Keyword.query.all()
        keyword_ids = [kw.id for kw in all_keywords]
        
        # 2. 批量查询课程知识点统计
        course_stats = db.session.query(
            CourseKeyword.keyword_id,
            db.func.count(CourseKeyword.course_id).label('course_count')
        ).filter(
            CourseKeyword.keyword_id.in_(keyword_ids)
        ).group_by(CourseKeyword.keyword_id).all()
        
        # 3. 批量查询视频知识点统计
        video_stats = db.session.query(
            VideoKeyword.keyword_id,
            db.func.count(VideoKeyword.video_id).label('video_count')
        ).filter(
            VideoKeyword.keyword_id.in_(keyword_ids)
        ).group_by(VideoKeyword.keyword_id).all()
        
        # 4. 批量查询所有知识点关系
        all_relations = KeywordRelation.query.filter(
            KeywordRelation.source_keyword_id.in_(keyword_ids),
            KeywordRelation.target_keyword_id.in_(keyword_ids)
        ).all()
        
        # 构建统计字典
        course_count_map = {stat.keyword_id: stat.course_count for stat in course_stats}
        video_count_map = {stat.keyword_id: stat.video_count for stat in video_stats}
        
        # 构建节点数据
        nodes = []
        node_categories = []
        category_map = {}
        
        # 添加分类
        categories = ['core_concept', 'main_module', 'specific_point']
        category_names = ['一级知识点', '二级知识点', '三级知识点']
        
        for i, (cat, name) in enumerate(zip(categories, category_names)):
            category_map[cat] = i
            node_categories.append({'name': name})
        
        # 构建节点
        keyword_id_map = {}
        for keyword in all_keywords:
            course_count = course_count_map.get(keyword.id, 0)
            video_count = video_count_map.get(keyword.id, 0)
            
            # 根据课程数量和视频数量计算节点大小
            symbol_size = max(25, min(100, 25 + course_count * 10 + video_count * 2))
            
            node = {
                'id': str(keyword.id),
                'name': keyword.name,
                'category': category_map.get(keyword.category, 2),
                'symbolSize': symbol_size,
                'course_count': course_count,
                'video_count': video_count,
                'description': keyword.description or f"{keyword.name}相关知识点"
            }
            nodes.append(node)
            keyword_id_map[keyword.id] = keyword.name
        
        # 构建边数据
        links = []
        for relation in all_relations:
            link = {
                'source': str(relation.source_keyword_id),
                'target': str(relation.target_keyword_id),
                'relation_type': relation.relation_type,
                'strength': relation.strength,
                'description': relation.description,
                'lineStyle': {
                    'width': max(1, relation.strength * 3),
                    'opacity': max(0.3, relation.strength)
                }
            }
            links.append(link)
        
        # 构建返回数据
        graph_data = {
            'nodes': nodes,
            'links': links,
            'categories': node_categories,
            'statistics': {
                'total_keywords': len(nodes),
                'total_relations': len(links),
                'core_concepts': len([n for n in nodes if n['category'] == 0]),
                'main_modules': len([n for n in nodes if n['category'] == 1]),
                'specific_points': len([n for n in nodes if n['category'] == 2])
            }
        }
        
        return jsonify({
            'code': 200,
            'msg': '获取平台知识图谱成功',
            'data': graph_data
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/keyword/<keyword_id>/videos', methods=['GET'])
@token_required
def get_keyword_related_videos(keyword_id):
    """获取知识点相关的视频"""
    try:
        # 验证知识点是否存在
        keyword = Keyword.query.get(keyword_id)
        if not keyword:
            return jsonify({
                'code': 404,
                'msg': '知识点不存在',
                'data': None
            }), 404
        
        # 获取知识点相关的视频
        try:
            video_keywords = db.session.query(
                VideoKeyword, Video, Course
            ).join(
                Video, VideoKeyword.video_id == Video.id
            ).join(
                Course, Video.course_id == Course.id
            ).filter(
                VideoKeyword.keyword_id == keyword_id,
                Video.is_deleted == False
            ).order_by(VideoKeyword.weight.desc()).all()
            
        except Exception as e:
            print(f"查询视频时出错: {str(e)}")  # 添加日志
            raise
        
        videos = []
        for vk, video, course in video_keywords:
            video_data = {
                'id': str(video.id),
                'title': video.title,
                'description': video.description,
                'cover_url': video.cover_url,
                'duration': video.duration,
                'upload_time': video.upload_time.strftime('%Y-%m-%d %H:%M:%S'),
                'view_count': video.view_count,
                'weight': round(vk.weight, 2),
                'course': {
                    'id': str(course.id),
                    'name': course.name
                }
            }
            videos.append(video_data)
        
        return jsonify({
            'code': 200,
            'msg': '获取知识点相关视频成功',
            'data': {
                'keyword': keyword.to_dict(),
                'videos': videos,
                'total': len(videos)
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/keyword/<keyword_id>/documents', methods=['GET'])
@token_required
def get_keyword_related_documents(keyword_id):
    """获取知识点相关的文档"""
    try:
        # 验证知识点是否存在
        keyword = Keyword.query.get(keyword_id)
        if not keyword:
            return jsonify({
                'code': 404,
                'msg': '知识点不存在',
                'data': None
            }), 404
        
        # 获取知识点相关的文档
        try:
            document_keywords = db.session.query(
                DocumentKeyword, Document, Course
            ).join(
                Document, DocumentKeyword.document_id == Document.id
            ).join(
                Course, Document.course_id == Course.id
            ).filter(
                DocumentKeyword.keyword_id == keyword_id,
                Document.is_deleted == False
            ).order_by(DocumentKeyword.weight.desc()).all()
            
        except Exception as e:
            print(f"查询文档时出错: {str(e)}")  # 添加日志
            raise
        
        documents = []
        for dk, document, course in document_keywords:
            document_data = {
                'id': str(document.id),
                'title': document.title,
                'description': document.description,
                'file_type': document.file_type,
                'file_size': document.file_size,
                'upload_time': document.upload_time.strftime('%Y-%m-%d %H:%M:%S'),
                'weight': round(dk.weight, 2),
                'course': {
                    'id': str(course.id),
                    'name': course.name
                }
            }
            documents.append(document_data)
        
        return jsonify({
            'code': 200,
            'msg': '获取知识点相关文档成功',
            'data': {
                'keyword': keyword.to_dict(),
                'documents': documents,
                'total': len(documents)
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/keyword/<keyword_id>/resources', methods=['GET'])
@token_required
def get_keyword_related_resources(keyword_id):
    """获取知识点相关的所有资源（视频+文档）"""
    try:
        # 验证知识点是否存在
        keyword = Keyword.query.get(keyword_id)
        if not keyword:
            return jsonify({
                'code': 404,
                'msg': '知识点不存在',
                'data': None
            }), 404
        
        # 获取相关视频
        video_keywords = db.session.query(
            VideoKeyword, Video, Course
        ).join(
            Video, VideoKeyword.video_id == Video.id
        ).join(
            Course, Video.course_id == Course.id
        ).filter(
            VideoKeyword.keyword_id == keyword_id,
            Video.is_deleted == False
        ).order_by(VideoKeyword.weight.desc()).all()
        
        videos = []
        for vk, video, course in video_keywords:
            video_data = {
                'id': str(video.id),
                'title': video.title,
                'description': video.description,
                'cover_url': video.cover_url,
                'duration': video.duration,
                'upload_time': video.upload_time.strftime('%Y-%m-%d %H:%M:%S'),
                'view_count': video.view_count,
                'weight': round(vk.weight, 2),
                'type': 'video',
                'course': {
                    'id': str(course.id),
                    'name': course.name
                }
            }
            videos.append(video_data)
        
        # 获取相关文档
        document_keywords = db.session.query(
            DocumentKeyword, Document, Course
        ).join(
            Document, DocumentKeyword.document_id == Document.id
        ).join(
            Course, Document.course_id == Course.id
        ).filter(
            DocumentKeyword.keyword_id == keyword_id,
            Document.is_deleted == False
        ).order_by(DocumentKeyword.weight.desc()).all()
        
        documents = []
        for dk, document, course in document_keywords:
            document_data = {
                'id': str(document.id),
                'title': document.title,
                'description': document.description,
                'file_type': document.file_type,
                'file_size': document.file_size,
                'upload_time': document.upload_time.strftime('%Y-%m-%d %H:%M:%S'),
                'weight': round(dk.weight, 2),
                'type': 'document',
                'course': {
                    'id': str(course.id),
                    'name': course.name
                }
            }
            documents.append(document_data)
        
        # 合并并按权重排序
        all_resources = videos + documents
        all_resources.sort(key=lambda x: x['weight'], reverse=True)
        
        return jsonify({
            'code': 200,
            'msg': '获取知识点相关资源成功',
            'data': {
                'keyword': keyword.to_dict(),
                'resources': all_resources,
                'videos': videos,
                'documents': documents,
                'total': len(all_resources),
                'video_count': len(videos),
                'document_count': len(documents)
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/task/<task_id>', methods=['GET'])
@token_required
def get_task_status(task_id):
    """获取知识图谱生成任务状态"""
    try:
        task = KnowledgeGraphProcessingTask.query.get(task_id)
        if not task:
            return jsonify({
                'code': 404,
                'msg': '任务不存在',
                'data': None
            }), 404
        
        return jsonify({
            'code': 200,
            'msg': '获取任务状态成功',
            'data': task.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500


@knowledge_graph_bp.route('/api/knowledge-graph/course/<course_id>/task', methods=['GET'])
@token_required
def get_course_task_status(course_id):
    """获取课程最新的知识图谱任务状态"""
    try:
        # 获取该课程最新的任务
        task = KnowledgeGraphProcessingTask.query.filter_by(
            course_id=course_id
        ).order_by(KnowledgeGraphProcessingTask.create_time.desc()).first()
        
        if not task:
            return jsonify({
                'code': 404,
                'msg': '未找到相关任务',
                'data': None
            }), 404
        
        return jsonify({
            'code': 200,
            'msg': '获取任务状态成功',
            'data': task.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500


@knowledge_graph_bp.route('/api/knowledge-graph/pool-status', methods=['GET'])
@token_required
def get_pool_status():
    """获取知识图谱处理线程池的状态"""
    try:
        from utils.knowledge_graph_processing_pool import knowledge_graph_processing_pool
        
        status = {
            'active_tasks': knowledge_graph_processing_pool.get_active_tasks_count(),
            'pending_tasks': knowledge_graph_processing_pool.get_pending_tasks_count(),
            'max_workers': knowledge_graph_processing_pool.max_workers,
            'is_full': knowledge_graph_processing_pool.get_active_tasks_count() >= knowledge_graph_processing_pool.max_workers
        }
        
        # 获取正在处理的任务信息
        active_tasks = []
        for task_id, task_info in knowledge_graph_processing_pool.current_tasks.items():
            # 查找任务记录
            task = KnowledgeGraphProcessingTask.query.filter_by(course_id=task_info['course_id']).order_by(
                KnowledgeGraphProcessingTask.create_time.desc()
            ).first()
            if task:
                # 获取课程信息
                course = Course.query.get(task.course_id)
                active_tasks.append({
                    'task_id': task_id,
                    'course_id': str(task.course_id),
                    'course_title': course.name if course else "未知课程",
                    'start_time': task_info['start_time'].isoformat(),
                    'progress': task.progress if task else 0
                })
        
        status['active_tasks_detail'] = active_tasks
        
        return jsonify({
            'code': 200,
            'msg': '获取线程池状态成功',
            'data': status
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/video/<video_id>/keywords', methods=['GET'])
@token_required
def get_video_keywords(video_id):
    """获取视频的所有知识点"""
    try:
        # 验证视频是否存在
        video = Video.query.get(video_id)
        if not video:
            return jsonify({
                'code': 404,
                'msg': '视频不存在',
                'data': None
            }), 404
        
        # 获取视频知识点
        video_keywords = db.session.query(
            Keyword, VideoKeyword
        ).join(VideoKeyword).filter(
            VideoKeyword.video_id == video_id
        ).order_by(VideoKeyword.weight.desc()).all()
        
        # 构建返回数据
        keywords_data = []
        for keyword, video_keyword in video_keywords:
            keywords_data.append({
                'id': str(keyword.id),
                'name': keyword.name,
                'category': keyword.category,
                'description': keyword.description,
                'weight': video_keyword.weight,
                'create_time': video_keyword.create_time.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'code': 200,
            'msg': '获取视频知识点成功',
            'data': {
                'video_info': {
                    'id': str(video.id),
                    'title': video.title,
                    'description': video.description
                },
                'keywords': keywords_data,
                'total_count': len(keywords_data)
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/course/<course_id>/keywords', methods=['GET'])
@token_required
def get_course_keywords_detailed(course_id):
    """获取课程的所有知识点（带统计信息）"""
    try:
        # 验证课程是否存在
        course = Course.query.get(course_id)
        if not course:
            return jsonify({
                'code': 404,
                'msg': '课程不存在',
                'data': None
            }), 404
        
        # 获取请求参数
        category = request.args.get('category')  # 可选：过滤特定分类
        limit = request.args.get('limit', type=int)  # 可选：限制返回数量
        
        # 构建查询
        query = db.session.query(
            Keyword, CourseKeyword
        ).join(CourseKeyword).filter(
            CourseKeyword.course_id == course_id
        )
        
        if category:
            query = query.filter(Keyword.category == category)
        
        # 按视频数量和平均权重排序
        query = query.order_by(
            CourseKeyword.video_count.desc(),
            CourseKeyword.avg_weight.desc()
        )
        
        if limit:
            query = query.limit(limit)
        
        course_keywords = query.all()
        
        # 构建返回数据
        keywords_data = []
        for keyword, course_keyword in course_keywords:
            keywords_data.append({
                'id': str(keyword.id),
                'name': keyword.name,
                'category': keyword.category,
                'description': keyword.description,
                'video_count': course_keyword.video_count,
                'avg_weight': round(course_keyword.avg_weight, 3),
                'importance_score': round(course_keyword.video_count * course_keyword.avg_weight, 3),
                'create_time': course_keyword.create_time.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # 统计信息
        category_stats = db.session.query(
            Keyword.category,
            db.func.count(Keyword.id).label('count')
        ).join(CourseKeyword).filter(
            CourseKeyword.course_id == course_id
        ).group_by(Keyword.category).all()
        
        return jsonify({
            'code': 200,
            'msg': '获取课程知识点成功',
            'data': {
                'course_info': {
                    'id': str(course.id),
                    'name': course.name,
                    'description': course.description
                },
                'keywords': keywords_data,
                'total_count': len(keywords_data),
                'category_stats': {cat: count for cat, count in category_stats}
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/keyword/<keyword_id>/usage', methods=['GET'])
@token_required
def get_keyword_usage(keyword_id):
    """获取知识点的使用情况（在哪些视频和课程中出现）"""
    try:
        # 验证知识点是否存在
        keyword = Keyword.query.get(keyword_id)
        if not keyword:
            return jsonify({
                'code': 404,
                'msg': '知识点不存在',
                'data': None
            }), 404
        
        # 获取知识点在视频中的使用情况
        video_usage = db.session.query(
            VideoKeyword, Video, Course
        ).join(Video).join(Course).filter(
            VideoKeyword.keyword_id == keyword_id,
            Video.is_deleted == False
        ).order_by(VideoKeyword.weight.desc()).all()
        
        videos_data = []
        course_map = {}
        
        for vk, video, course in video_usage:
            video_data = {
                'id': str(video.id),
                'title': video.title,
                'duration': video.duration,
                'weight': vk.weight,
                'course_id': str(course.id),
                'course_name': course.name
            }
            videos_data.append(video_data)
            
            # 统计课程信息
            if str(course.id) not in course_map:
                course_map[str(course.id)] = {
                    'id': str(course.id),
                    'name': course.name,
                    'video_count': 0,
                    'total_weight': 0
                }
            course_map[str(course.id)]['video_count'] += 1
            course_map[str(course.id)]['total_weight'] += vk.weight
        
        # 计算课程平均权重
        courses_data = []
        for course_info in course_map.values():
            course_info['avg_weight'] = round(
                course_info['total_weight'] / course_info['video_count'], 3
            ) if course_info['video_count'] > 0 else 0
            del course_info['total_weight']  # 移除临时字段
            courses_data.append(course_info)
        
        # 按视频数量排序
        courses_data.sort(key=lambda x: x['video_count'], reverse=True)
        
        return jsonify({
            'code': 200,
            'msg': '获取知识点使用情况成功',
            'data': {
                'keyword_info': {
                    'id': str(keyword.id),
                    'name': keyword.name,
                    'category': keyword.category,
                    'description': keyword.description
                },
                'usage_summary': {
                    'total_videos': len(videos_data),
                    'total_courses': len(courses_data),
                    'avg_weight': round(sum(vk.weight for vk, _, _ in video_usage) / len(video_usage), 3) if video_usage else 0
                },
                'videos': videos_data,
                'courses': courses_data
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/course/<course_id>/videos-status', methods=['GET'])
@token_required
def get_course_videos_processing_status(course_id):
    """获取课程视频的知识图谱处理状态"""
    try:
        # 验证课程是否存在
        course = Course.query.get(course_id)
        if not course:
            return jsonify({
                'code': 404,
                'msg': '课程不存在',
                'data': None
            }), 404
        
        # 使用知识图谱处理器检查状态
        from tasks.knowledge_graph_processor import KnowledgeGraphProcessor
        processor = KnowledgeGraphProcessor()
        status = processor.check_videos_processed_status(course_id)
        
        return jsonify({
            'code': 200,
            'msg': '获取视频处理状态成功',
            'data': {
                'course_info': {
                    'id': str(course.id),
                    'name': course.name
                },
                'processing_status': status,
                'is_up_to_date': status['unprocessed_count'] == 0,
                'can_use_incremental': status['processed_count'] > 0 and status['unprocessed_count'] > 0
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

# ===== 知识图谱内容管理 API =====

@knowledge_graph_bp.route('/api/knowledge-graph/keywords', methods=['POST'])
@token_required
def create_keyword():
    """创建新知识点并建立与课程、视频的关系"""
    try:
        data = request.get_json()
        
        # 参数验证
        name = data.get('name', '').strip()
        category = data.get('category', '').strip()
        description = data.get('description', '').strip()
        course_ids = data.get('courseIds', [])
        video_ids = data.get('videoIds', [])
        default_weight = data.get('defaultWeight', 0.5)  # 默认权重
        
        if not name:
            return jsonify({
                'code': 400,
                'msg': '知识点名称不能为空',
                'data': None
            }), 400
            
        if not category:
            return jsonify({
                'code': 400,
                'msg': '知识点分类不能为空',
                'data': None
            }), 400
            
        # 验证分类是否有效
        valid_categories = ['core_concept', 'main_module', 'specific_point', '一级知识点', '二级知识点', '三级知识点']
        # 中文分类到英文代码的映射
        category_mapping = {
            '一级知识点': 'core_concept',
            '二级知识点': 'main_module',
            '三级知识点': 'specific_point'
        }
        
        if category not in valid_categories:
            return jsonify({
                'code': 400,
                'msg': f'知识点分类必须是以下之一: core_concept(一级知识点), main_module(二级知识点), specific_point(三级知识点)',
                'data': None
            }), 400
            
        # 如果是中文分类，转换为对应的英文代码
        if category in category_mapping:
            category = category_mapping[category]
        
        # 验证权重范围
        try:
            default_weight = float(default_weight)
            if default_weight < 0 or default_weight > 1:
                return jsonify({
                    'code': 400,
                    'msg': '默认权重必须在0-1之间',
                    'data': None
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'code': 400,
                'msg': '默认权重必须是数字',
                'data': None
            }), 400
        
        # 验证至少关联一个课程或视频
        if not course_ids and not video_ids:
            return jsonify({
                'code': 400,
                'msg': '至少需要关联一个课程或视频',
                'data': None
            }), 400
        
        # 验证课程是否存在
        existing_courses = []
        if course_ids:
            existing_courses = Course.query.filter(Course.id.in_(course_ids)).all()
            existing_course_ids = [str(c.id) for c in existing_courses]
            if len(existing_courses) != len(course_ids):
                missing_courses = set(course_ids) - set(existing_course_ids)
                return jsonify({
                    'code': 404,
                    'msg': f'课程不存在: {", ".join(missing_courses)}',
                    'data': None
                }), 404
        
        # 验证视频是否存在
        existing_videos = []
        if video_ids:
            existing_videos = Video.query.filter(
                Video.id.in_(video_ids),
                Video.is_deleted == False
            ).all()
            existing_video_ids = [str(v.id) for v in existing_videos]
            if len(existing_videos) != len(video_ids):
                missing_videos = set(video_ids) - set(existing_video_ids)
                return jsonify({
                    'code': 404,
                    'msg': f'视频不存在或已删除: {", ".join(missing_videos)}',
                    'data': None
                }), 404
        
        # 检查知识点是否已存在
        existing_keyword = Keyword.query.filter_by(name=name).first()
        if existing_keyword:
            return jsonify({
                'code': 409,
                'msg': '知识点已存在',
                'data': {
                    'existing_keyword': existing_keyword.to_dict(),
                    'hint': '如需为现有知识点添加关联，请使用更新接口'
                }
            }), 409
        
        # 开始事务操作
        try:
            # 创建新知识点
            keyword = Keyword(
                name=name,
                category=category,
                description=description if description else None
            )
            
            db.session.add(keyword)
            db.session.flush()  # 获取keyword.id
            
            # 建立课程知识点关系
            course_relations = []
            for course in existing_courses:
                # 检查是否已存在关系
                existing_ck = CourseKeyword.query.filter_by(
                    course_id=course.id,
                    keyword_id=keyword.id
                ).first()
                
                if not existing_ck:
                    course_keyword = CourseKeyword(
                        course_id=course.id,
                        keyword_id=keyword.id,
                        video_count=0,  # 初始为0，后续会更新
                        avg_weight=default_weight
                    )
                    db.session.add(course_keyword)
                    course_relations.append({
                        'course_id': str(course.id),
                        'course_name': course.name,
                        'status': 'created'
                    })
                else:
                    course_relations.append({
                        'course_id': str(course.id),
                        'course_name': course.name,
                        'status': 'already_exists'
                    })
            
            # 建立视频知识点关系
            video_relations = []
            video_course_map = {}  # 用于更新课程知识点统计
            
            for video in existing_videos:
                # 检查是否已存在关系
                existing_vk = VideoKeyword.query.filter_by(
                    video_id=video.id,
                    keyword_id=keyword.id
                ).first()
                
                if not existing_vk:
                    video_keyword = VideoKeyword(
                        video_id=video.id,
                        keyword_id=keyword.id,
                        weight=default_weight
                    )
                    db.session.add(video_keyword)
                    video_relations.append({
                        'video_id': str(video.id),
                        'video_title': video.title,
                        'course_id': str(video.course_id),
                        'weight': default_weight,
                        'status': 'created'
                    })
                    
                    # 统计课程信息
                    course_id = str(video.course_id)
                    if course_id not in video_course_map:
                        video_course_map[course_id] = {
                            'video_count': 0,
                            'total_weight': 0
                        }
                    video_course_map[course_id]['video_count'] += 1
                    video_course_map[course_id]['total_weight'] += default_weight
                else:
                    video_relations.append({
                        'video_id': str(video.id),
                        'video_title': video.title,
                        'course_id': str(video.course_id),
                        'weight': existing_vk.weight,
                        'status': 'already_exists'
                    })
            
            # 更新或创建课程知识点统计
            for course_id, stats in video_course_map.items():
                course_keyword = CourseKeyword.query.filter_by(
                    course_id=course_id,
                    keyword_id=keyword.id
                ).first()
                
                if course_keyword:
                    # 更新现有统计
                    course_keyword.video_count += stats['video_count']
                    # 重新计算平均权重
                    total_videos = VideoKeyword.query.filter_by(
                        keyword_id=keyword.id
                    ).join(Video).filter(
                        Video.course_id == course_id,
                        Video.is_deleted == False
                    ).count()
                    
                    if total_videos > 0:
                        avg_weight = db.session.query(
                            db.func.avg(VideoKeyword.weight)
                        ).filter_by(
                            keyword_id=keyword.id
                        ).join(Video).filter(
                            Video.course_id == course_id,
                            Video.is_deleted == False
                        ).scalar()
                        course_keyword.avg_weight = avg_weight or default_weight
                else:
                    # 创建新的课程知识点关系
                    course_keyword = CourseKeyword(
                        course_id=course_id,
                        keyword_id=keyword.id,
                        video_count=stats['video_count'],
                        avg_weight=stats['total_weight'] / stats['video_count'] if stats['video_count'] > 0 else default_weight
                    )
                    db.session.add(course_keyword)
            
            # 提交事务
            db.session.commit()
            
            # 构建返回数据
            result_data = {
                'keyword': keyword.to_dict(),
                'relations': {
                    'courses': course_relations,
                    'videos': video_relations
                },
                'statistics': {
                    'total_course_relations': len([r for r in course_relations if r['status'] == 'created']),
                    'total_video_relations': len([r for r in video_relations if r['status'] == 'created']),
                    'existing_course_relations': len([r for r in course_relations if r['status'] == 'already_exists']),
                    'existing_video_relations': len([r for r in video_relations if r['status'] == 'already_exists'])
                }
            }
            
            return jsonify({
                'code': 200,
                'msg': '知识点创建成功并建立关系',
                'data': result_data
            })
            
        except Exception as inner_e:
            db.session.rollback()
            logger.error(f"创建知识点关系时发生错误: {str(inner_e)}")
            raise inner_e
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建知识点失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/keywords/<keyword_id>', methods=['PUT'])
@token_required
def update_keyword(keyword_id):
    """更新知识点信息"""
    try:
        # 验证知识点是否存在
        keyword = Keyword.query.get(keyword_id)
        if not keyword:
            return jsonify({
                'code': 404,
                'msg': '知识点不存在',
                'data': None
            }), 404
        
        data = request.get_json()
        
        # 获取更新参数
        name = data.get('name', '').strip()
        category = data.get('category', '').strip()
        description = data.get('description', '').strip()
        course_ids = data.get('courseIds', [])
        video_ids = data.get('videoIds', [])
        document_ids = data.get('documentIds', [])
        
        # 验证参数
        if not name or not category:
            return jsonify({
                'code': 400,
                'msg': '知识点名称和分类不能为空',
                'data': None
            }), 400

        if name != keyword.name:
            # 检查新名称是否已被其他知识点使用
            existing_keyword = Keyword.query.filter(
                Keyword.name == name,
                Keyword.id != keyword.id
            ).first()
            if existing_keyword:
                return jsonify({
                    'code': 409,
                    'msg': '知识点名称已被使用',
                    'data': None
                }), 409
            keyword.name = name
        
        if category:
            # 验证分类是否有效
            valid_categories = ['core_concept', 'main_module', 'specific_point', '一级知识点', '二级知识点', '三级知识点']
            # 中文分类到英文代码的映射
            category_mapping = {
                '一级知识点': 'core_concept',
                '二级知识点': 'main_module',
                '三级知识点': 'specific_point'
            }
            
            if category not in valid_categories:
                return jsonify({
                    'code': 400,
                    'msg': f'知识点分类必须是以下之一: core_concept(一级知识点), main_module(二级知识点), specific_point(三级知识点)',
                    'data': None
                }), 400
                
            # 如果是中文分类，转换为对应的英文代码
            if category in category_mapping:
                category = category_mapping[category]
                
            keyword.category = category
        
        if 'description' in data:  # 允许设置为空字符串
            keyword.description = description if description else None
        
        # 更新课程关联
        if course_ids is not None:
            # 删除现有关联
            CourseKeyword.query.filter_by(keyword_id=keyword_id).delete()
            # 添加新关联
            for course_id in course_ids:
                course_keyword = CourseKeyword(course_id=course_id, keyword_id=keyword_id)
                db.session.add(course_keyword)
        
        # 更新视频关联
        if video_ids is not None:
            # 删除现有关联
            VideoKeyword.query.filter_by(keyword_id=keyword_id).delete()
            # 添加新关联
            for video_id in video_ids:
                video_keyword = VideoKeyword(video_id=video_id, keyword_id=keyword_id)
                db.session.add(video_keyword)
        
        # 更新文档关联
        if document_ids is not None:
            # 删除现有关联
            DocumentKeyword.query.filter_by(keyword_id=keyword_id).delete()
            # 添加新关联
            for document_id in document_ids:
                document_keyword = DocumentKeyword(document_id=document_id, keyword_id=keyword_id)
                db.session.add(document_keyword)
        
        keyword.update_time = datetime.now()
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'msg': '知识点更新成功',
            'data': keyword.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/keywords/<keyword_id>', methods=['DELETE'])
@token_required
def delete_keyword(keyword_id):
    # 兼容多种 true 写法
    force_delete_raw = request.args.get('force', 'false')
    force_delete = str(force_delete_raw).lower() in ['true', '1']
    print('force_delete:', force_delete, 'raw:', force_delete_raw)
    """删除知识点"""
    try:
        # 验证知识点是否存在
        keyword = Keyword.query.get(keyword_id)
        if not keyword:
            return jsonify({
                'code': 404,
                'msg': '知识点不存在',
                'data': None
            }), 404

        # 检查是否有关联
        video_keyword_count = VideoKeyword.query.filter_by(keyword_id=keyword_id).count()
        document_keyword_count = DocumentKeyword.query.filter_by(keyword_id=keyword_id).count()
        course_keyword_count = CourseKeyword.query.filter_by(keyword_id=keyword_id).count()
        relation_count = KeywordRelation.query.filter(
            (KeywordRelation.source_keyword_id == keyword_id) |
            (KeywordRelation.target_keyword_id == keyword_id)
        ).count()

        if not force_delete and (video_keyword_count > 0 or document_keyword_count > 0 or course_keyword_count > 0 or relation_count > 0):
            return jsonify({
                'code': 409,
                'msg': '知识点正在被使用，无法删除',
                'data': {
                    'video_associations': video_keyword_count,
                    'document_associations': document_keyword_count,
                    'course_associations': course_keyword_count,
                    'relations': relation_count,
                    'hint': '如需强制删除，请添加参数 ?force=true'
                }
            }), 409

        # 强制删除时，先删除所有相关数据
        if force_delete:
            VideoKeyword.query.filter_by(keyword_id=keyword_id).delete()
            DocumentKeyword.query.filter_by(keyword_id=keyword_id).delete()
            CourseKeyword.query.filter_by(keyword_id=keyword_id).delete()
            KeywordRelation.query.filter(
                (KeywordRelation.source_keyword_id == keyword_id) |
                (KeywordRelation.target_keyword_id == keyword_id)
            ).delete()

        # 删除知识点
        db.session.delete(keyword)
        db.session.commit()

        return jsonify({
            'code': 200,
            'msg': '知识点删除成功',
            'data': None
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/relations', methods=['POST'])
@token_required
def create_keyword_relation():
    """创建知识点关系"""
    try:
        data = request.get_json()
        
        # 参数验证
        source_keyword_id = data.get('sourceKeywordId')
        target_keyword_id = data.get('targetKeywordId')
        relation_type = data.get('relationType', '').strip()
        strength = data.get('strength', 1.0)
        description = data.get('description', '').strip()
        
        if not source_keyword_id or not target_keyword_id:
            return jsonify({
                'code': 400,
                'msg': '源知识点和目标知识点不能为空',
                'data': None
            }), 400
            
        if not relation_type:
            return jsonify({
                'code': 400,
                'msg': '关系类型不能为空',
                'data': None
            }), 400
        
        # 验证关系类型
        valid_relation_types = ['prerequisite', 'related', 'contains', 'opposite', 'similar']
        if relation_type not in valid_relation_types:
            return jsonify({
                'code': 400,
                'msg': f'关系类型必须是以下之一: {", ".join(valid_relation_types)}',
                'data': None
            }), 400
        
        # 验证强度范围
        try:
            strength = float(strength)
            if strength < 0 or strength > 1:
                return jsonify({
                    'code': 400,
                    'msg': '关系强度必须在0-1之间',
                    'data': None
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'code': 400,
                'msg': '关系强度必须是数字',
                'data': None
            }), 400
        
        # 验证知识点是否存在
        source_keyword = Keyword.query.get(source_keyword_id)
        target_keyword = Keyword.query.get(target_keyword_id)
        
        if not source_keyword:
            return jsonify({
                'code': 404,
                'msg': '源知识点不存在',
                'data': None
            }), 404
            
        if not target_keyword:
            return jsonify({
                'code': 404,
                'msg': '目标知识点不存在',
                'data': None
            }), 404
        
        # 检查是否已存在相同的关系
        existing_relation = KeywordRelation.query.filter_by(
            source_keyword_id=source_keyword_id,
            target_keyword_id=target_keyword_id,
            relation_type=relation_type
        ).first()
        
        if existing_relation:
            return jsonify({
                'code': 409,
                'msg': '该关系已存在',
                'data': None
            }), 409
        
        # 创建新关系
        relation = KeywordRelation(
            source_keyword_id=source_keyword_id,
            target_keyword_id=target_keyword_id,
            relation_type=relation_type,
            strength=strength,
            description=description if description else None
        )
        
        db.session.add(relation)
        db.session.commit()
        
        # 构建返回数据
        result = relation.to_dict()
        result['source_keyword'] = source_keyword.to_dict()
        result['target_keyword'] = target_keyword.to_dict()
        
        return jsonify({
            'code': 200,
            'msg': '知识点关系创建成功',
            'data': result
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/relations/<relation_id>', methods=['PUT'])
@token_required
def update_keyword_relation(relation_id):
    """更新知识点关系"""
    try:
        # 验证关系是否存在
        relation = KeywordRelation.query.get(relation_id)
        if not relation:
            return jsonify({
                'code': 404,
                'msg': '知识点关系不存在',
                'data': None
            }), 404
        
        data = request.get_json()
        
        # 获取更新参数
        relation_type = data.get('relationType', '').strip()
        strength = data.get('strength')
        description = data.get('description', '').strip()
        
        # 更新关系类型
        if relation_type:
            valid_relation_types = ['prerequisite', 'related', 'contains', 'opposite', 'similar']
            if relation_type not in valid_relation_types:
                return jsonify({
                    'code': 400,
                    'msg': f'关系类型必须是以下之一: {", ".join(valid_relation_types)}',
                    'data': None
                }), 400
            relation.relation_type = relation_type
        
        # 更新强度
        if strength is not None:
            try:
                strength = float(strength)
                if strength < 0 or strength > 1:
                    return jsonify({
                        'code': 400,
                        'msg': '关系强度必须在0-1之间',
                        'data': None
                    }), 400
                relation.strength = strength
            except (ValueError, TypeError):
                return jsonify({
                    'code': 400,
                    'msg': '关系强度必须是数字',
                    'data': None
                }), 400
        
        # 更新描述
        if 'description' in data:
            relation.description = description if description else None
        
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'msg': '知识点关系更新成功',
            'data': relation.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/relations/<relation_id>', methods=['DELETE'])
@token_required
def delete_keyword_relation(relation_id):
    """删除知识点关系"""
    try:
        # 验证关系是否存在
        relation = KeywordRelation.query.get(relation_id)
        if not relation:
            return jsonify({
                'code': 404,
                'msg': '知识点关系不存在',
                'data': None
            }), 404
        
        db.session.delete(relation)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'msg': '知识点关系删除成功',
            'data': None
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/video-keywords', methods=['POST'])
@token_required
def add_video_keyword():
    """为视频添加知识点"""
    try:
        data = request.get_json()
        
        # 参数验证
        video_id = data.get('videoId')
        keyword_id = data.get('keywordId')
        weight = data.get('weight', 1.0)
        
        if not video_id or not keyword_id:
            return jsonify({
                'code': 400,
                'msg': '视频ID和知识点ID不能为空',
                'data': None
            }), 400
        
        # 验证权重
        try:
            weight = float(weight)
            if weight < 0 or weight > 1:
                return jsonify({
                    'code': 400,
                    'msg': '知识点权重必须在0-1之间',
                    'data': None
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'code': 400,
                'msg': '知识点权重必须是数字',
                'data': None
            }), 400
        
        # 验证视频和知识点是否存在
        video = Video.query.get(video_id)
        keyword = Keyword.query.get(keyword_id)
        
        if not video:
            return jsonify({
                'code': 404,
                'msg': '视频不存在',
                'data': None
            }), 404
            
        if not keyword:
            return jsonify({
                'code': 404,
                'msg': '知识点不存在',
                'data': None
            }), 404
        
        # 检查是否已存在关联
        existing_vk = VideoKeyword.query.filter_by(
            video_id=video_id,
            keyword_id=keyword_id
        ).first()
        
        if existing_vk:
            # 更新权重
            existing_vk.weight = weight
            db.session.commit()
            
            return jsonify({
                'code': 200,
                'msg': '视频知识点权重已更新',
                'data': {
                    'id': str(existing_vk.id),
                    'video_id': str(video_id),
                    'keyword_id': str(keyword_id),
                    'weight': weight,
                    'keyword_name': keyword.name
                }
            })
        
        # 创建新关联
        video_keyword = VideoKeyword(
            video_id=video_id,
            keyword_id=keyword_id,
            weight=weight
        )
        
        db.session.add(video_keyword)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'msg': '视频知识点添加成功',
            'data': {
                'id': str(video_keyword.id),
                'video_id': str(video_id),
                'keyword_id': str(keyword_id),
                'weight': weight,
                'keyword_name': keyword.name
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/document-keywords', methods=['POST'])
@token_required
def add_document_keyword():
    """为文档添加知识点"""
    try:
        data = request.get_json()
        
        # 参数验证
        document_id = data.get('documentId')
        keyword_id = data.get('keywordId')
        weight = data.get('weight', 1.0)
        
        if not document_id or not keyword_id:
            return jsonify({
                'code': 400,
                'msg': '文档ID和知识点ID不能为空',
                'data': None
            }), 400
        
        # 验证权重
        try:
            weight = float(weight)
            if weight < 0 or weight > 1:
                return jsonify({
                    'code': 400,
                    'msg': '知识点权重必须在0-1之间',
                    'data': None
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'code': 400,
                'msg': '知识点权重必须是数字',
                'data': None
            }), 400
        
        # 验证文档和知识点是否存在
        document = Document.query.get(document_id)
        keyword = Keyword.query.get(keyword_id)
        
        if not document:
            return jsonify({
                'code': 404,
                'msg': '文档不存在',
                'data': None
            }), 404
            
        if not keyword:
            return jsonify({
                'code': 404,
                'msg': '知识点不存在',
                'data': None
            }), 404
        
        # 检查是否已存在关联
        existing_dk = DocumentKeyword.query.filter_by(
            document_id=document_id,
            keyword_id=keyword_id
        ).first()
        
        if existing_dk:
            # 更新权重
            existing_dk.weight = weight
            db.session.commit()
            
            return jsonify({
                'code': 200,
                'msg': '文档知识点权重已更新',
                'data': {
                    'id': str(existing_dk.id),
                    'document_id': str(document_id),
                    'keyword_id': str(keyword_id),
                    'weight': weight,
                    'keyword_name': keyword.name
                }
            })
        
        # 创建新关联
        document_keyword = DocumentKeyword(
            document_id=document_id,
            keyword_id=keyword_id,
            weight=weight
        )
        
        db.session.add(document_keyword)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'msg': '文档知识点添加成功',
            'data': {
                'id': str(document_keyword.id),
                'document_id': str(document_id),
                'keyword_id': str(keyword_id),
                'weight': weight,
                'keyword_name': keyword.name
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/document-keywords/<document_keyword_id>', methods=['PUT'])
@token_required
def update_document_keyword(document_keyword_id):
    """更新文档知识点权重"""
    try:
        # 验证关联是否存在
        document_keyword = DocumentKeyword.query.get(document_keyword_id)
        if not document_keyword:
            return jsonify({
                'code': 404,
                'msg': '文档知识点关联不存在',
                'data': None
            }), 404
        
        data = request.get_json()
        weight = data.get('weight')
        
        if weight is None:
            return jsonify({
                'code': 400,
                'msg': '权重不能为空',
                'data': None
            }), 400
        
        # 验证权重
        try:
            weight = float(weight)
            if weight < 0 or weight > 1:
                return jsonify({
                    'code': 400,
                    'msg': '知识点权重必须在0-1之间',
                    'data': None
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'code': 400,
                'msg': '知识点权重必须是数字',
                'data': None
            }), 400
        
        # 更新权重
        document_keyword.weight = weight
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'msg': '文档知识点权重更新成功',
            'data': {
                'id': str(document_keyword.id),
                'document_id': str(document_keyword.document_id),
                'keyword_id': str(document_keyword.keyword_id),
                'weight': weight
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/document-keywords/<document_keyword_id>', methods=['DELETE'])
@token_required
def delete_document_keyword(document_keyword_id):
    """删除文档知识点关联"""
    try:
        # 验证关联是否存在
        document_keyword = DocumentKeyword.query.get(document_keyword_id)
        if not document_keyword:
            return jsonify({
                'code': 404,
                'msg': '文档知识点关联不存在',
                'data': None
            }), 404
        
        # 删除关联
        db.session.delete(document_keyword)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'msg': '文档知识点关联删除成功',
            'data': None
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/document/<document_id>/keywords', methods=['GET'])
@token_required
def get_document_keywords(document_id):
    """获取文档的所有知识点"""
    try:
        # 验证文档是否存在
        document = Document.query.get(document_id)
        if not document:
            return jsonify({
                'code': 404,
                'msg': '文档不存在',
                'data': None
            }), 404
        
        # 获取文档知识点
        document_keywords = db.session.query(
            Keyword, DocumentKeyword
        ).join(
            DocumentKeyword, Keyword.id == DocumentKeyword.keyword_id
        ).filter(
            DocumentKeyword.document_id == document_id
        ).order_by(DocumentKeyword.weight.desc()).all()
        
        keywords = []
        for keyword, dk in document_keywords:
            keyword_data = keyword.to_dict()
            keyword_data['weight'] = round(dk.weight, 2)
            keyword_data['document_keyword_id'] = str(dk.id)
            keywords.append(keyword_data)
        
        return jsonify({
            'code': 200,
            'msg': '获取文档知识点成功',
            'data': {
                'document': {
                    'id': str(document.id),
                    'title': document.title,
                    'description': document.description
                },
                'keywords': keywords,
                'total': len(keywords)
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/video-keywords/<video_keyword_id>', methods=['PUT'])
@token_required
def update_video_keyword(video_keyword_id):
    """更新视频知识点权重"""
    try:
        # 验证关联是否存在
        video_keyword = VideoKeyword.query.get(video_keyword_id)
        if not video_keyword:
            return jsonify({
                'code': 404,
                'msg': '视频知识点关联不存在',
                'data': None
            }), 404
        
        data = request.get_json()
        weight = data.get('weight')
        
        if weight is None:
            return jsonify({
                'code': 400,
                'msg': '权重参数不能为空',
                'data': None
            }), 400
        
        # 验证权重
        try:
            weight = float(weight)
            if weight < 0 or weight > 1:
                return jsonify({
                    'code': 400,
                    'msg': '知识点权重必须在0-1之间',
                    'data': None
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'code': 400,
                'msg': '知识点权重必须是数字',
                'data': None
            }), 400
        
        video_keyword.weight = weight
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'msg': '视频知识点权重更新成功',
            'data': {
                'id': str(video_keyword.id),
                'video_id': str(video_keyword.video_id),
                'keyword_id': str(video_keyword.keyword_id),
                'weight': weight
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/video-keywords/<video_keyword_id>', methods=['DELETE'])
@token_required
def delete_video_keyword(video_keyword_id):
    """删除视频知识点关联"""
    try:
        # 验证关联是否存在
        video_keyword = VideoKeyword.query.get(video_keyword_id)
        if not video_keyword:
            return jsonify({
                'code': 404,
                'msg': '视频知识点关联不存在',
                'data': None
            }), 404
        
        db.session.delete(video_keyword)
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'msg': '视频知识点关联删除成功',
            'data': None
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/batch-operations', methods=['POST'])
@token_required
def batch_operations():
    """批量操作（批量创建/更新/删除知识点和关系）"""
    try:
        data = request.get_json()
        operation_type = data.get('operationType')  # 'create', 'update', 'delete'
        target_type = data.get('targetType')  # 'keywords', 'relations', 'video_keywords'
        items = data.get('items', [])
        
        if not operation_type or not target_type or not items:
            return jsonify({
                'code': 400,
                'msg': '操作类型、目标类型和操作项目不能为空',
                'data': None
            }), 400
        
        results = []
        errors = []
        
        # 批量操作知识点
        if target_type == 'keywords':
            for i, item in enumerate(items):
                try:
                    if operation_type == 'create':
                        # 创建知识点
                        name = item.get('name', '').strip()
                        category = item.get('category', '').strip()
                        description = item.get('description', '').strip()
                        
                        if not name or not category:
                            errors.append(f"第{i+1}项：名称和分类不能为空")
                            continue
                        
                        # 检查是否已存在
                        if Keyword.query.filter_by(name=name).first():
                            errors.append(f"第{i+1}项：知识点'{name}'已存在")
                            continue
                        
                        keyword = Keyword(
                            name=name,
                            category=category,
                            description=description if description else None
                        )
                        db.session.add(keyword)
                        results.append({
                            'index': i,
                            'status': 'success',
                            'data': {'name': name, 'category': category}
                        })
                        
                    elif operation_type == 'update':
                        # 更新知识点
                        keyword_id = item.get('id')
                        if not keyword_id:
                            errors.append(f"第{i+1}项：知识点ID不能为空")
                            continue
                        
                        keyword = Keyword.query.get(keyword_id)
                        if not keyword:
                            errors.append(f"第{i+1}项：知识点不存在")
                            continue
                        
                        if 'name' in item and item['name'].strip():
                            keyword.name = item['name'].strip()
                        if 'category' in item and item['category'].strip():
                            keyword.category = item['category'].strip()
                        if 'description' in item:
                            keyword.description = item['description'].strip() if item['description'].strip() else None
                        
                        keyword.update_time = datetime.now()
                        results.append({
                            'index': i,
                            'status': 'success',
                            'data': {'id': str(keyword_id)}
                        })
                        
                    elif operation_type == 'delete':
                        # 删除知识点
                        keyword_id = item.get('id')
                        if not keyword_id:
                            errors.append(f"第{i+1}项：知识点ID不能为空")
                            continue
                        
                        keyword = Keyword.query.get(keyword_id)
                        if not keyword:
                            errors.append(f"第{i+1}项：知识点不存在")
                            continue
                        
                        # 强制删除相关数据
                        VideoKeyword.query.filter_by(keyword_id=keyword_id).delete()
                        DocumentKeyword.query.filter_by(keyword_id=keyword_id).delete()
                        CourseKeyword.query.filter_by(keyword_id=keyword_id).delete()
                        KeywordRelation.query.filter(
                            (KeywordRelation.source_keyword_id == keyword_id) |
                            (KeywordRelation.target_keyword_id == keyword_id)
                        ).delete()
                        db.session.delete(keyword)
                        
                        results.append({
                            'index': i,
                            'status': 'success',
                            'data': {'id': str(keyword_id)}
                        })
                        
                except Exception as e:
                    errors.append(f"第{i+1}项：{str(e)}")
        
        # 批量操作关系
        elif target_type == 'relations':
            for i, item in enumerate(items):
                try:
                    if operation_type == 'create':
                        # 创建关系
                        source_id = item.get('sourceKeywordId')
                        target_id = item.get('targetKeywordId')
                        relation_type = item.get('relationType', '').strip()
                        strength = item.get('strength', 1.0)
                        description = item.get('description', '').strip()
                        
                        if not source_id or not target_id or not relation_type:
                            errors.append(f"第{i+1}项：源知识点、目标知识点和关系类型不能为空")
                            continue
                        
                        # 检查知识点是否存在
                        if not Keyword.query.get(source_id) or not Keyword.query.get(target_id):
                            errors.append(f"第{i+1}项：知识点不存在")
                            continue
                        
                        # 检查关系是否已存在
                        if KeywordRelation.query.filter_by(
                            source_keyword_id=source_id,
                            target_keyword_id=target_id,
                            relation_type=relation_type
                        ).first():
                            errors.append(f"第{i+1}项：关系已存在")
                            continue
                        
                        relation = KeywordRelation(
                            source_keyword_id=source_id,
                            target_keyword_id=target_id,
                            relation_type=relation_type,
                            strength=float(strength),
                            description=description if description else None
                        )
                        db.session.add(relation)
                        results.append({
                            'index': i,
                            'status': 'success',
                            'data': {
                                'source_keyword_id': str(source_id),
                                'target_keyword_id': str(target_id),
                                'relation_type': relation_type
                            }
                        })
                        
                except Exception as e:
                    errors.append(f"第{i+1}项：{str(e)}")
        
        # 提交所有更改
        if not errors:
            db.session.commit()
        else:
            db.session.rollback()
        
        return jsonify({
            'code': 200 if not errors else 207,  # 207表示部分成功
            'msg': f'批量操作完成，成功{len(results)}项，失败{len(errors)}项',
            'data': {
                'success_count': len(results),
                'error_count': len(errors),
                'results': results,
                'errors': errors
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

# ===== Neo4j 增强功能 API =====

@knowledge_graph_bp.route('/api/knowledge-graph/prerequisite-path', methods=['GET'])
@token_required
def get_prerequisite_path():
    """
    获取知识点的前置知识路径（Neo4j增强）
    
    GET /api/knowledge-graph/prerequisite-path?keyword=知识点名称
    """
    try:
        keyword_name = request.args.get('keyword')
        if not keyword_name:
            return jsonify({
                'code': 400,
                'msg': '缺少知识点参数',
                'data': None
            }), 400
        
        query_service = get_query_service()
        paths = query_service.find_prerequisite_knowledge(keyword_name)
        
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': {
                'keyword': keyword_name,
                'prerequisite_paths': paths,
                'path_count': len(paths)
            }
        })
        
    except Exception as e:
        logger.error(f"获取前置知识路径失败: {e}")
        return jsonify({
            'code': 500,
            'msg': f'查询失败: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/recommendations', methods=['GET'])
@token_required
def get_smart_recommendations():
    """
    获取智能知识点推荐（Neo4j增强）
    
    GET /api/knowledge-graph/recommendations?keyword=知识点名称
    """
    try:
        keyword_name = request.args.get('keyword')
        if not keyword_name:
            return jsonify({
                'code': 400,
                'msg': '缺少知识点参数',
                'data': None
            }), 400
        
        query_service = get_query_service()
        recommendations = query_service.get_smart_recommendations(keyword_name)
        
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': {
                'keyword': keyword_name,
                'recommendations': recommendations,
                'recommendation_count': len(recommendations)
            }
        })
        
    except Exception as e:
        logger.error(f"获取智能推荐失败: {e}")
        return jsonify({
            'code': 500,
            'msg': f'查询失败: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/sync-status', methods=['GET'])
@token_required
def get_sync_status():
    """
    获取Neo4j同步状态
    
    GET /api/knowledge-graph/sync-status
    """
    try:
        from services.knowledge_graph_service import get_neo4j_adapter
        
        adapter = get_neo4j_adapter()
        
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': {
                'neo4j_available': adapter.is_available(),
                'status': 'connected' if adapter.is_available() else 'disconnected'
            }
        })
        
    except Exception as e:
        logger.error(f"获取同步状态失败: {e}")
        return jsonify({
            'code': 500,
            'msg': f'查询失败: {str(e)}',
            'data': None
        }), 500

# ===== 知识图谱辅助查询 API =====

@knowledge_graph_bp.route('/api/knowledge-graph/keywords/list', methods=['GET'])
@token_required
def list_all_keywords():
    """获取所有知识点列表（用于下拉选择等）"""
    try:
        # 获取查询参数
        category = request.args.get('category')
        search = request.args.get('search', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)
        
        # 构建查询
        query = Keyword.query
        
        if category:
            query = query.filter(Keyword.category == category)
            
        if search:
            query = query.filter(
                db.or_(
                    Keyword.name.contains(search),
                    Keyword.description.contains(search)
                )
            )
        
        # 分页查询
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        keywords = []
        for keyword in pagination.items:
            # 获取使用统计
            video_count = VideoKeyword.query.filter_by(keyword_id=keyword.id).count()
            document_count = DocumentKeyword.query.filter_by(keyword_id=keyword.id).count()
            course_count = CourseKeyword.query.filter_by(keyword_id=keyword.id).count()
            
            keywords.append({
                'id': str(keyword.id),
                'name': keyword.name,
                'category': keyword.category,
                'description': keyword.description,
                'video_count': video_count,
                'document_count': document_count,
                'course_count': course_count,
                'create_time': keyword.create_time.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'code': 200,
            'msg': '获取知识点列表成功',
            'data': {
                'keywords': keywords,
                'pagination': {
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'current_page': page,
                    'per_page': per_page,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/relations/list', methods=['GET'])
@token_required
def list_keyword_relations():
    """获取知识点关系列表"""
    try:
        # 获取查询参数
        source_keyword_id = request.args.get('sourceKeywordId')
        target_keyword_id = request.args.get('targetKeywordId')
        relation_type = request.args.get('relationType')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # 构建查询
        source_kw = db.aliased(Keyword)
        target_kw = db.aliased(Keyword)
        
        query = db.session.query(
            KeywordRelation, 
            source_kw, 
            target_kw
        ).join(
            source_kw, 
            KeywordRelation.source_keyword_id == source_kw.id
        ).join(
            target_kw, 
            KeywordRelation.target_keyword_id == target_kw.id
        )
        
        if source_keyword_id:
            query = query.filter(KeywordRelation.source_keyword_id == source_keyword_id)
            
        if target_keyword_id:
            query = query.filter(KeywordRelation.target_keyword_id == target_keyword_id)
            
        if relation_type:
            query = query.filter(KeywordRelation.relation_type == relation_type)
        
        # 分页查询
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        relations = []
        for relation, source_kw, target_kw in pagination.items:
            relations.append({
                'id': str(relation.id),
                'source_keyword': {
                    'id': str(source_kw.id),
                    'name': source_kw.name,
                    'category': source_kw.category
                },
                'target_keyword': {
                    'id': str(target_kw.id),
                    'name': target_kw.name,
                    'category': target_kw.category
                },
                'relation_type': relation.relation_type,
                'strength': relation.strength,
                'description': relation.description,
                'create_time': relation.create_time.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'code': 200,
            'msg': '获取知识点关系列表成功',
            'data': {
                'relations': relations,
                'pagination': {
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'current_page': page,
                    'per_page': per_page,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/statistics', methods=['GET'])
@token_required
def get_knowledge_graph_statistics():
    """获取知识图谱统计信息"""
    try:
        # 基础统计
        total_keywords = Keyword.query.count()
        total_relations = KeywordRelation.query.count()
        total_video_keywords = VideoKeyword.query.count()
        total_document_keywords = DocumentKeyword.query.count()
        total_course_keywords = CourseKeyword.query.count()
        
        # 分类统计
        category_stats = db.session.query(
            Keyword.category,
            db.func.count(Keyword.id).label('count')
        ).group_by(Keyword.category).all()
        
        # 关系类型统计
        relation_type_stats = db.session.query(
            KeywordRelation.relation_type,
            db.func.count(KeywordRelation.id).label('count')
        ).group_by(KeywordRelation.relation_type).all()
        
        # 最活跃的知识点（被关联最多的）
        top_keywords = db.session.query(
            Keyword,
            db.func.count(VideoKeyword.id).label('video_count')
        ).join(VideoKeyword).group_by(Keyword.id).order_by(
            db.func.count(VideoKeyword.id).desc()
        ).limit(10).all()
        
        return jsonify({
            'code': 200,
            'msg': '获取知识图谱统计信息成功',
            'data': {
                'basic_stats': {
                    'total_keywords': total_keywords,
                    'total_relations': total_relations,
                    'total_video_keywords': total_video_keywords,
                    'total_document_keywords': total_document_keywords,
                    'total_course_keywords': total_course_keywords
                },
                'category_distribution': {cat: count for cat, count in category_stats},
                'relation_type_distribution': {rt: count for rt, count in relation_type_stats},
                'top_keywords': [
                    {
                        'id': str(keyword.id),
                        'name': keyword.name,
                        'category': keyword.category,
                        'video_count': video_count
                    }
                    for keyword, video_count in top_keywords
                ]
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/validate', methods=['POST'])
@token_required
def validate_knowledge_graph():
    """验证知识图谱数据完整性"""
    try:
        issues = []
        
        # 检查孤立的知识点（没有任何关联的）
        orphaned_keywords = db.session.query(Keyword).outerjoin(VideoKeyword).outerjoin(
            CourseKeyword
        ).outerjoin(
            KeywordRelation, 
            db.or_(
                KeywordRelation.source_keyword_id == Keyword.id,
                KeywordRelation.target_keyword_id == Keyword.id
            )
        ).filter(
            VideoKeyword.id.is_(None),
            CourseKeyword.id.is_(None),
            KeywordRelation.id.is_(None)
        ).all()
        
        if orphaned_keywords:
            issues.append({
                'type': 'orphaned_keywords',
                'count': len(orphaned_keywords),
                'message': f'发现{len(orphaned_keywords)}个孤立知识点（没有任何关联）',
                'items': [{'id': str(kw.id), 'name': kw.name} for kw in orphaned_keywords[:10]]
            })
        
        # 检查无效的关系（指向不存在的知识点）
        invalid_relations = db.session.query(KeywordRelation).outerjoin(
            Keyword.alias('source'), 
            KeywordRelation.source_keyword_id == Keyword.id
        ).outerjoin(
            Keyword.alias('target'),
            KeywordRelation.target_keyword_id == Keyword.id
        ).filter(
            db.or_(
                Keyword.alias('source').id.is_(None),
                Keyword.alias('target').id.is_(None)
            )
        ).all()
        
        if invalid_relations:
            issues.append({
                'type': 'invalid_relations',
                'count': len(invalid_relations),
                'message': f'发现{len(invalid_relations)}个无效关系（指向不存在的知识点）',
                'items': [{'id': str(rel.id)} for rel in invalid_relations[:10]]
            })
        
        # 检查重复的关系
        duplicate_relations = db.session.query(
            KeywordRelation.source_keyword_id,
            KeywordRelation.target_keyword_id,
            KeywordRelation.relation_type,
            db.func.count(KeywordRelation.id).label('count')
        ).group_by(
            KeywordRelation.source_keyword_id,
            KeywordRelation.target_keyword_id,
            KeywordRelation.relation_type
        ).having(db.func.count(KeywordRelation.id) > 1).all()
        
        if duplicate_relations:
            issues.append({
                'type': 'duplicate_relations',
                'count': len(duplicate_relations),
                'message': f'发现{len(duplicate_relations)}组重复关系',
                'items': [
                    {
                        'source_keyword_id': str(dr.source_keyword_id),
                        'target_keyword_id': str(dr.target_keyword_id),
                        'relation_type': dr.relation_type,
                        'duplicate_count': dr.count
                    }
                    for dr in duplicate_relations[:10]
                ]
            })
        
        return jsonify({
            'code': 200,
            'msg': '知识图谱验证完成',
            'data': {
                'is_valid': len(issues) == 0,
                'issues_count': len(issues),
                'issues': issues
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500
