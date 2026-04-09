#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
个性化推荐服务
基于知识点掌握情况的个性化学习推荐
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import desc, func, and_, or_
from models.models import db, KnowledgePointMastery, Keyword, KeywordRelation, Video, VideoKeyword, Course, UserVideoProgress, Document, DocumentKeyword, Question, QuestionKeyword, StudentAnswer, DocumentProgress, Assignment
from services.llm_service import LLMService
from services.mastery_calculator import MasteryCalculator
from services.redis_service import redis_service
from functools import lru_cache
import hashlib
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PersonalizedRecommendationService:
    """个性化推荐服务"""
    
    def __init__(self):
        self.mastery_calculator = MasteryCalculator()
        self.llm_service = LLMService()
        self._recommendation_cache = {}  # 简单的内存缓存（仅用于推荐理由）
        self.redis = redis_service
        
        # 缓存配置
        self.CACHE_EXPIRE_SECONDS = 3600  # 1小时过期
        self.CACHE_KEY_PREFIX = "ai_recommendations"
        
    def _get_cache_key(self, source_keyword: str, target_keyword: str, mastery_level: float) -> str:
        """生成缓存键"""
        data = f"{source_keyword}_{target_keyword}_{mastery_level:.2f}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def get_personalized_learning_path(self, user_id: str, limit: int = 5, force_refresh: bool = False) -> Dict[str, Any]:
        """
        获取个性化学习路径推荐
        
        Args:
            user_id: 用户ID
            limit: 推荐数量限制
            force_refresh: 是否强制刷新缓存
            
        Returns:
            个性化学习路径推荐结果
        """
        try:
            # 1. 检查缓存（除非强制刷新）
            if not force_refresh:
                cached_data = self._get_cached_recommendations(user_id)
                if cached_data is not None:
                    recommendations = cached_data['value']
                    # 添加缓存信息到结果中
                    recommendations['cache_info'] = {
                        'is_from_cache': True,
                        'created_at': cached_data.get('created_at'),
                        'metadata': cached_data.get('metadata', {})
                    }
                    return recommendations
            
            # 2. 生成新的推荐
            logger.info(f"为用户 {user_id} 生成新的AI推荐")
            
            # 获取用户掌握程度概览
            mastery_overview = self.mastery_calculator.get_mastery_overview(user_id)
            
            # 找到掌握度最高的知识点
            highest_mastery_keywords = self._get_highest_mastery_keywords(user_id, limit=5)
            
            # 构建知识图谱上下文，让AI生成完整推荐
            if highest_mastery_keywords:
                # 获取知识图谱信息
                knowledge_context = self._build_knowledge_context(user_id, highest_mastery_keywords)
                
                # 让AI生成推荐决策
                ai_recommendations = self._generate_ai_recommendations(
                    user_id, knowledge_context, mastery_overview, limit
                )
                
                # 为AI推荐的知识点获取详细资源信息
                recommendations = self._enrich_ai_recommendations(ai_recommendations, user_id)
                
            else:
                # 如果没有掌握度数据，使用兜底策略
                logger.info(f"用户 {user_id} 没有掌握度数据，使用兜底策略")
                recommendations = self._get_fallback_recommendations_with_ai(user_id, limit)
            
            # 3. 构建完整结果
            result = {
                'user_mastery_overview': mastery_overview,
                'highest_mastery_keywords': highest_mastery_keywords,
                'learning_path_recommendations': recommendations[:limit],
                'total_recommendations': len(recommendations),
                'cache_info': {
                    'is_from_cache': False,
                    'created_at': datetime.now().isoformat(),
                    'expires_in_seconds': self.CACHE_EXPIRE_SECONDS
                }
            }
            
            # 4. 缓存结果
            self._cache_recommendations(user_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"获取个性化学习路径失败: {str(e)}")
            raise
    
    def _get_highest_mastery_keywords(self, user_id: str, limit: int = 8) -> List[Dict[str, Any]]:
        """
        获取用户掌握度最高的知识点
        
        Args:
            user_id: 用户ID
            limit: 返回数量限制
            
        Returns:
            掌握度最高的知识点列表
        """
        highest_mastery = db.session.query(
            KnowledgePointMastery.keyword_id,
            KnowledgePointMastery.mastery_level,
            Keyword.name,
            Keyword.category
        ).join(
            Keyword, KnowledgePointMastery.keyword_id == Keyword.id
        ).filter(
            KnowledgePointMastery.user_id == user_id,
            Keyword.category.in_(['main_module', 'core_concept'])  # 限制知识点类别
            #KnowledgePointMastery.mastery_level >= 0.6  # 只考虑掌握度较高的知识点
        ).order_by(
            desc(KnowledgePointMastery.mastery_level)
        ).limit(limit).all()
        
        # 兜底：如果核心类别没有掌握度记录，获取用户的任意掌握度记录
        if not highest_mastery:
            highest_mastery = db.session.query(
                KnowledgePointMastery.keyword_id,
                KnowledgePointMastery.mastery_level,
                Keyword.name,
                Keyword.category
            ).join(
                Keyword, KnowledgePointMastery.keyword_id == Keyword.id
            ).filter(
                KnowledgePointMastery.user_id == user_id
            ).order_by(
                desc(KnowledgePointMastery.mastery_level)
            ).limit(limit).all()
        
        return [{
            'keyword_id': str(mastery.keyword_id),
            'keyword_name': mastery.name,
            'category': mastery.category,
            'mastery_level': mastery.mastery_level
        } for mastery in highest_mastery]
    
    def _get_next_learning_keywords(self, keyword_id: str, user_id: str) -> List[Dict[str, Any]]:
        """
        基于当前知识点，获取下一步应该学习的知识点
        
        Args:
            keyword_id: 当前知识点ID
            user_id: 用户ID
            
        Returns:
            下一步学习的知识点列表
        """
        # 1. 查找当前知识点的后续知识点（当前知识点是前置条件的知识点）
        next_keywords_query = db.session.query(
            KeywordRelation.target_keyword_id,
            Keyword.name,
            Keyword.category,
            KnowledgePointMastery.mastery_level
        ).join(
            Keyword, KeywordRelation.target_keyword_id == Keyword.id
        ).outerjoin(
            KnowledgePointMastery,
            and_(
                KnowledgePointMastery.keyword_id == Keyword.id,
                KnowledgePointMastery.user_id == user_id
            )
        ).filter(
            KeywordRelation.source_keyword_id == keyword_id,
            KeywordRelation.relation_type.in_(['prerequisite', 'related', 'extends'])
        ).order_by(
            func.coalesce(KnowledgePointMastery.mastery_level, 0.0)  # 优先推荐掌握度较低的
        ).limit(5).all()
        
        next_keywords = []
        for relation in next_keywords_query:
            next_keywords.append({
                'id': str(relation.target_keyword_id),
                'name': relation.name,
                'category': relation.category,
                'current_mastery': relation.mastery_level or 0.0
            })
        
        # 2. 如果没有找到直接的后续知识点，查找相关的同级知识点
        if not next_keywords:
            related_keywords_query = db.session.query(
                Keyword.id,
                Keyword.name,
                Keyword.category,
                KnowledgePointMastery.mastery_level
            ).outerjoin(
                KnowledgePointMastery,
                and_(
                    KnowledgePointMastery.keyword_id == Keyword.id,
                    KnowledgePointMastery.user_id == user_id
                )
            ).join(
                KeywordRelation,
                or_(
                    and_(
                        KeywordRelation.source_keyword_id == Keyword.id,
                        KeywordRelation.target_keyword_id == keyword_id
                    ),
                    and_(
                        KeywordRelation.target_keyword_id == Keyword.id,
                        KeywordRelation.source_keyword_id == keyword_id
                    )
                )
            ).filter(
                Keyword.id != keyword_id
            ).order_by(
                func.coalesce(KnowledgePointMastery.mastery_level, 0.0)
            ).limit(3).all()
            
            for keyword in related_keywords_query:
                next_keywords.append({
                    'id': str(keyword.id),
                    'name': keyword.name,
                    'category': keyword.category,
                    'current_mastery': keyword.mastery_level or 0.0
                })
        
        return next_keywords
    
    def _get_fallback_recommendations(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取兜底推荐 - 当用户没有足够的学习记录时使用
        
        Args:
            user_id: 用户ID
            limit: 推荐数量限制
            
        Returns:
            兜底推荐的知识点列表
        """
        try:
            # 1. 获取用户已经有记录的知识点，避免重复推荐
            existing_keywords = db.session.query(KnowledgePointMastery.keyword_id).filter_by(
                user_id=user_id
            ).subquery()
            
            # 2. 优先推荐基础类知识点
            basic_keywords = db.session.query(
                Keyword.id,
                Keyword.name,
                Keyword.category,
                func.count(VideoKeyword.video_id).label('video_count'),
                func.count(DocumentKeyword.document_id).label('document_count'),
                func.count(QuestionKeyword.question_id).label('question_count')
            ).outerjoin(VideoKeyword).outerjoin(DocumentKeyword).outerjoin(QuestionKeyword).filter(
                ~Keyword.id.in_(existing_keywords),  # 排除已有记录的知识点
                or_(
                    Keyword.category.in_(['基础', '入门', 'foundation', 'basic']),
                    Keyword.name.ilike('%基础%'),
                    Keyword.name.ilike('%入门%'),
                    Keyword.name.ilike('%介绍%')
                )
            ).group_by(Keyword.id, Keyword.name, Keyword.category).having(
                or_(
                    func.count(VideoKeyword.video_id) > 0,
                    func.count(DocumentKeyword.document_id) > 0,
                    func.count(QuestionKeyword.question_id) > 0
                )
            ).order_by(
                desc(func.count(VideoKeyword.video_id) + func.count(DocumentKeyword.document_id) + func.count(QuestionKeyword.question_id))
            ).limit(limit).all()
            
            fallback_list = []
            for keyword in basic_keywords:
                fallback_list.append({
                    'id': str(keyword.id),
                    'name': keyword.name,
                    'category': keyword.category,
                    'current_mastery': 0.0,
                    'resource_count': keyword.video_count + keyword.document_count + keyword.question_count
                })
            
            # 3. 如果基础知识点不够，补充有学习资源的其他知识点
            if len(fallback_list) < limit:
                additional_keywords = db.session.query(
                    Keyword.id,
                    Keyword.name,
                    Keyword.category,
                    func.count(VideoKeyword.video_id).label('video_count'),
                    func.count(DocumentKeyword.document_id).label('document_count'),
                    func.count(QuestionKeyword.question_id).label('question_count')
                ).outerjoin(VideoKeyword).outerjoin(DocumentKeyword).outerjoin(QuestionKeyword).filter(
                    ~Keyword.id.in_(existing_keywords),  # 排除已有记录的知识点
                    ~Keyword.id.in_([k['id'] for k in fallback_list]) if fallback_list else True  # 排除已选择的知识点
                ).group_by(Keyword.id, Keyword.name, Keyword.category).having(
                    or_(
                        func.count(VideoKeyword.video_id) > 0,
                        func.count(DocumentKeyword.document_id) > 0,
                        func.count(QuestionKeyword.question_id) > 0
                    )
                ).order_by(
                    desc(func.count(VideoKeyword.video_id) + func.count(DocumentKeyword.document_id) + func.count(QuestionKeyword.question_id))
                ).limit(limit - len(fallback_list)).all()
                
                for keyword in additional_keywords:
                    fallback_list.append({
                        'id': str(keyword.id),
                        'name': keyword.name,
                        'category': keyword.category,
                        'current_mastery': 0.0,
                        'resource_count': keyword.video_count + keyword.document_count + keyword.question_count
                    })
            
            logger.info(f"为用户 {user_id} 生成了 {len(fallback_list)} 个兜底推荐")
            return fallback_list
            
        except Exception as e:
            logger.error(f"获取兜底推荐失败: {str(e)}")
            # 最后的兜底：随机选择一些知识点
            try:
                random_keywords = db.session.query(
                    Keyword.id,
                    Keyword.name,
                    Keyword.category
                ).limit(limit).all()
                
                return [{
                    'id': str(keyword.id),
                    'name': keyword.name,
                    'category': keyword.category,
                    'current_mastery': 0.0,
                    'resource_count': 0
                } for keyword in random_keywords]
            except:
                return []

    def _get_learning_resources_batch(self, keyword_ids: List[str], user_id: str) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """
        批量获取多个知识点的学习资源
        
        Args:
            keyword_ids: 知识点ID列表
            user_id: 用户ID
            
        Returns:
            按知识点ID分组的学习资源字典
        """
        if not keyword_ids:
            return {}
            
        batch_resources = {}
        
        # 批量获取视频资源
        video_resources = db.session.query(
            VideoKeyword.keyword_id,
            VideoKeyword.video_id,
            Video.title,
            Video.duration,
            Course.name.label('course_name'),
            Course.id.label('course_id'),
            UserVideoProgress.progress
        ).join(
            Video, VideoKeyword.video_id == Video.id
        ).join(
            Course, Video.course_id == Course.id
        ).outerjoin(
            UserVideoProgress,
            and_(
                UserVideoProgress.video_id == Video.id,
                UserVideoProgress.user_id == user_id
            )
        ).filter(
            VideoKeyword.keyword_id.in_(keyword_ids)
        ).limit(50).all()  # 限制总数量
        
        # 批量获取文档资源
        document_resources = db.session.query(
            DocumentKeyword.keyword_id,
            DocumentKeyword.document_id,
            Document.title,
            Document.file_type,  # 修正：使用正确的字段名
            Course.name.label('course_name'),
            Course.id.label('course_id')
        ).join(
            Document, DocumentKeyword.document_id == Document.id
        ).join(
            Course, Document.course_id == Course.id
        ).filter(
            DocumentKeyword.keyword_id.in_(keyword_ids)
        ).limit(50).all()
        
        # 批量获取题目资源
        question_resources = db.session.query(
            QuestionKeyword.keyword_id,
            QuestionKeyword.question_id,
            Question.content,
            Question.difficulty,  # 修正：使用正确的字段名
            StudentAnswer.is_correct,
            StudentAnswer.score
        ).join(
            Question, QuestionKeyword.question_id == Question.id
        ).outerjoin(
            StudentAnswer,
            and_(
                StudentAnswer.question_id == Question.id,
                StudentAnswer.student_id == user_id
            )
        ).filter(
            QuestionKeyword.keyword_id.in_(keyword_ids)
        ).limit(50).all()
        
        # 组织数据
        for keyword_id in keyword_ids:
            batch_resources[keyword_id] = {
                'videos': [],
                'documents': [],
                'questions': []
            }
        
        # 处理视频资源
        for resource in video_resources:
            keyword_id = str(resource.keyword_id)
            if keyword_id in batch_resources:
                batch_resources[keyword_id]['videos'].append({
                    'id': resource.video_id,
                    'title': resource.title,
                    'duration': resource.duration,
                    'course_name': resource.course_name,
                    'course_id': resource.course_id,
                    'progress': resource.progress or 0.0
                })
        
        # 处理文档资源
        for resource in document_resources:
            keyword_id = str(resource.keyword_id)
            if keyword_id in batch_resources:
                batch_resources[keyword_id]['documents'].append({
                    'id': resource.document_id,
                    'title': resource.title,
                    'file_type': resource.file_type,  # 修正：使用正确的字段名
                    'course_name': resource.course_name,
                    'course_id': resource.course_id
                })
        
        # 处理题目资源
        for resource in question_resources:
            keyword_id = str(resource.keyword_id)
            if keyword_id in batch_resources:
                batch_resources[keyword_id]['questions'].append({
                    'id': resource.question_id,
                    'content': resource.content[:200] + '...' if len(resource.content) > 200 else resource.content,
                    'difficulty': resource.difficulty,  # 修正：使用正确的字段名
                    'is_correct': resource.is_correct,
                    'score': resource.score or 0
                })
        
        return batch_resources
    
    def _get_learning_resources(self, keyword_id: str, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取知识点相关的学习资源（视频、文档、题目）
        
        Args:
            keyword_id: 知识点ID
            user_id: 用户ID
            
        Returns:
            学习资源字典
        """
        resources = {
            'videos': [],
            'documents': [],
            'questions': []
        }
        
        # 获取相关视频
        video_resources = db.session.query(
            VideoKeyword.video_id,
            Video.title,
            Video.duration,
            Course.name.label('course_name'),
            Course.id.label('course_id'),
            UserVideoProgress.progress
        ).join(
            Video, VideoKeyword.video_id == Video.id
        ).join(
            Course, Video.course_id == Course.id
        ).outerjoin(
            UserVideoProgress,
            and_(
                UserVideoProgress.video_id == Video.id,
                UserVideoProgress.user_id == user_id
            )
        ).filter(
            VideoKeyword.keyword_id == keyword_id
        ).order_by(
            desc(VideoKeyword.weight)
        ).limit(5).all()
        
        for video in video_resources:
            resources['videos'].append({
                'id': str(video.video_id),
                'title': video.title,
                'duration': video.duration,
                'course_name': video.course_name,
                'course_id': str(video.course_id),
                'progress': video.progress or 0.0
            })
        
        # 获取相关文档
        document_resources = db.session.query(
            DocumentKeyword.document_id,
            Document.title,
            Document.file_url,  # 修正：使用正确的字段名
            Course.name.label('course_name'),
            Course.id.label('course_id'),
            DocumentProgress.progress
        ).join(
            Document, DocumentKeyword.document_id == Document.id
        ).join(
            Course, Document.course_id == Course.id
        ).outerjoin(
            DocumentProgress,
            and_(
                DocumentProgress.document_id == Document.id,
                DocumentProgress.user_id == user_id
            )
        ).filter(
            DocumentKeyword.keyword_id == keyword_id
        ).order_by(
            desc(DocumentKeyword.weight)
        ).limit(3).all()
        
        for doc in document_resources:
            resources['documents'].append({
                'id': str(doc.document_id),
                'title': doc.title,
                'file_url': doc.file_url,  # 修正：使用正确的字段名
                'course_name': doc.course_name,
                'course_id': str(doc.course_id),
                'progress': doc.progress or 0.0
            })
        
        # 获取相关题目
        question_resources = db.session.query(
            QuestionKeyword.question_id,
            Question.content,
            Question.type,
            Assignment.title.label('assignment_title'),
            Assignment.id.label('assignment_id'),
            Question.difficulty,  # 修正：使用正确的字段名
            StudentAnswer.is_correct
        ).join(
            Question, QuestionKeyword.question_id == Question.id
        ).join(
            Assignment, Question.assignment_id == Assignment.id
        ).outerjoin(
            StudentAnswer,
            and_(
                StudentAnswer.question_id == Question.id,
                StudentAnswer.student_id == user_id
            )
        ).filter(
            QuestionKeyword.keyword_id == keyword_id
        ).order_by(
            Question.difficulty  # 修正：使用正确的字段名
        ).limit(5).all()
        
        for question in question_resources:
            resources['questions'].append({
                'id': str(question.question_id),
                'content': question.content[:100] + '...' if len(question.content) > 100 else question.content,
                'type': question.type,
                'assignment_title': question.assignment_title,
                'assignment_id': str(question.assignment_id),
                'difficulty': question.difficulty,  # 修正：使用正确的字段名
                'is_completed': question.is_correct is not None,
                'is_correct': question.is_correct
            })
        
        return resources
    
    def _generate_recommendation_reason(self, source_keyword: str, target_keyword: str, 
                                       mastery_level: float, resources: Dict[str, List]) -> str:
        """
        生成个性化推荐理由（带缓存优化）
        
        Args:
            source_keyword: 源知识点名称
            target_keyword: 目标知识点名称
            mastery_level: 源知识点掌握度
            resources: 可用学习资源
            
        Returns:
            推荐理由
        """
        # 检查缓存
        cache_key = self._get_cache_key(source_keyword, target_keyword, mastery_level)
        if cache_key in self._recommendation_cache:
            return self._recommendation_cache[cache_key]
            
        try:
            # 构建提示词
            prompt = f"""
            基于以下信息，为用户生成个性化的学习推荐理由：
            
            用户当前状态：
            - 已掌握知识点：{source_keyword}（掌握度：{mastery_level:.1%}）
            - 推荐学习知识点：{target_keyword}
            
            可用学习资源：
            - 视频资源：{len(resources.get('videos', []))}个
            - 文档资源：{len(resources.get('documents', []))}个
            - 练习题：{len(resources.get('questions', []))}个
            
            请生成一个简洁、个性化的推荐理由（不超过100字），说明为什么推荐学习这个知识点。
            不要使用Markdown格式，直接返回纯文本。
            """
            
            llm = self.llm_service.create_non_streaming_llm()
            response = llm.invoke(prompt)
            reason = response.content.strip()
            
            # 缓存结果
            self._recommendation_cache[cache_key] = reason
            return reason
            
        except Exception as e:
            logger.error(f"生成推荐理由失败: {str(e)}")
            # 降级策略：返回基于规则的推荐理由
            reason = self._generate_fallback_reason(source_keyword, target_keyword, mastery_level, resources)
            self._recommendation_cache[cache_key] = reason
            return reason
            
    def _generate_fallback_reason(self, source_keyword: str, target_keyword: str, 
                                mastery_level: float, resources: Dict[str, List]) -> str:
        """
        生成降级推荐理由（基于规则）
        """
        resource_count = len(resources.get('videos', [])) + len(resources.get('documents', [])) + len(resources.get('questions', []))
        
        if mastery_level >= 0.8:
            return f"您已熟练掌握{source_keyword}，现在是学习{target_keyword}的最佳时机，我们为您准备了{resource_count}个优质学习资源。"
        elif mastery_level >= 0.6:
            return f"基于您对{source_keyword}的良好掌握，建议进一步学习{target_keyword}来拓展知识体系。"
        else:
            return f"在{source_keyword}基础上学习{target_keyword}，将帮助您建立更完整的知识结构。"
    
    def _calculate_priority_score(self, source_mastery: float, target_mastery: float) -> float:
        """
        计算推荐优先级分数
        
        Args:
            source_mastery: 源知识点掌握程度
            target_mastery: 目标知识点掌握程度
            
        Returns:
            优先级分数（越高越优先）
        """
        # 源知识点掌握程度越高，目标知识点掌握程度越低，优先级越高
        return source_mastery * (1 - target_mastery)
    
    def get_knowledge_point_recommendations(self, user_id: str, keyword_id: str) -> Dict[str, Any]:
        """
        获取特定知识点的个性化推荐
        
        Args:
            user_id: 用户ID
            keyword_id: 知识点ID
            
        Returns:
            知识点推荐结果
        """
        try:
            # 获取知识点信息
            keyword = Keyword.query.get_or_404(keyword_id)
            
            # 获取当前掌握程度
            current_mastery = KnowledgePointMastery.query.filter_by(
                user_id=user_id, keyword_id=keyword_id
            ).first()
            
            mastery_level = current_mastery.mastery_level if current_mastery else 0.0
            
            # 获取下一步学习建议
            next_keywords = self._get_next_learning_keywords(keyword_id, user_id)
            
            recommendations = []
            for next_keyword in next_keywords:
                resources = self._get_learning_resources(next_keyword['id'], user_id)
                reason = self._generate_recommendation_reason(
                    keyword.name, next_keyword['name'], mastery_level, resources
                )
                
                recommendations.append({
                    'keyword': next_keyword,
                    'resources': resources,
                    'recommendation_reason': reason
                })
            
            return {
                'current_keyword': {
                    'id': keyword_id,
                    'name': keyword.name,
                    'category': keyword.category,
                    'mastery_level': mastery_level
                },
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"获取知识点推荐失败: {str(e)}")
            raise

    def _build_knowledge_context(self, user_id: str, highest_mastery_keywords: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        构建知识图谱上下文，为AI推荐提供完整信息
        
        Args:
            user_id: 用户ID
            highest_mastery_keywords: 用户掌握度最高的知识点列表
            
        Returns:
            知识图谱上下文信息
        """
        context = {
            'mastered_keywords': [],
            'available_next_steps': [],
            'learning_resources_summary': {}
        }
        
        # 收集掌握的知识点及其关联信息
        for keyword_info in highest_mastery_keywords:
            keyword_id = keyword_info['keyword_id']
            keyword_name = keyword_info['keyword_name']
            mastery_level = keyword_info['mastery_level']
            
            # 获取关联的知识点
            related_keywords = self._get_all_related_keywords(keyword_id, user_id)
            
            context['mastered_keywords'].append({
                'id': keyword_id,
                'name': keyword_name,
                'category': keyword_info['category'],
                'mastery_level': mastery_level,
                'related_keywords': related_keywords
            })
            
            # 收集可能的下一步学习选项
            next_steps = self._get_detailed_next_keywords(keyword_id, user_id)
            context['available_next_steps'].extend(next_steps)
        
        # 去重并获取学习资源摘要
        unique_next_steps = []
        seen_ids = set()
        for step in context['available_next_steps']:
            if step['id'] not in seen_ids:
                unique_next_steps.append(step)
                seen_ids.add(step['id'])
                
                # 获取资源摘要
                resources_summary = self._get_resources_summary(step['id'])
                context['learning_resources_summary'][step['id']] = resources_summary
        
        context['available_next_steps'] = unique_next_steps
        return context
    
    def _get_all_related_keywords(self, keyword_id: str, user_id: str) -> List[Dict[str, Any]]:
        """
        获取与指定知识点相关的所有知识点（包括前置、后续、相关）
        
        Args:
            keyword_id: 知识点ID
            user_id: 用户ID
            
        Returns:
            相关知识点列表
        """
        # 查询所有相关的知识点（作为源或目标）
        related_query = db.session.query(
            KeywordRelation.source_keyword_id,
            KeywordRelation.target_keyword_id,
            KeywordRelation.relation_type,
            Keyword.id,
            Keyword.name,
            Keyword.category,
            KnowledgePointMastery.mastery_level
        ).join(
            Keyword, 
            or_(
                Keyword.id == KeywordRelation.source_keyword_id,
                Keyword.id == KeywordRelation.target_keyword_id
            )
        ).outerjoin(
            KnowledgePointMastery,
            and_(
                KnowledgePointMastery.keyword_id == Keyword.id,
                KnowledgePointMastery.user_id == user_id
            )
        ).filter(
            or_(
                KeywordRelation.source_keyword_id == keyword_id,
                KeywordRelation.target_keyword_id == keyword_id
            ),
            Keyword.id != keyword_id  # 排除自己
        ).all()
        
        related_keywords = []
        for relation in related_query:
            related_keywords.append({
                'id': str(relation.id),
                'name': relation.name,
                'category': relation.category,
                'relation_type': relation.relation_type,
                'current_mastery': relation.mastery_level or 0.0,
                'is_source': str(relation.source_keyword_id) == str(keyword_id),
                'is_target': str(relation.target_keyword_id) == str(keyword_id)
            })
        
        return related_keywords
    
    def _get_detailed_next_keywords(self, keyword_id: str, user_id: str) -> List[Dict[str, Any]]:
        """
        获取详细的下一步学习知识点信息
        
        Args:
            keyword_id: 当前知识点ID
            user_id: 用户ID
            
        Returns:
            详细的下一步知识点列表
        """
        # 获取后续知识点（当前知识点作为前置条件）
        next_keywords_query = db.session.query(
            KeywordRelation.target_keyword_id,
            KeywordRelation.relation_type,
            Keyword.name,
            Keyword.category,
            Keyword.description,
            KnowledgePointMastery.mastery_level,
            func.count(VideoKeyword.video_id).label('video_count'),
            func.count(DocumentKeyword.document_id).label('document_count'),
            func.count(QuestionKeyword.question_id).label('question_count')
        ).join(
            Keyword, KeywordRelation.target_keyword_id == Keyword.id
        ).outerjoin(
            KnowledgePointMastery,
            and_(
                KnowledgePointMastery.keyword_id == Keyword.id,
                KnowledgePointMastery.user_id == user_id
            )
        ).outerjoin(VideoKeyword, VideoKeyword.keyword_id == Keyword.id).outerjoin(
            DocumentKeyword, DocumentKeyword.keyword_id == Keyword.id
        ).outerjoin(QuestionKeyword, QuestionKeyword.keyword_id == Keyword.id).filter(
            KeywordRelation.source_keyword_id == keyword_id,
            KeywordRelation.relation_type.in_(['prerequisite', 'related', 'contains'])
        ).group_by(
            KeywordRelation.target_keyword_id,
            KeywordRelation.relation_type,
            Keyword.name,
            Keyword.category,
            Keyword.description,
            KnowledgePointMastery.mastery_level
        ).limit(10).all()
        
        next_keywords = []
        for keyword in next_keywords_query:
            next_keywords.append({
                'id': str(keyword.target_keyword_id),
                'name': keyword.name,
                'category': keyword.category,
                'description': keyword.description or '',
                'relation_type': keyword.relation_type,
                'current_mastery': keyword.mastery_level or 0.0,
                'available_resources': {
                    'videos': keyword.video_count,
                    'documents': keyword.document_count,
                    'questions': keyword.question_count
                }
            })
        
        return next_keywords
    
    def _get_resources_summary(self, keyword_id: str) -> Dict[str, int]:
        """
        获取知识点的学习资源数量摘要
        
        Args:
            keyword_id: 知识点ID
            
        Returns:
            资源数量摘要
        """
        # 统计各类资源数量
        video_count = db.session.query(func.count(VideoKeyword.video_id)).filter(
            VideoKeyword.keyword_id == keyword_id
        ).scalar() or 0
        
        document_count = db.session.query(func.count(DocumentKeyword.document_id)).filter(
            DocumentKeyword.keyword_id == keyword_id
        ).scalar() or 0
        
        question_count = db.session.query(func.count(QuestionKeyword.question_id)).filter(
            QuestionKeyword.keyword_id == keyword_id
        ).scalar() or 0
        
        return {
            'videos': video_count,
            'documents': document_count,
            'questions': question_count,
            'total': video_count + document_count + question_count
        }
    
    def _generate_ai_recommendations(self, user_id: str, knowledge_context: Dict[str, Any], 
                                   mastery_overview: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """
        使用AI生成个性化推荐决策
        
        Args:
            user_id: 用户ID
            knowledge_context: 知识图谱上下文
            mastery_overview: 用户掌握度概览
            limit: 推荐数量限制
            
        Returns:
            AI生成的推荐列表
        """
        try:
            # 构建AI提示词
            prompt = self._build_ai_recommendation_prompt(knowledge_context, mastery_overview, limit)
            
            # 调用LLM
            llm = self.llm_service.create_non_streaming_llm()
            response = llm.invoke(prompt)
            
            # 解析AI返回的JSON
            try:
                # 提取JSON内容（处理可能的代码块包装）
                json_content = self._extract_json_from_response(response.content.strip())
                ai_response = json.loads(json_content)
                return ai_response.get('recommendations', [])
            except json.JSONDecodeError as e:
                logger.error(f"AI推荐结果JSON解析失败: {str(e)}")
                logger.error(f"AI返回内容: {response.content}")
                # 降级到基于规则的推荐
                return self._fallback_to_rule_based_recommendations(knowledge_context, limit)
                
        except Exception as e:
            logger.error(f"AI推荐生成失败: {str(e)}")
            # 降级到基于规则的推荐
            return self._fallback_to_rule_based_recommendations(knowledge_context, limit)
    
    def _build_ai_recommendation_prompt(self, knowledge_context: Dict[str, Any], 
                                      mastery_overview: Dict[str, Any], limit: int) -> str:
        """
        构建AI推荐的提示词
        
        Args:
            knowledge_context: 知识图谱上下文
            mastery_overview: 用户掌握度概览
            limit: 推荐数量限制
            
        Returns:
            完整的提示词
        """
        prompt = f"""
        你是一个智能学习路径推荐专家。请基于以下用户学习情况和知识图谱信息，生成个性化的下一步学习推荐。

        ## 用户学习概览
        - 总学习知识点: {mastery_overview.get('total_keywords', 0)}
        - 已掌握知识点: {mastery_overview.get('mastered_keywords', 0)}
        - 平均掌握度: {mastery_overview.get('average_mastery', 0):.1%}

        ## 用户掌握较好的知识点（源知识点）
        """
        
        for keyword in knowledge_context['mastered_keywords']:
            prompt += f"""
        ### {keyword['name']} (ID: {keyword['id']}, 掌握度: {keyword['mastery_level']:.1%})
        - 分类: {keyword['category']}
        - 相关知识点: {len(keyword['related_keywords'])}个
        """
            
        prompt += f"""

        ## 与以上知识点相关联的知识点（等待被推荐的知识点）
        """
        
        for i, option in enumerate(knowledge_context['available_next_steps'][:20], 1):
            resources = knowledge_context['learning_resources_summary'].get(option['id'], {})
            prompt += f"""
        {i}. **{option['name']}** (ID: {option['id']})
           - 分类: {option['category']}
           - 当前掌握度: {option['current_mastery']:.1%}
           - 关系类型: {option['relation_type']}
           - 可用资源: {resources.get('videos', 0)}个视频, {resources.get('documents', 0)}个文档, {resources.get('questions', 0)}道练习
           - 描述: {option.get('description', '暂无描述')[:100]}
        """

        prompt += f"""

        ## 任务要求
        请分析用户的学习情况，从上述选项生成从源知识点到目标知识点的个性化学习推荐。

        ### 选择标准
        1. **学习路径合理性**: 基于已掌握知识点的自然延伸
        2. **掌握度差异**: 优先推荐当前掌握度较低的相关知识点
        3. **资源丰富性**: 考虑可用学习资源的数量和质量
        4. **学习难度梯度**: 确保学习难度适中，循序渐进
        5. **知识体系完整性**: 有助于构建完整的知识体系

        ### 输出格式
        请严格按照以下JSON格式输出，不要添加任何其他文字：

        {{
            "recommendations": [
                {{
                    "source_keyword_id": "用户已经掌握的知识点ID",
                    "source_keyword_name": "用户已经掌握的知识点名称",
                    "recommended_keyword_id": "推荐用户学习的知识点ID",
                    "recommended_keyword_name": "推荐用户学习的知识点名称",
                    "priority_score": 0.85,
                    "recommendation_reason": "简要的推荐理由，说明为什么从原来知识点推荐到这个知识点",
                    "learning_benefits": ["学习这个知识点的具体好处1", "好处2", "好处3"],
                    "suggested_learning_order": 1
                }}
            ]
        }}

        注意：
        - priority_score范围为0-1，越高越优先
        - recommendation_reason应该个性化且具体
        - learning_benefits应该列出3-5个具体好处
        - suggested_learning_order从1开始排序
        - 推荐时，尽量从不同的源知识点出发
        """
        
        return prompt
    
    def _fallback_to_rule_based_recommendations(self, knowledge_context: Dict[str, Any], 
                                              limit: int) -> List[Dict[str, Any]]:
        """
        基于规则的推荐降级策略
        
        Args:
            knowledge_context: 知识图谱上下文
            limit: 推荐数量限制
            
        Returns:
            基于规则的推荐列表
        """
        recommendations = []
        
        # 从可选项中选择最佳推荐
        available_options = knowledge_context['available_next_steps']
        resources_summary = knowledge_context['learning_resources_summary']
        
        # 按优先级排序：掌握度低 + 资源丰富
        def calculate_rule_priority(option):
            resources = resources_summary.get(option['id'], {})
            resource_score = min(resources.get('total', 0) / 10, 1.0)  # 资源丰富度
            mastery_gap = 1 - option['current_mastery']  # 掌握度差距
            return resource_score * 0.4 + mastery_gap * 0.6
        
        sorted_options = sorted(available_options, key=calculate_rule_priority, reverse=True)
        
        for i, option in enumerate(sorted_options[:limit]):
            # 找到最相关的源知识点
            source_keyword = self._find_best_source_keyword(option, knowledge_context['mastered_keywords'])
            
            recommendations.append({
                'recommended_keyword_id': option['id'],
                'recommended_keyword_name': option['name'],
                'source_keyword_id': source_keyword['id'],
                'source_keyword_name': source_keyword['name'],
                'priority_score': calculate_rule_priority(option),
                'recommendation_reason': f"基于您对{source_keyword['name']}的掌握，推荐学习{option['name']}来进一步完善知识体系。",
                'learning_benefits': [
                    f"巩固{source_keyword['name']}相关知识",
                    f"拓展{option['category']}领域理解",
                    "提升整体知识结构完整性"
                ],
                'suggested_learning_order': i + 1
            })
        
        return recommendations
    
    def _find_best_source_keyword(self, target_option: Dict[str, Any], 
                                mastered_keywords: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        为目标知识点找到最佳的源知识点
        
        Args:
            target_option: 目标知识点选项
            mastered_keywords: 已掌握的知识点列表
            
        Returns:
            最佳源知识点
        """
        best_source = mastered_keywords[0] if mastered_keywords else {
            'id': 'system',
            'name': '系统推荐',
            'mastery_level': 0.0
        }
        
        # 寻找掌握度最高且相关的知识点
        for keyword in mastered_keywords:
            # 检查是否有直接关联
            for related in keyword.get('related_keywords', []):
                if related['id'] == target_option['id']:
                    if keyword['mastery_level'] > best_source.get('mastery_level', 0):
                        best_source = keyword
                    break
        
        return best_source

    def _enrich_ai_recommendations(self, ai_recommendations: List[Dict[str, Any]], 
                                 user_id: str) -> List[Dict[str, Any]]:
        """
        为AI推荐结果补充详细的学习资源信息
        
        Args:
            ai_recommendations: AI生成的推荐列表
            user_id: 用户ID
            
        Returns:
            补充了资源信息的推荐列表
        """
        if not ai_recommendations:
            return []
        
        # 提取所有推荐的知识点ID
        recommended_keyword_ids = [rec['recommended_keyword_id'] for rec in ai_recommendations]
        
        # 批量获取学习资源
        batch_resources = self._get_learning_resources_batch(recommended_keyword_ids, user_id)
        
        # 补充推荐信息
        enriched_recommendations = []
        for rec in ai_recommendations:
            keyword_id = rec['recommended_keyword_id']
            resources = batch_resources.get(keyword_id, {'videos': [], 'documents': [], 'questions': []})
            
            enriched_recommendations.append({
                'source_keyword': {
                    'id': rec['source_keyword_id'],
                    'name': rec['source_keyword_name'],
                    'mastery_level': self._get_keyword_mastery_level(rec['source_keyword_id'], user_id)
                },
                'recommended_keyword': {
                    'id': keyword_id,
                    'name': rec['recommended_keyword_name'],
                    'current_mastery': self._get_keyword_mastery_level(keyword_id, user_id)
                },
                'resources': resources,
                'recommendation_reason': rec['recommendation_reason'],
                'learning_benefits': rec.get('learning_benefits', []),
                'priority_score': rec['priority_score'],
                'suggested_learning_order': rec.get('suggested_learning_order', 1)
            })
        
        return enriched_recommendations
    
    def _get_keyword_mastery_level(self, keyword_id: str, user_id: str) -> float:
        """
        获取用户对特定知识点的掌握度
        
        Args:
            keyword_id: 知识点ID
            user_id: 用户ID
            
        Returns:
            掌握度（0.0-1.0）
        """
        if keyword_id in ['system', 'fallback']:
            return 0.0
            
        mastery = KnowledgePointMastery.query.filter_by(
            user_id=user_id, 
            keyword_id=keyword_id
        ).first()
        
        return mastery.mastery_level if mastery else 0.0
    
    def _get_fallback_recommendations_with_ai(self, user_id: str, limit: int) -> List[Dict[str, Any]]:
        """
        使用AI生成兜底推荐（当用户没有掌握度数据时）
        
        Args:
            user_id: 用户ID
            limit: 推荐数量限制
            
        Returns:
            兜底推荐列表
        """
        try:
            # 获取基础知识点
            basic_keywords = self._get_basic_keywords_for_ai(limit * 2)
            
            if not basic_keywords:
                return []
            
            # 构建AI提示词
            prompt = f"""
            用户是新学习者，还没有学习记录。请从以下基础知识点中选择{limit}个最适合新手开始学习的知识点：

            ## 可选基础知识点
            """
            
            for i, keyword in enumerate(basic_keywords, 1):
                prompt += f"""
            {i}. **{keyword['name']}** (ID: {keyword['id']})
               - 分类: {keyword['category']}
               - 可用资源: {keyword['resource_count']}个
               - 描述: {keyword.get('description', '基础知识点')[:100]}
            """
            
            prompt += f"""

            请选择最适合新手的{limit}个知识点，按学习顺序排列。

            输出JSON格式：
            {{
                "recommendations": [
                    {{
                        "recommended_keyword_id": "知识点ID",
                        "recommended_keyword_name": "知识点名称",
                        "priority_score": 0.9,
                        "recommendation_reason": "为什么推荐新手学习这个知识点",
                        "learning_benefits": ["学习好处1", "好处2", "好处3"],
                        "suggested_learning_order": 1
                    }}
                ]
            }}
            """
            
            llm = self.llm_service.create_non_streaming_llm()
            response = llm.invoke(prompt)
            
            try:
                # 提取JSON内容（处理可能的代码块包装）
                json_content = self._extract_json_from_response(response.content.strip())
                ai_response = json.loads(json_content)
                recommendations = ai_response.get('recommendations', [])
                
                # 为推荐补充资源信息
                return self._enrich_fallback_recommendations(recommendations, user_id)
                
            except json.JSONDecodeError as e:
                logger.error(f"AI兜底推荐JSON解析失败: {str(e)}")
                logger.error(f"AI兜底推荐返回内容: {response.content}")
                return self._get_simple_fallback_recommendations(user_id, limit)
                
        except Exception as e:
            logger.error(f"AI兜底推荐失败: {str(e)}")
            return self._get_simple_fallback_recommendations(user_id, limit)
    
    def _get_basic_keywords_for_ai(self, limit: int) -> List[Dict[str, Any]]:
        """
        获取基础知识点用于AI推荐
        
        Args:
            limit: 数量限制
            
        Returns:
            基础知识点列表
        """
        basic_keywords = db.session.query(
            Keyword.id,
            Keyword.name,
            Keyword.category,
            Keyword.description,
            func.count(VideoKeyword.video_id).label('video_count'),
            func.count(DocumentKeyword.document_id).label('document_count'),
            func.count(QuestionKeyword.question_id).label('question_count')
        ).outerjoin(VideoKeyword).outerjoin(DocumentKeyword).outerjoin(QuestionKeyword).filter(
            or_(
                Keyword.category.in_(['基础', '入门', 'foundation', 'basic']),
                Keyword.name.ilike('%基础%'),
                Keyword.name.ilike('%入门%'),
                Keyword.name.ilike('%介绍%')
            )
        ).group_by(
            Keyword.id, Keyword.name, Keyword.category, Keyword.description
        ).having(
            or_(
                func.count(VideoKeyword.video_id) > 0,
                func.count(DocumentKeyword.document_id) > 0,
                func.count(QuestionKeyword.question_id) > 0
            )
        ).order_by(
            desc(func.count(VideoKeyword.video_id) + func.count(DocumentKeyword.document_id) + func.count(QuestionKeyword.question_id))
        ).limit(limit).all()
        
        # 兜底：如果没有基础类别或匹配的知识点，随机选择有资源的知识点
        if len(basic_keywords) < limit:
            existing_ids = [k.id for k in basic_keywords]
            additional_keywords = db.session.query(
                Keyword.id,
                Keyword.name,
                Keyword.category,
                Keyword.description,
                func.count(VideoKeyword.video_id).label('video_count'),
                func.count(DocumentKeyword.document_id).label('document_count'),
                func.count(QuestionKeyword.question_id).label('question_count')
            ).outerjoin(VideoKeyword).outerjoin(DocumentKeyword).outerjoin(QuestionKeyword).filter(
                ~Keyword.id.in_(existing_ids) if existing_ids else True
            ).group_by(
                Keyword.id, Keyword.name, Keyword.category, Keyword.description
            ).having(
                or_(
                    func.count(VideoKeyword.video_id) > 0,
                    func.count(DocumentKeyword.document_id) > 0,
                    func.count(QuestionKeyword.question_id) > 0
                )
            ).order_by(
                desc(func.count(VideoKeyword.video_id) + func.count(DocumentKeyword.document_id) + func.count(QuestionKeyword.question_id))
            ).limit(limit - len(basic_keywords)).all()
            
            basic_keywords.extend(additional_keywords)
        
        return [{
            'id': str(keyword.id),
            'name': keyword.name,
            'category': keyword.category,
            'description': keyword.description or '',
            'resource_count': keyword.video_count + keyword.document_count + keyword.question_count
        } for keyword in basic_keywords]
    
    def _enrich_fallback_recommendations(self, recommendations: List[Dict[str, Any]], 
                                       user_id: str) -> List[Dict[str, Any]]:
        """
        为兜底推荐补充资源信息
        
        Args:
            recommendations: 推荐列表
            user_id: 用户ID
            
        Returns:
            补充了资源信息的推荐列表
        """
        if not recommendations:
            return []
        
        # 提取知识点ID
        keyword_ids = [rec['recommended_keyword_id'] for rec in recommendations]
        batch_resources = self._get_learning_resources_batch(keyword_ids, user_id)
        
        enriched = []
        for rec in recommendations:
            keyword_id = rec['recommended_keyword_id']
            resources = batch_resources.get(keyword_id, {'videos': [], 'documents': [], 'questions': []})
            
            enriched.append({
                'source_keyword': {
                    'id': 'new_learner',
                    'name': '新学习者',
                    'mastery_level': 0.0
                },
                'recommended_keyword': {
                    'id': keyword_id,
                    'name': rec['recommended_keyword_name'],
                    'current_mastery': 0.0
                },
                'resources': resources,
                'recommendation_reason': rec['recommendation_reason'],
                'learning_benefits': rec.get('learning_benefits', []),
                'priority_score': rec['priority_score'],
                'suggested_learning_order': rec.get('suggested_learning_order', 1)
            })
        
        return enriched
    
    def _get_simple_fallback_recommendations(self, user_id: str, limit: int) -> List[Dict[str, Any]]:
        """
        简单的兜底推荐策略
        
        Args:
            user_id: 用户ID
            limit: 推荐数量限制
            
        Returns:
            简单推荐列表
        """
        # 直接获取基础知识点和资源
        fallback_keywords = self._get_fallback_recommendations(user_id, limit)
        keyword_ids = [k['id'] for k in fallback_keywords]
        batch_resources = self._get_learning_resources_batch(keyword_ids, user_id)
        
        recommendations = []
        for i, keyword in enumerate(fallback_keywords):
            keyword_id = keyword['id']
            resources = batch_resources.get(keyword_id, {'videos': [], 'documents': [], 'questions': []})
            
            recommendations.append({
                'source_keyword': {
                    'id': 'system',
                    'name': '系统推荐',
                    'mastery_level': 0.0
                },
                'recommended_keyword': {
                    'id': keyword_id,
                    'name': keyword['name'],
                    'current_mastery': 0.0
                },
                'resources': resources,
                'recommendation_reason': f"推荐学习{keyword['name']}，这是一个重要的基础知识点。",
                'learning_benefits': ["建立基础知识体系", "为后续学习做准备", "掌握核心概念"],
                'priority_score': 0.5,
                'suggested_learning_order': i + 1
            })
        
        return recommendations

    def _extract_json_from_response(self, response_text: str) -> str:
        """
        从AI响应中提取JSON内容
        
        Args:
            response_text: AI的原始响应文本
            
        Returns:
            提取的JSON字符串
        """
        import re
        
        # 尝试从代码块中提取JSON
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()
        
        # 尝试从一般代码块中提取JSON
        code_match = re.search(r'```\s*(.*?)\s*```', response_text, re.DOTALL)
        if code_match:
            potential_json = code_match.group(1).strip()
            # 简单验证是否看起来像JSON
            if potential_json.startswith('{') and potential_json.endswith('}'):
                return potential_json
        
        # 尝试直接查找JSON对象
        json_object_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_object_match:
            return json_object_match.group(0)
        
        # 如果都没找到，返回原始文本
        return response_text

    def _get_user_recommendations_cache_key(self, user_id: str) -> str:
        """生成用户推荐的缓存键"""
        return f"{self.CACHE_KEY_PREFIX}:user:{user_id}"
    
    def _get_cached_recommendations(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        获取用户的缓存推荐
        
        Args:
            user_id: 用户ID
            
        Returns:
            缓存的推荐结果，包含创建时间等元数据
        """
        try:
            cache_key = self._get_user_recommendations_cache_key(user_id)
            cached_data = self.redis.get_with_metadata(cache_key)
            
            if cached_data is not None:
                logger.info(f"用户 {user_id} 命中推荐缓存")
                return cached_data
            
            return None
        except Exception as e:
            logger.error(f"获取缓存推荐失败 {user_id}: {str(e)}")
            return None
    
    def _cache_recommendations(self, user_id: str, recommendations: Dict[str, Any]) -> bool:
        """
        缓存用户推荐结果
        
        Args:
            user_id: 用户ID
            recommendations: 推荐结果
            
        Returns:
            是否缓存成功
        """
        try:
            cache_key = self._get_user_recommendations_cache_key(user_id)
            
            # 添加缓存元数据
            metadata = {
                'user_id': user_id,
                'total_recommendations': len(recommendations.get('learning_path_recommendations', [])),
                'cache_version': '1.0'
            }
            
            success = self.redis.set_with_metadata(
                cache_key, 
                recommendations, 
                self.CACHE_EXPIRE_SECONDS,
                metadata
            )
            
            if success:
                logger.info(f"用户 {user_id} 推荐结果已缓存，过期时间: {self.CACHE_EXPIRE_SECONDS}秒")
            else:
                logger.warning(f"用户 {user_id} 推荐结果缓存失败")
            
            return success
        except Exception as e:
            logger.error(f"缓存推荐失败 {user_id}: {str(e)}")
            return False
    
    def _invalidate_user_cache(self, user_id: str) -> bool:
        """
        清除用户的推荐缓存
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否清除成功
        """
        try:
            cache_key = self._get_user_recommendations_cache_key(user_id)
            success = self.redis.delete(cache_key)
            
            if success:
                logger.info(f"用户 {user_id} 推荐缓存已清除")
            
            return success
        except Exception as e:
            logger.error(f"清除用户缓存失败 {user_id}: {str(e)}")
            return False
    
    def get_cache_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        获取用户缓存信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            缓存信息字典
        """
        try:
            cache_key = self._get_user_recommendations_cache_key(user_id)
            
            if not self.redis.exists(cache_key):
                return None
            
            # 获取缓存元数据
            cached_data = self.redis.get_with_metadata(cache_key)
            if cached_data is None:
                return None
            
            # 获取TTL
            ttl = self.redis.ttl(cache_key)
            
            return {
                'is_cached': True,
                'created_at': cached_data.get('created_at'),
                'expires_in_seconds': ttl if ttl > 0 else 0,
                'metadata': cached_data.get('metadata', {})
            }
        except Exception as e:
            logger.error(f"获取缓存信息失败 {user_id}: {str(e)}")
            return None
    
    def invalidate_user_recommendations_on_progress_update(self, user_id: str) -> bool:
        """
        当用户学习进度更新时，清除推荐缓存
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否清除成功
        """
        try:
            logger.info(f"用户 {user_id} 学习进度更新，清除推荐缓存")
            return self._invalidate_user_cache(user_id)
        except Exception as e:
            logger.error(f"用户进度更新时清除缓存失败 {user_id}: {str(e)}")
            return False
    
    def refresh_user_recommendations(self, user_id: str, limit: int = 10) -> Dict[str, Any]:
        """
        强制刷新用户推荐
        
        Args:
            user_id: 用户ID
            limit: 推荐数量限制
            
        Returns:
            新的推荐结果
        """
        logger.info(f"强制刷新用户 {user_id} 的推荐")
        return self.get_personalized_learning_path(user_id, limit, force_refresh=True)
    
    def get_all_cached_users(self) -> List[str]:
        """
        获取所有有缓存的用户ID列表
        
        Returns:
            用户ID列表
        """
        try:
            pattern = f"{self.CACHE_KEY_PREFIX}:user:*"
            cache_keys = self.redis.keys(pattern)
            
            # 提取用户ID
            user_ids = []
            for key in cache_keys:
                # 格式: ai_recommendations:user:user_id
                parts = key.split(':')
                if len(parts) >= 3:
                    user_ids.append(parts[2])
            
            return user_ids
        except Exception as e:
            logger.error(f"获取缓存用户列表失败: {str(e)}")
            return []
    
    def cleanup_expired_cache(self) -> int:
        """
        清理过期的缓存（主要用于内存缓存降级情况）
        
        Returns:
            清理的缓存数量
        """
        try:
            pattern = f"{self.CACHE_KEY_PREFIX}:user:*"
            cache_keys = self.redis.keys(pattern)
            
            cleaned_count = 0
            for key in cache_keys:
                ttl = self.redis.ttl(key)
                if ttl == -2:  # 已过期或不存在
                    cleaned_count += 1
            
            logger.info(f"清理过期缓存: {cleaned_count} 个")
            return cleaned_count
        except Exception as e:
            logger.error(f"清理过期缓存失败: {str(e)}")
            return 0

# 全局服务实例
personalized_recommendation_service = PersonalizedRecommendationService()