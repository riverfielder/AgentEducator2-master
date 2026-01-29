#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识点详情和掌握程度API路由
提供知识点详情查看、掌握程度计算、学习进度跟踪等功能
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import func, and_, or_, desc
from models.models import (
    db, Keyword, KeywordRelation, KnowledgePointMastery,
    VideoKeyword, DocumentKeyword, QuestionKeyword,
    UserVideoProgress, DocumentProgress, StudentAnswer,
    Video, Document, Question, Assignment, Course,
    Users, StudentCourseEnrollment
)
from services.mastery_calculator import MasteryCalculator
from utils.auth import token_required
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
knowledge_point_bp = Blueprint('knowledge_point', __name__)


from tools.knowledge_point_info_tool import KnowledgePointInfoTool
from tools.student_learning_analyzer import StudentLearningAnalyzer

@knowledge_point_bp.route('/<keyword_id>', methods=['GET'])
@token_required
def get_knowledge_point_detail(keyword_id):
    """
    获取知识点详情
    
    Args:
        keyword_id: 知识点ID
        
    Returns:
        知识点详细信息，包括基本信息、相关资源、子知识点等
    """
    try:
        user_id = request.user.get('user_id')
        
        # 使用知识点信息工具获取完整信息
        knowledge_point_tool = KnowledgePointInfoTool()
        knowledge_point_info = knowledge_point_tool.get_knowledge_point_info(keyword_id, user_id)
        
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': knowledge_point_info
        })
    except Exception as e:
        logger.error(f'获取知识点详情失败: {str(e)}')
        return jsonify({
            'code': 500,
            'msg': '获取知识点详情失败',
            'data': None
        }), 500


@knowledge_point_bp.route('/learning/analysis', methods=['GET'])
@token_required
def analyze_learning_status():
    """
    分析学生学习状态
    
    Returns:
        学习状态分析结果，包括:
        - 整体学习进度
        - 最强/最弱知识点
        - AI学习建议
    """
    try:
        user_id = request.user.get('user_id')
        
        # 使用学习分析工具获取分析结果
        analyzer = StudentLearningAnalyzer()
        analysis_result = analyzer.analyze_learning_status(user_id)
        
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': analysis_result
        })
    except Exception as e:
        logger.error(f'分析学习状态失败: {str(e)}')
        return jsonify({
            'code': 500,
            'msg': '分析学习状态失败',
            'data': None
        }), 500

@knowledge_point_bp.route('/<keyword_id>/children', methods=['GET'])
@token_required
def get_knowledge_point_children(keyword_id):
    """
    获取知识点的子知识点
    
    Args:
        keyword_id: 知识点ID
        
    Returns:
        子知识点列表
    """
    try:
        user_id = request.user.get('user_id')
        
        # 获取子知识点关系
        child_relations = db.session.query(
            KeywordRelation, Keyword
        ).join(
            Keyword, KeywordRelation.target_keyword_id == Keyword.id
        ).filter(
            KeywordRelation.source_keyword_id == keyword_id
        ).all()
        
        children = []
        for relation, keyword in child_relations:
            # 获取掌握程度
            mastery = KnowledgePointMastery.query.filter_by(
                user_id=user_id, keyword_id=keyword.id
            ).first()
            
            children.append({
                'id': str(keyword.id),
                'name': keyword.name,
                'category': keyword.category,
                'description': keyword.description,
                'relation_type': relation.relation_type,
                'relation_strength': relation.strength,
                'mastery_level': mastery.mastery_level if mastery else 0.0,
                'last_updated': mastery.last_updated.isoformat() if mastery and mastery.last_updated else None
            })
        
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': {
                'children': children,
                'total': len(children)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting knowledge point children: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'获取子知识点失败: {str(e)}'
        }), 500


@knowledge_point_bp.route('/<keyword_id>/mastery', methods=['GET'])
@token_required
def get_knowledge_point_mastery(keyword_id):
    """
    获取知识点掌握程度详情
    
    Args:
        keyword_id: 知识点ID
        
    Returns:
        掌握程度详细信息
    """
    try:
        user_id = request.user.get('user_id')
        force_recalculate = request.args.get('recalculate', 'false').lower() == 'true'
        
        mastery_info = MasteryCalculator().calculate_mastery_level(
            user_id, keyword_id, force_recalculate=force_recalculate
        )
        
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': mastery_info
        })
        
    except Exception as e:
        logger.error(f"Error getting knowledge point mastery: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'获取掌握程度失败: {str(e)}'
        }), 500


@knowledge_point_bp.route('/<keyword_id>/learning-path', methods=['GET'])
@token_required
def get_knowledge_point_learning_path(keyword_id):
    """
    获取知识点学习路径建议
    
    Args:
        keyword_id: 知识点ID
        
    Returns:
        学习路径建议
    """
    try:
        user_id = request.user.get('user_id')
        
        # 获取知识点信息
        keyword = Keyword.query.get_or_404(keyword_id)
        
        # 获取当前掌握程度
        current_mastery = KnowledgePointMastery.query.filter_by(
            user_id=user_id, keyword_id=keyword_id
        ).first()
        
        current_level = current_mastery.mastery_level if current_mastery else 0.0
        
        # 生成学习建议
        suggestions = []
        
        # 如果掌握程度较低，建议先学习基础材料
        if current_level < 0.4:
            # 推荐相关视频
            video_keywords = db.session.query(
                VideoKeyword, Video, Course
            ).join(
                Video, VideoKeyword.video_id == Video.id
            ).join(
                Course, Video.course_id == Course.id
            ).filter(
                VideoKeyword.keyword_id == keyword_id
            ).order_by(VideoKeyword.weight.desc()).limit(3).all()
            
            for vk, video, course in video_keywords:
                progress = UserVideoProgress.query.filter_by(
                    user_id=user_id, video_id=video.id
                ).first()
                
                if not progress or progress.progress < 0.8:
                    suggestions.append({
                        'type': 'video',
                        'priority': 'high',
                        'resource_id': str(video.id),
                        'title': video.title,
                        'description': f'观看课程《{course.name}》中的视频',
                        'estimated_time': video.duration,
                        'current_progress': progress.progress if progress else 0.0
                    })
        
        # 如果基础掌握较好，配套练习题
        elif current_level >= 0.4 and current_level < 0.8:
            question_keywords = db.session.query(
                QuestionKeyword, Question, Assignment
            ).join(
                Question, QuestionKeyword.question_id == Question.id
            ).join(
                Assignment, Question.assignment_id == Assignment.id
            ).filter(
                QuestionKeyword.keyword_id == keyword_id,
                QuestionKeyword.difficulty_level <= 3  # 推荐中等难度以下的题目
            ).order_by(QuestionKeyword.difficulty_level).limit(5).all()
            
            for qk, question, assignment in question_keywords:
                student_answer = StudentAnswer.query.filter_by(
                    student_id=user_id, question_id=question.id
                ).first()
                
                if not student_answer or not student_answer.is_correct:
                    suggestions.append({
                        'type': 'exercise',
                        'priority': 'medium',
                        'resource_id': str(question.id),
                        'title': f'练习题 - {assignment.title}',
                        'description': f'完成难度等级{qk.difficulty_level}的练习题',
                        'difficulty_level': qk.difficulty_level,
                        'attempted': student_answer is not None
                    })
        
        # 如果掌握程度很好，推荐高难度题目或相关知识点
        else:
            # 推荐高难度题目
            hard_questions = db.session.query(
                QuestionKeyword, Question, Assignment
            ).join(
                Question, QuestionKeyword.question_id == Question.id
            ).join(
                Assignment, Question.assignment_id == Assignment.id
            ).filter(
                QuestionKeyword.keyword_id == keyword_id,
                QuestionKeyword.difficulty_level >= 4
            ).limit(3).all()
            
            for qk, question, assignment in hard_questions:
                suggestions.append({
                    'type': 'challenge',
                    'priority': 'low',
                    'resource_id': str(question.id),
                    'title': f'挑战题 - {assignment.title}',
                    'description': f'挑战难度等级{qk.difficulty_level}的高难度题目',
                    'difficulty_level': qk.difficulty_level
                })
            
            # 推荐相关知识点
            related_keywords = db.session.query(
                KeywordRelation, Keyword
            ).join(
                Keyword, KeywordRelation.target_keyword_id == Keyword.id
            ).filter(
                KeywordRelation.source_keyword_id == keyword_id
            ).limit(3).all()
            
            for relation, related_keyword in related_keywords:
                related_mastery = KnowledgePointMastery.query.filter_by(
                    user_id=user_id, keyword_id=related_keyword.id
                ).first()
                
                related_level = related_mastery.mastery_level if related_mastery else 0.0
                
                if related_level < current_level:
                    suggestions.append({
                        'type': 'related_knowledge',
                        'priority': 'medium',
                        'resource_id': str(related_keyword.id),
                        'title': f'相关知识点: {related_keyword.name}',
                        'description': f'学习相关知识点以加深理解',
                        'current_mastery': related_level
                    })
        
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': {
                'keyword_name': keyword.name,
                'current_mastery_level': current_level,
                'suggestions': suggestions,
                'total_suggestions': len(suggestions)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting learning path: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'获取学习路径失败: {str(e)}'
        }), 500


@knowledge_point_bp.route('/mastery/overview', methods=['GET'])
@token_required
def get_mastery_overview():
    """
    获取用户知识点掌握程度概览
    
    Returns:
        掌握程度概览数据
    """
    try:
        user_id = request.user.get('user_id')
        mastery_calculator = MasteryCalculator()
        overview = mastery_calculator.get_mastery_overview(user_id)
        
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': overview
        })
        
    except Exception as e:
        logger.error(f"Error getting mastery overview: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'获取掌握程度概览失败: {str(e)}'
        }), 500


@knowledge_point_bp.route('/document-progress', methods=['POST'])
@token_required
def update_document_progress():
    """
    更新文档学习进度
    
    Request Body:
        {
            "document_id": "document_id",
            "progress": 0.5,  // 0-1
            "last_position": 1000,  // 最后阅读位置
            "reading_time": 300,  // 本次阅读时长(秒)
            "completed": false
        }
    
    Returns:
        更新结果
    """
    try:
        user_id = request.user.get('user_id')
        data = request.get_json()
        
        if not data or 'document_id' not in data:
            return jsonify({
                'code': 400,
                'msg': '缺少必要参数: document_id'
            }), 400
        
        document_id = data['document_id']
        progress = max(0.0, min(1.0, data.get('progress', 0.0)))
        last_position = data.get('last_position', 0)
        reading_time_delta = data.get('reading_time', 0)
        completed = data.get('completed', progress >= 1.0)
        
        # 查找或创建进度记录
        progress_record = DocumentProgress.query.filter_by(
            user_id=user_id, document_id=document_id
        ).first()
        
        if progress_record:
            progress_record.progress = progress
            progress_record.last_position = last_position
            progress_record.completed = completed
            progress_record.reading_time += reading_time_delta
            progress_record.last_read_time = datetime.now()
            progress_record.updated_at = datetime.now()
        else:
            progress_record = DocumentProgress(
                user_id=user_id,
                document_id=document_id,
                progress=progress,
                last_position=last_position,
                completed=completed,
                reading_time=reading_time_delta,
                last_read_time=datetime.now()
            )
            db.session.add(progress_record)
        
        db.session.commit()
        
        # 触发相关知识点掌握程度重新计算
        document_keywords = DocumentKeyword.query.filter_by(document_id=document_id).all()
        for dk in document_keywords:
            try:
                MasteryCalculator().calculate_mastery_level(
                    user_id, dk.keyword_id, force_recalculate=True
                )
            except Exception as e:
                logger.warning(f"Failed to recalculate mastery for keyword {dk.keyword_id}: {str(e)}")
        
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': progress_record.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating document progress: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'更新文档进度失败: {str(e)}'
        }), 500


@knowledge_point_bp.route('/document-progress/<user_id>', methods=['GET'])
@token_required
def get_user_document_progress(user_id):
    """
    获取用户文档学习进度
    
    Args:
        user_id: 用户ID
        
    Returns:
        用户文档学习进度列表
    """
    try:
        # 检查权限（只能查看自己的进度，或管理员/教师查看学生进度）
        current_user_id = request.user.get('user_id')
        user_role = request.user.get('role')
        
        if current_user_id != user_id and user_role not in ['admin', 'teacher']:
            return jsonify({
                'code': 403,
                'msg': '无权限查看该用户的学习进度'
            }), 403
        
        # 获取文档进度记录
        progress_records = db.session.query(
            DocumentProgress, Document, Course
        ).join(
            Document, DocumentProgress.document_id == Document.id
        ).join(
            Course, Document.course_id == Course.id
        ).filter(
            DocumentProgress.user_id == user_id
        ).order_by(desc(DocumentProgress.last_read_time)).all()
        
        progress_list = []
        for progress, document, course in progress_records:
            progress_list.append({
                'id': str(progress.id),
                'document_id': str(document.id),
                'document_title': document.title,
                'document_type': document.file_type,
                'course_id': str(course.id),
                'course_name': course.name,
                'progress': progress.progress,
                'last_position': progress.last_position,
                'completed': progress.completed,
                'reading_time': progress.reading_time,
                'last_read_time': progress.last_read_time.isoformat() if progress.last_read_time else None,
                'created_at': progress.created_at.isoformat() if progress.created_at else None
            })
        
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': {
                'progress_list': progress_list,
                'total': len(progress_list)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting user document progress: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'获取文档学习进度失败: {str(e)}'
        }), 500

@knowledge_point_bp.route('/<keyword_id>/student-mastery/<student_id>', methods=['GET'])
@token_required
def get_student_knowledge_point_mastery(keyword_id, student_id):
    """
    获取特定学生对特定知识点的掌握程度详情
    
    Args:
        keyword_id: 知识点ID
        student_id: 学生ID
        
    Returns:
        掌握程度详细信息，包括具体资源的进度
    """
    try:
        # 检查当前用户是否有权限（应该是教师）
        current_user = request.user
        if current_user.get('role') != 'teacher':
            return jsonify({
                'code': 403,
                'msg': '只有教师可以查看学生的掌握度信息'
            }), 403
        
        force_recalculate = request.args.get('recalculate', 'false').lower() == 'true'
        
        # 获取基本掌握度信息
        mastery_info = MasteryCalculator().calculate_mastery_level(
            student_id, keyword_id, force_recalculate=force_recalculate
        )
        
        # 获取详细的资源进度信息
        from sqlalchemy import and_
        
        # 获取视频进度详情
        video_details = []
        video_keywords = db.session.query(VideoKeyword).filter_by(keyword_id=keyword_id).all()
        for vk in video_keywords:
            video = db.session.query(Video).filter_by(id=vk.video_id).first()
            if video:
                progress = db.session.query(UserVideoProgress).filter_by(
                    user_id=student_id, video_id=vk.video_id
                ).first()
                
                video_details.append({
                    'id': str(video.id),
                    'title': video.title,
                    'duration': video.duration,
                    'progress': progress.progress if progress else 0.0,
                    'completed': progress.completed if progress else False,
                    'last_watched': progress.update_time.isoformat() if progress and progress.update_time else None
                })
        
        # 获取文档进度详情
        document_details = []
        document_keywords = db.session.query(DocumentKeyword).filter_by(keyword_id=keyword_id).all()
        for dk in document_keywords:
            document = db.session.query(Document).filter_by(id=dk.document_id).first()
            if document:
                progress = db.session.query(DocumentProgress).filter_by(
                    user_id=student_id, document_id=dk.document_id
                ).first()
                
                document_details.append({
                    'id': str(document.id),
                    'title': document.title,
                    'file_type': document.file_type,
                    'file_size': document.file_size,
                    'progress': progress.progress if progress else 0.0,
                    'completed': progress.completed if progress else False,
                    'last_read': progress.last_read_time.isoformat() if progress and progress.last_read_time else None
                })
        
        # 获取作业/练习详情
        assignment_details = []
        question_keywords = db.session.query(QuestionKeyword).filter_by(keyword_id=keyword_id).all()
        
        # 按作业分组
        assignment_scores = {}
        for qk in question_keywords:
            question = db.session.query(Question).filter_by(id=qk.question_id).first()
            if question:
                assignment = db.session.query(Assignment).filter_by(id=question.assignment_id).first()
                if assignment:
                    # 获取学生的答题记录
                    answers = db.session.query(StudentAnswer).filter_by(
                        student_id=student_id, question_id=qk.question_id
                    ).all()
                    
                    best_score = 0
                    answered = False
                    if answers:
                        answered = True
                        best_score = max(answer.score for answer in answers)
                    
                    assignment_id = str(assignment.id)
                    if assignment_id not in assignment_scores:
                        assignment_scores[assignment_id] = {
                            'id': assignment_id,
                            'title': assignment.title,
                            'total_questions': 0,
                            'answered_questions': 0,
                            'total_score': 0,
                            'student_score': 0,
                            'completed': False
                        }
                    
                    assignment_scores[assignment_id]['total_questions'] += 1
                    assignment_scores[assignment_id]['total_score'] += question.max_score or 5.0
                    
                    if answered:
                        assignment_scores[assignment_id]['answered_questions'] += 1
                        assignment_scores[assignment_id]['student_score'] += best_score
        
        # 计算每个作业的完成率和得分率
        for assignment_id, assignment_data in assignment_scores.items():
            if assignment_data['total_questions'] > 0:
                assignment_data['completion_rate'] = assignment_data['answered_questions'] / assignment_data['total_questions']
                assignment_data['score_rate'] = assignment_data['student_score'] / assignment_data['total_score'] if assignment_data['total_score'] > 0 else 0
                assignment_data['completed'] = assignment_data['completion_rate'] >= 1.0
        
        assignment_details = list(assignment_scores.values())
        
        # 增强返回的数据
        mastery_info.update({
            'resource_details': {
                'videos': video_details,
                'documents': document_details,
                'assignments': assignment_details
            },
            'summary': {
                'total_videos': len(video_details),
                'completed_videos': len([v for v in video_details if v['completed']]),
                'total_documents': len(document_details),
                'completed_documents': len([d for d in document_details if d['completed']]),
                'total_assignments': len(assignment_details),
                'completed_assignments': len([a for a in assignment_details if a['completed']])
            }
        })
        
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': mastery_info
        })
        
    except Exception as e:
        logger.error(f"Error getting student knowledge point mastery: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'获取学生掌握程度失败: {str(e)}'
        }), 500


@knowledge_point_bp.route('/batch/mastery', methods=['POST'])
@token_required
def batch_calculate_mastery():
    """
    批量计算多个知识点的掌握程度
    
    Body:
        {
            "keyword_ids": ["id1", "id2", ...],  // 可选，如果不提供则计算用户所有相关知识点
            "force_recalculate": false,          // 可选，是否强制重新计算
            "use_extended_cache": true           // 可选，是否使用扩展缓存策略
        }
        
    Returns:
        批量计算结果
    """
    try:
        user_id = request.user.get('user_id')
        data = request.get_json() or {}
        
        keyword_ids = data.get('keyword_ids')
        force_recalculate = data.get('force_recalculate', False)
        use_extended_cache = data.get('use_extended_cache', True)
        
        mastery_calculator = MasteryCalculator()
        results = mastery_calculator.batch_calculate_mastery(
            user_id=user_id,
            keyword_ids=keyword_ids,
            force_recalculate=force_recalculate,
            use_extended_cache=use_extended_cache
        )
        
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': {
                'results': results,
                'total_count': len(results),
                'calculated_count': len([r for r in results.values() if 'calculation_time' in str(r)])
            }
        })
        
    except Exception as e:
        logger.error(f"Error in batch mastery calculation: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'批量计算掌握程度失败: {str(e)}'
        }), 500


@knowledge_point_bp.route('/precompute/course/<course_id>', methods=['POST'])
@token_required
def precompute_course_mastery(course_id):
    """
    为指定课程预计算掌握程度
    用于课程加载时的性能优化
    
    Args:
        course_id: 课程ID
        
    Returns:
        预计算结果
    """
    try:
        user_id = request.user.get('user_id')
        
        mastery_calculator = MasteryCalculator()
        results = mastery_calculator.precompute_mastery_for_course(
            user_id=user_id,
            course_id=course_id
        )
        
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': {
                'results': results,
                'course_id': course_id,
                'keyword_count': len(results)
            }
        })
        
    except Exception as e:
        logger.error(f"Error precomputing course mastery: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'预计算课程掌握程度失败: {str(e)}'
        }), 500


@knowledge_point_bp.route('/cache/stats', methods=['GET'])
@token_required  
def get_cache_statistics():
    """
    获取缓存统计信息
    用于监控和调试缓存性能
    
    Returns:
        缓存统计信息
    """
    try:
        user_id = request.user.get('user_id')
        
        # 查询用户的掌握程度记录统计
        total_records = KnowledgePointMastery.query.filter_by(user_id=user_id).count()
        
        # 查询最近更新的记录
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_records = KnowledgePointMastery.query.filter(
            KnowledgePointMastery.user_id == user_id,
            KnowledgePointMastery.last_updated >= recent_cutoff
        ).count()
        
        # 查询不同时间段的记录分布
        cache_stats = {
            'total_records': total_records,
            'recent_24h': recent_records,
            'cache_distribution': {}
        }
        
        # 统计不同缓存时间段的记录数量
        time_ranges = [
            ('1h', 1), ('6h', 6), ('24h', 24), ('7d', 168), ('older', float('inf'))
        ]
        
        for label, hours in time_ranges:
            if label == 'older':
                cutoff = datetime.now() - timedelta(hours=168)  # 7天前
                count = KnowledgePointMastery.query.filter(
                    KnowledgePointMastery.user_id == user_id,
                    KnowledgePointMastery.last_updated < cutoff
                ).count()
            else:
                cutoff = datetime.now() - timedelta(hours=hours)
                count = KnowledgePointMastery.query.filter(
                    KnowledgePointMastery.user_id == user_id,
                    KnowledgePointMastery.last_updated >= cutoff
                ).count()
            cache_stats['cache_distribution'][label] = count
        
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': cache_stats
        })
        
    except Exception as e:
        logger.error(f"Error getting cache statistics: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'获取缓存统计失败: {str(e)}'
        }), 500


@knowledge_point_bp.route('/<keyword_id>/course-students-mastery', methods=['GET'])
@token_required
def get_course_students_knowledge_point_mastery(keyword_id):
    """
    获取课程中所有学生对特定知识点的掌握程度详情
    
    Args:
        keyword_id: 知识点ID
        
    Query Params:
        course_id: 课程ID，如果提供则只获取该课程的学生
        recalculate: 是否重新计算掌握度，默认为false
        
    Returns:
        所有相关学生的掌握程度详细信息
    """
    try:
        # 检查当前用户是否有权限（应该是教师）
        current_user = request.user
        if current_user.get('role') != 'teacher':
            return jsonify({
                'code': 403,
                'msg': '只有教师可以查看学生的掌握度信息'
            }), 403
        
        course_id = request.args.get('course_id')
        force_recalculate = request.args.get('recalculate', 'false').lower() == 'true'
        
        # 获取课程中的学生
        if course_id:
            # 通过join Users表确保只获取未删除的学生
            student_enrollments = db.session.query(StudentCourseEnrollment).join(
                Users, StudentCourseEnrollment.student_id == Users.id
            ).filter(
                StudentCourseEnrollment.course_id == course_id,
                Users.is_deleted == False,
                Users.role == 'student'
            ).all()
            student_ids = [str(enrollment.student_id) for enrollment in student_enrollments]
        else:
            # 如果没有指定课程，获取当前教师所有课程的学生
            teacher_id = current_user.get('user_id')
            teacher_courses = db.session.query(Course).filter_by(teacher_id=teacher_id).all()
            course_ids = [str(course.id) for course in teacher_courses]
            
            # 通过join Users表确保只获取未删除的学生
            student_enrollments = db.session.query(StudentCourseEnrollment).join(
                Users, StudentCourseEnrollment.student_id == Users.id
            ).filter(
                StudentCourseEnrollment.course_id.in_(course_ids),
                Users.is_deleted == False,
                Users.role == 'student'
            ).all()
            student_ids = [str(enrollment.student_id) for enrollment in student_enrollments]
        
        # 去重学生ID
        student_ids = list(set(student_ids))
        
        if not student_ids:
            return jsonify({
                'code': 200,
                'msg': 'success',
                'data': {
                    'students_mastery': {}
                }
            })
        
        # 批量获取学生信息
        students = db.session.query(Users).filter(Users.id.in_(student_ids), Users.is_deleted == False).all()
        student_info = {str(student.id): {
            'id': str(student.id),
            'name': student.username,
            'email': student.email
        } for student in students}
        
        # 批量获取每个学生的掌握度
        mastery_calculator = MasteryCalculator()
        students_mastery = {}
        resource_details = {}
        
        for student_id in student_ids:
            try:
                # 获取掌握度信息
                mastery_data = mastery_calculator.calculate_mastery_level(
                    student_id, keyword_id, force_recalculate=force_recalculate
                )
                
                # 获取详细的资源进度信息
                from sqlalchemy import and_
                
                # 获取视频进度详情
                video_details = []
                video_keywords = db.session.query(VideoKeyword).filter_by(keyword_id=keyword_id).all()
                for vk in video_keywords:
                    video = db.session.query(Video).filter_by(id=vk.video_id).first()
                    if video:
                        progress = db.session.query(UserVideoProgress).filter_by(
                            user_id=student_id, video_id=vk.video_id
                        ).first()
                        
                        video_details.append({
                            'id': str(video.id),
                            'title': video.title,
                            'duration': video.duration,
                            'progress': progress.progress if progress else 0.0,
                            'completed': progress.completed if progress else False,
                            'last_watched': progress.update_time.isoformat() if progress and progress.update_time else None
                        })
                
                # 获取文档进度详情
                document_details = []
                document_keywords = db.session.query(DocumentKeyword).filter_by(keyword_id=keyword_id).all()
                for dk in document_keywords:
                    document = db.session.query(Document).filter_by(id=dk.document_id).first()
                    if document:
                        progress = db.session.query(DocumentProgress).filter_by(
                            user_id=student_id, document_id=dk.document_id
                        ).first()
                        
                        document_details.append({
                            'id': str(document.id),
                            'title': document.title,
                            'file_type': document.file_type,
                            'file_size': document.file_size,
                            'progress': progress.progress if progress else 0.0,
                            'completed': progress.completed if progress else False,
                            'last_read': progress.last_read_time.isoformat() if progress and progress.last_read_time else None
                        })
                
                # 获取作业/练习详情
                assignment_details = []
                question_keywords = db.session.query(QuestionKeyword).filter_by(keyword_id=keyword_id).all()
                
                # 按作业分组
                assignment_scores = {}
                for qk in question_keywords:
                    question = db.session.query(Question).filter_by(id=qk.question_id).first()
                    if question:
                        assignment = db.session.query(Assignment).filter_by(id=question.assignment_id).first()
                        if assignment:
                            # 获取学生的答题记录
                            answers = db.session.query(StudentAnswer).filter_by(
                                student_id=student_id, question_id=qk.question_id
                            ).all()
                            
                            best_score = 0
                            answered = False
                            if answers:
                                answered = True
                                best_score = max(answer.score for answer in answers)
                            
                            assignment_id = str(assignment.id)
                            if assignment_id not in assignment_scores:
                                assignment_scores[assignment_id] = {
                                    'id': assignment_id,
                                    'title': assignment.title,
                                    'total_questions': 0,
                                    'answered_questions': 0,
                                    'total_score': 0,
                                    'student_score': 0,
                                    'completed': False
                                }
                            
                            assignment_scores[assignment_id]['total_questions'] += 1
                            assignment_scores[assignment_id]['total_score'] += question.max_score or 5.0
                            
                            if answered:
                                assignment_scores[assignment_id]['answered_questions'] += 1
                                assignment_scores[assignment_id]['student_score'] += best_score
                
                # 计算每个作业的完成率和得分率
                for assignment_id, assignment_data in assignment_scores.items():
                    if assignment_data['total_questions'] > 0:
                        assignment_data['completion_rate'] = assignment_data['answered_questions'] / assignment_data['total_questions']
                        assignment_data['score_rate'] = assignment_data['student_score'] / assignment_data['total_score'] if assignment_data['total_score'] > 0 else 0
                        assignment_data['completed'] = assignment_data['completion_rate'] >= 1.0
                
                assignment_details = list(assignment_scores.values())
                
                # 整合数据
                resource_details[student_id] = {
                    'videos': video_details,
                    'documents': document_details,
                    'assignments': assignment_details
                }
                
                # 学生掌握度信息
                student_mastery = {
                    'mastery_level': mastery_data.get('mastery_level', 0) * 100,  # 转换为百分比
                    'material_progress': mastery_data.get('material_progress', 0) * 100,
                    'exercise_score': mastery_data.get('exercise_score', 0) * 100,
                    'summary': {
                        'total_videos': len(video_details),
                        'completed_videos': len([v for v in video_details if v['completed']]),
                        'total_documents': len(document_details),
                        'completed_documents': len([d for d in document_details if d['completed']]),
                        'total_assignments': len(assignment_details),
                        'completed_assignments': len([a for a in assignment_details if a['completed']])
                    }
                }
                
                # 添加学生基本信息
                if student_id in student_info:
                    student_mastery.update(student_info[student_id])
                
                students_mastery[student_id] = student_mastery
                
            except Exception as e:
                logger.warning(f"计算学生 {student_id} 的掌握度失败: {str(e)}")
                continue
        
        return jsonify({
            'code': 200,
            'msg': 'success',
            'data': {
                'students_mastery': students_mastery,
                'resource_details': resource_details,
                'total_students': len(students_mastery)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting course students knowledge point mastery: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': f'获取学生掌握程度失败: {str(e)}'
        }), 500