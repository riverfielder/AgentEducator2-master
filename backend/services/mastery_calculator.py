#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识点掌握程度计算服务
实现基于多维度数据的知识点掌握程度算法
合并了改进版的图遍历算法和原版的完整功能
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from models.models import (
    db, KnowledgePointMastery, Keyword, KeywordRelation, Video, VideoKeyword, 
    Document, DocumentKeyword, Question, QuestionKeyword, StudentAnswer, 
    DocumentProgress, UserVideoProgress, Course, Users
)
import logging
import json
import hashlib
from collections import deque, defaultdict
from .redis_service import redis_service

logger = logging.getLogger(__name__)

class MasteryCalculator:
    """知识点掌握程度计算器（合并改进版算法）"""
    
    # 算法权重配置
    MATERIAL_WEIGHT = 0.75  # 教学材料权重
    EXERCISE_WEIGHT = 0.15  # 练习表现权重
    SUB_KNOWLEDGE_WEIGHT = 0.1  # 子知识点权重
    
    # 难度系数配置
    DIFFICULTY_COEFFICIENTS = {
        1: 1.0,   # 简单
        2: 1.2,   # 较易
        3: 1.5,   # 中等
        4: 2.0,   # 较难
        5: 2.5    # 困难
    }
    
    # 缓存策略配置
    CACHE_CONFIG = {
        'default_cache_hours': 6,      # 默认缓存6小时
        'active_learning_hours': 2,    # 活跃学习期间缓存2小时
        'high_mastery_hours': 24,      # 高掌握度知识点缓存24小时
        'low_activity_hours': 48,      # 低活跃度知识点缓存48小时
        'batch_cache_hours': 12,       # 批量计算时的缓存时间
        'min_cache_minutes': 30,       # 最小缓存时间30分钟
    }
    
    # Redis缓存配置
    REDIS_CACHE_CONFIG = {
        'mastery_key_prefix': 'mastery:',           # 单个掌握度缓存前缀
        'batch_key_prefix': 'batch_mastery:',      # 批量掌握度缓存前缀
        'course_key_prefix': 'course_mastery:',    # 课程掌握度缓存前缀
        'dependency_graph_key': 'dependency_graph', # 依赖图缓存键
        'default_expire': 3600 * 6,               # 默认过期时间6小时
        'batch_expire': 3600 * 12,                # 批量计算过期时间12小时
        'dependency_expire': 3600 * 24,           # 依赖图过期时间24小时
        'high_mastery_expire': 3600 * 24,         # 高掌握度过期时间24小时
        'low_activity_expire': 3600 * 48,         # 低活跃度过期时间48小时
    }
    
    # 递归深度限制
    MAX_RECURSION_DEPTH = 10
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._calculation_cache = {}  # 计算缓存
        self._visited_nodes = set()   # 访问过的节点，防止循环
        self.redis = redis_service    # Redis服务实例
    
    def _generate_mastery_cache_key(self, user_id: str, keyword_id: str) -> str:
        """生成单个掌握度的缓存键"""
        return f"{self.REDIS_CACHE_CONFIG['mastery_key_prefix']}{user_id}:{keyword_id}"
    
    def _generate_batch_cache_key(self, user_id: str, keyword_ids: List[str]) -> str:
        """生成批量掌握度的缓存键"""
        # 对知识点ID列表进行排序和哈希，确保相同的知识点集合有相同的缓存键
        sorted_ids = sorted(keyword_ids)
        ids_hash = hashlib.md5('|'.join(sorted_ids).encode()).hexdigest()[:8]
        return f"{self.REDIS_CACHE_CONFIG['batch_key_prefix']}{user_id}:{ids_hash}"
    
    def _generate_course_cache_key(self, user_id: str, course_id: str) -> str:
        """生成课程掌握度的缓存键"""
        return f"{self.REDIS_CACHE_CONFIG['course_key_prefix']}{user_id}:{course_id}"
    
    def _get_redis_mastery_cache(self, user_id: str, keyword_id: str) -> Optional[Dict]:
        """从Redis获取单个掌握度缓存"""
        try:
            cache_key = self._generate_mastery_cache_key(user_id, keyword_id)
            cached_data = self.redis.get_with_metadata(cache_key)
            if cached_data:
                print(f"Redis cache hit for mastery: {user_id}:{keyword_id}")
                return cached_data['value']
            return None
        except Exception as e:
            self.logger.warning(f"Error getting Redis mastery cache: {e}")
            return None
    
    def _set_redis_mastery_cache(self, user_id: str, keyword_id: str, mastery_data: Dict, 
                                expire_seconds: Optional[int] = None) -> bool:
        """设置单个掌握度的Redis缓存"""
        try:
            cache_key = self._generate_mastery_cache_key(user_id, keyword_id)
            expire_time = expire_seconds or self.REDIS_CACHE_CONFIG['default_expire']
            
            # 根据掌握度动态调整过期时间
            mastery_level = mastery_data.get('mastery_level', 0.0)
            if mastery_level >= 0.85:
                expire_time = self.REDIS_CACHE_CONFIG['high_mastery_expire']
            
            metadata = {
                'user_id': user_id,
                'keyword_id': keyword_id,
                'mastery_level': mastery_level,
                'cache_type': 'single_mastery'
            }
            
            success = self.redis.set_with_metadata(cache_key, mastery_data, expire_time, metadata)
            if success:
                print(f"Redis cache set for mastery: {user_id}:{keyword_id}, expire: {expire_time}s")
            return success
        except Exception as e:
            self.logger.warning(f"Error setting Redis mastery cache: {e}")
            return False
    
    def _get_redis_batch_cache(self, user_id: str, keyword_ids: List[str]) -> Optional[Dict[str, Dict]]:
        """从Redis获取批量掌握度缓存"""
        try:
            cache_key = self._generate_batch_cache_key(user_id, keyword_ids)
            cached_data = self.redis.get_with_metadata(cache_key)
            if cached_data:
                print(f"Redis batch cache hit for user: {user_id}, keywords: {len(keyword_ids)}")
                return cached_data['value']
            return None
        except Exception as e:
            self.logger.warning(f"Error getting Redis batch cache: {e}")
            return None
    
    def _set_redis_batch_cache(self, user_id: str, keyword_ids: List[str], 
                              batch_data: Dict[str, Dict]) -> bool:
        """设置批量掌握度的Redis缓存"""
        try:
            cache_key = self._generate_batch_cache_key(user_id, keyword_ids)
            expire_time = self.REDIS_CACHE_CONFIG['batch_expire']
            
            metadata = {
                'user_id': user_id,
                'keyword_count': len(keyword_ids),
                'cache_type': 'batch_mastery'
            }
            
            success = self.redis.set_with_metadata(cache_key, batch_data, expire_time, metadata)
            if success:
                print(f"Redis batch cache set for user: {user_id}, keywords: {len(keyword_ids)}")
            return success
        except Exception as e:
            self.logger.warning(f"Error setting Redis batch cache: {e}")
            return False
    
    def _get_redis_dependency_graph(self) -> Optional[Dict[str, List[str]]]:
        """从Redis获取依赖图缓存"""
        try:
            cache_key = self.REDIS_CACHE_CONFIG['dependency_graph_key']
            cached_data = self.redis.get_with_metadata(cache_key)
            if cached_data:
                print("Redis dependency graph cache hit")
                return cached_data['value']
            return None
        except Exception as e:
            self.logger.warning(f"Error getting Redis dependency graph cache: {e}")
            return None
    
    def _set_redis_dependency_graph(self, dependency_graph: Dict[str, List[str]]) -> bool:
        """设置依赖图的Redis缓存"""
        try:
            cache_key = self.REDIS_CACHE_CONFIG['dependency_graph_key']
            expire_time = self.REDIS_CACHE_CONFIG['dependency_expire']
            
            metadata = {
                'graph_size': len(dependency_graph),
                'cache_type': 'dependency_graph'
            }
            
            success = self.redis.set_with_metadata(cache_key, dependency_graph, expire_time, metadata)
            if success:
                print(f"Redis dependency graph cache set, size: {len(dependency_graph)}")
            return success
        except Exception as e:
            self.logger.warning(f"Error setting Redis dependency graph cache: {e}")
            return False
    
    def _invalidate_user_mastery_cache(self, user_id: str, keyword_id: str = None) -> int:
        """清除用户的掌握度缓存"""
        try:
            if keyword_id:
                # 清除特定知识点的缓存
                cache_key = self._generate_mastery_cache_key(user_id, keyword_id)
                success = self.redis.delete(cache_key)
                return 1 if success else 0
            else:
                # 清除用户所有掌握度相关缓存
                patterns = [
                    f"{self.REDIS_CACHE_CONFIG['mastery_key_prefix']}{user_id}:*",
                    f"{self.REDIS_CACHE_CONFIG['batch_key_prefix']}{user_id}:*",
                    f"{self.REDIS_CACHE_CONFIG['course_key_prefix']}{user_id}:*"
                ]
                
                total_deleted = 0
                for pattern in patterns:
                    deleted = self.redis.invalidate_pattern(pattern)
                    total_deleted += deleted
                
                print(f"Invalidated {total_deleted} cache entries for user: {user_id}")
                return total_deleted
        except Exception as e:
            self.logger.warning(f"Error invalidating user mastery cache: {e}")
            return 0
    
    def invalidate_related_cache_on_learning_activity(self, user_id: str, keyword_id: str = None, 
                                                     activity_type: str = None) -> int:
        """当用户学习活动发生时，智能清除相关缓存"""
        try:
            total_deleted = 0
            
            if keyword_id:
                # 清除特定知识点及其相关知识点的缓存
                # 1. 清除当前知识点缓存
                deleted = self._invalidate_user_mastery_cache(user_id, keyword_id)
                total_deleted += deleted
                
                # 2. 清除相关的批量缓存（包含该知识点的批量缓存）
                batch_pattern = f"{self.REDIS_CACHE_CONFIG['batch_key_prefix']}{user_id}:*"
                batch_deleted = self.redis.invalidate_pattern(batch_pattern)
                total_deleted += batch_deleted
                
                # 3. 如果是重要的学习活动，清除相关知识点的缓存
                if activity_type in ['video_completed', 'exercise_completed', 'document_finished']:
                    # 获取相关知识点（父知识点和子知识点）
                    related_keywords = self._get_related_keywords_for_cache_invalidation(keyword_id)
                    for related_id in related_keywords:
                        deleted = self._invalidate_user_mastery_cache(user_id, related_id)
                        total_deleted += deleted
                
                print(
                    f"Invalidated cache for learning activity: user={user_id}, "
                    f"keyword={keyword_id}, activity={activity_type}, deleted={total_deleted}"
                )
            else:
                # 清除用户所有缓存
                total_deleted = self._invalidate_user_mastery_cache(user_id)
            
            return total_deleted
            
        except Exception as e:
            self.logger.warning(f"Error invalidating cache on learning activity: {e}")
            return 0
    
    def _get_related_keywords_for_cache_invalidation(self, keyword_id: str) -> List[str]:
        """获取需要清除缓存的相关知识点"""
        try:
            related_keywords = set()
            
            # 获取父知识点（当前知识点的掌握度变化可能影响父知识点）
            parent_relations = db.session.query(KeywordRelation).filter_by(
                target_keyword_id=keyword_id
            ).all()
            
            for relation in parent_relations:
                related_keywords.add(relation.source_keyword_id)
            
            # 获取子知识点（父知识点的掌握度变化可能影响子知识点的计算）
            child_relations = db.session.query(KeywordRelation).filter_by(
                source_keyword_id=keyword_id
            ).all()
            
            for relation in child_relations:
                related_keywords.add(relation.target_keyword_id)
            
            return list(related_keywords)
            
        except Exception as e:
            self.logger.warning(f"Error getting related keywords for cache invalidation: {e}")
            return []
    
    def get_cache_statistics(self, user_id: str = None) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            stats = {
                'redis_available': self.redis is not None,
                'cache_config': self.REDIS_CACHE_CONFIG.copy()
            }
            
            if self.redis:
                if user_id:
                    # 获取特定用户的缓存统计
                    patterns = [
                        f"{self.REDIS_CACHE_CONFIG['mastery_key_prefix']}{user_id}:*",
                        f"{self.REDIS_CACHE_CONFIG['batch_key_prefix']}{user_id}:*",
                        f"{self.REDIS_CACHE_CONFIG['course_key_prefix']}{user_id}:*"
                    ]
                    
                    user_cache_count = 0
                    for pattern in patterns:
                        count = self.redis.count_keys(pattern)
                        user_cache_count += count
                    
                    stats['user_cache_entries'] = user_cache_count
                    stats['user_id'] = user_id
                else:
                    # 获取全局缓存统计
                    total_mastery_cache = self.redis.count_keys(f"{self.REDIS_CACHE_CONFIG['mastery_key_prefix']}*")
                    total_batch_cache = self.redis.count_keys(f"{self.REDIS_CACHE_CONFIG['batch_key_prefix']}*")
                    total_course_cache = self.redis.count_keys(f"{self.REDIS_CACHE_CONFIG['course_key_prefix']}*")
                    dependency_graph_exists = self.redis.exists(self.REDIS_CACHE_CONFIG['dependency_graph_key'])
                    
                    stats.update({
                        'total_mastery_cache': total_mastery_cache,
                        'total_batch_cache': total_batch_cache,
                        'total_course_cache': total_course_cache,
                        'dependency_graph_cached': dependency_graph_exists,
                        'total_cache_entries': total_mastery_cache + total_batch_cache + total_course_cache
                    })
            
            return stats
            
        except Exception as e:
            self.logger.warning(f"Error getting cache statistics: {e}")
            return {'error': str(e), 'redis_available': False}
    
    def calculate_mastery_level(self, user_id: str, keyword_id: str, 
                               force_recalculate: bool = False) -> Dict:
        """
        计算用户对特定知识点的掌握程度（使用图遍历算法，集成Redis缓存）
        
        Args:
            user_id: 用户ID
            keyword_id: 知识点ID
            force_recalculate: 是否强制重新计算
            
        Returns:
            包含掌握程度详情的字典
        """
        try:
            # 检查Redis缓存
            if not force_recalculate:
                # 首先检查Redis缓存
                redis_cached = self._get_redis_mastery_cache(user_id, keyword_id)
                if redis_cached:
                    print(f"Redis cache hit for user {user_id}, keyword {keyword_id}")
                    return redis_cached
            
            # 清理缓存和访问记录
            self._calculation_cache.clear()
            self._visited_nodes.clear()
            
            # 使用现有的数据库会话，避免事务冲突
            mastery_data = self._calculate_mastery_with_graph_traversal(
                user_id, keyword_id, force_recalculate, db.session
            )
            
            # 更新Redis缓存
            if mastery_data and 'error' not in mastery_data:
                self._set_redis_mastery_cache(user_id, keyword_id, mastery_data)
            
            return mastery_data
            
        except Exception as e:
            self.logger.error(f"Error calculating mastery for user {user_id}, keyword {keyword_id}: {e}")
            return {
                'mastery_level': 0.0,
                'confidence': 0.0,
                'last_updated': datetime.now(),
                'error': str(e)
            }
                
    def _calculate_mastery_with_graph_traversal(self, user_id: str, keyword_id: str, 
                                              force_recalculate: bool, session) -> Dict:
        """
        使用图遍历算法计算掌握程度，避免递归深度问题
        """
        # 构建知识点依赖图
        dependency_graph = self._build_dependency_graph(session)
        
        # 使用拓扑排序计算掌握程度
        mastery_results = self._calculate_mastery_topologically(
            user_id, keyword_id, dependency_graph, force_recalculate, session
        )
        
        return mastery_results.get(keyword_id, {
            'mastery_level': 0.0,
            'material_progress': 0.0,
            'exercise_score': 0.0,
            'sub_knowledge_contribution': 0.0,
            'calculation_details': {}
        })
    
    def _build_dependency_graph(self, session) -> Dict[str, List[str]]:
        """
        构建知识点依赖图
        
        Returns:
            依赖图字典 {parent_id: [child_id1, child_id2, ...]}
        """
        graph = defaultdict(list)
        
        # 查询所有知识点关系
        relations = session.query(KeywordRelation).all()
        
        for relation in relations:
            graph[relation.source_keyword_id].append(relation.target_keyword_id)
        
        return dict(graph)
    
    def _calculate_mastery_topologically(self, user_id: str, target_keyword_id: str,
                                       dependency_graph: Dict[str, List[str]],
                                       force_recalculate: bool, session) -> Dict[str, Dict]:
        """
        使用拓扑排序算法计算掌握程度
        """
        # 找到所有相关的知识点
        all_keywords = self._find_related_keywords(target_keyword_id, dependency_graph)
        
        # 计算入度
        in_degree = defaultdict(int)
        for parent, children in dependency_graph.items():
            if parent in all_keywords:
                for child in children:
                    if child in all_keywords:
                        in_degree[child] += 1
        
        # 初始化队列（入度为0的节点）
        queue = deque([kw for kw in all_keywords if in_degree[kw] == 0])
        mastery_results = {}
        
        # 拓扑排序处理
        while queue:
            current_keyword = queue.popleft()
            
            # 计算当前知识点的掌握程度
            mastery_info = self._calculate_single_keyword_mastery(
                user_id, current_keyword, mastery_results, force_recalculate, session
            )
            mastery_results[current_keyword] = mastery_info
            
            # 更新依赖此知识点的其他知识点
            for child in dependency_graph.get(current_keyword, []):
                if child in all_keywords:
                    in_degree[child] -= 1
                    if in_degree[child] == 0:
                        queue.append(child)
        
        return mastery_results
    
    def _find_related_keywords(self, target_keyword_id: str, 
                             dependency_graph: Dict[str, List[str]]) -> Set[str]:
        """
        找到与目标知识点相关的所有知识点（包括依赖和被依赖）
        """
        related = set([target_keyword_id])
        queue = deque([target_keyword_id])
        visited = set()
        
        while queue and len(visited) < self.MAX_RECURSION_DEPTH:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            
            # 添加子知识点
            for child in dependency_graph.get(current, []):
                if child not in related:
                    related.add(child)
                    queue.append(child)
            
            # 添加父知识点
            for parent, children in dependency_graph.items():
                if current in children and parent not in related:
                    related.add(parent)
                    queue.append(parent)
        
        return related
    
    def _calculate_single_keyword_mastery(self, user_id: str, keyword_id: str,
                                        existing_results: Dict[str, Dict],
                                        force_recalculate: bool, session) -> Dict:
        """
        计算单个知识点的掌握程度
        """
        try:
            # 检查是否需要重新计算
            existing_mastery = session.query(KnowledgePointMastery).filter_by(
                user_id=user_id, keyword_id=keyword_id
            ).first()
            
            if not force_recalculate:
                if existing_mastery and self._is_calculation_fresh(existing_mastery, user_id, keyword_id, False):
                    print(f"[mastery] use cached for user={user_id}, keyword={keyword_id}, value={existing_mastery.mastery_level}")
                    return existing_mastery.to_dict()
            
            # 计算各维度得分
            material_progress = self._calculate_material_progress(user_id, keyword_id, session)
            exercise_score = self._calculate_exercise_score(user_id, keyword_id, session)
            sub_knowledge_contribution = self._calculate_sub_knowledge_contribution_iterative(
                user_id, keyword_id, existing_results, session
            )
            
            # 动态权重计算 - 只有当某个维度有实际数据时才参与计算
            active_weights = []
            active_scores = []
            
            # 材料进度总是参与计算（即使为0，也表示没有学习）
            active_weights.append(self.MATERIAL_WEIGHT)
            active_scores.append(material_progress)
            
            # 练习得分：只有当知识点有对应的作业题目时才参与计算
            has_exercises = self._has_exercises_for_keyword(keyword_id, session)
            if has_exercises:
                active_weights.append(self.EXERCISE_WEIGHT)
                active_scores.append(exercise_score)
            
            # 子知识点贡献：只有当知识点有子知识点时才参与计算
            has_sub_knowledge = self._has_sub_knowledge_for_keyword(keyword_id, session)
            if has_sub_knowledge:
                active_weights.append(self.SUB_KNOWLEDGE_WEIGHT)
                active_scores.append(sub_knowledge_contribution)
            
            # 重新标准化权重
            if active_weights:
                total_weight = sum(active_weights)
                normalized_weights = [w / total_weight for w in active_weights]
                
                # 计算加权平均掌握程度
                mastery_level = sum(weight * score for weight, score in zip(normalized_weights, active_scores))
            else:
                # 如果没有任何活跃维度，默认使用材料进度
                mastery_level = material_progress
            
            # 确保掌握程度在0-1范围内
            mastery_level = max(0.0, min(1.0, mastery_level))
            
            # 计算详情
            calculation_details = {
                'material_progress': material_progress,
                'exercise_score': exercise_score,
                'sub_knowledge_contribution': sub_knowledge_contribution,
                'has_exercises': has_exercises,
                'has_sub_knowledge': has_sub_knowledge,
                'active_dimensions': len(active_weights),
                'normalized_weights': {
                    'material': normalized_weights[0] if len(normalized_weights) > 0 else 0,
                    'exercise': normalized_weights[1] if len(normalized_weights) > 1 and has_exercises else 0,
                    'sub_knowledge': normalized_weights[-1] if has_sub_knowledge and len(normalized_weights) > (2 if has_exercises else 1) else 0
                },
                'calculation_time': datetime.now().isoformat(),
                'algorithm_version': '2.1_dynamic_weights'
            }
            
            # 查询现有记录
            existing_record = session.query(KnowledgePointMastery).filter_by(
                user_id=user_id,
                keyword_id=keyword_id
            ).first()
            
            if existing_record:
                # 更新现有记录
                existing_record.mastery_level = mastery_level
                existing_record.material_progress = material_progress
                existing_record.exercise_score = exercise_score
                existing_record.sub_knowledge_contribution = sub_knowledge_contribution
                existing_record.calculation_details = json.dumps(calculation_details)
                existing_record.last_updated = datetime.now()
                mastery_record = existing_record
            else:
                # 创建新记录
                mastery_record = KnowledgePointMastery(
                    user_id=user_id,
                    keyword_id=keyword_id,
                    mastery_level=mastery_level,
                    material_progress=material_progress,
                    exercise_score=exercise_score,
                    sub_knowledge_contribution=sub_knowledge_contribution,
                    calculation_details=json.dumps(calculation_details),
                    last_updated=datetime.now()
                )
                session.add(mastery_record)
            
            session.commit()
            print(f"[mastery] calculated for user={user_id}, keyword={keyword_id}, value={mastery_level}, active_dims={len(active_weights)}")
            return mastery_record.to_dict()
            
        except Exception as e:
            self.logger.error(f"Error calculating single keyword mastery: {str(e)}")
            return {
                'mastery_level': 0.0,
                'material_progress': 0.0,
                'exercise_score': 0.0,
                'sub_knowledge_contribution': 0.0,
                'calculation_details': {'error': str(e)}
            }
    
    def _calculate_sub_knowledge_contribution_iterative(self, user_id: str, keyword_id: str,
                                                      existing_results: Dict[str, Dict],
                                                      session) -> float:
        """
        迭代计算子知识点贡献，避免递归
        """
        try:
            # 获取子知识点关系
            child_relations = session.query(KeywordRelation).filter_by(
                source_keyword_id=keyword_id
            ).all()
            
            if not child_relations:
                return 0.0
            
            total_weighted_mastery = 0.0
            total_weight = 0.0
            
            for relation in child_relations:
                child_keyword_id = relation.target_keyword_id
                weight = relation.strength or 1.0
                
                # 优先使用已计算的结果
                if child_keyword_id in existing_results:
                    mastery_level = existing_results[child_keyword_id].get('mastery_level', 0.0)
                else:
                    # 查询数据库中的现有记录
                    child_mastery = session.query(KnowledgePointMastery).filter_by(
                        user_id=user_id,
                        keyword_id=child_keyword_id
                    ).first()
                    
                    if child_mastery:
                        mastery_level = child_mastery.mastery_level
                    else:
                        # 如果没有记录，使用默认值
                        mastery_level = 0.0
                
                total_weighted_mastery += weight * mastery_level
                total_weight += weight
            
            # 计算加权平均掌握程度
            if total_weight > 0:
                return total_weighted_mastery / total_weight
            else:
                return 0.0
                
        except Exception as e:
            self.logger.error(f"Error calculating sub-knowledge contribution: {str(e)}")
            return 0.0
    
    def _calculate_material_progress(self, user_id: str, keyword_id: str, session) -> float:
        """
        计算教学材料学习进度
        """
        try:
            # 获取与知识点相关的视频和文档
            video_keywords = session.query(VideoKeyword).filter_by(keyword_id=keyword_id).all()
            document_keywords = session.query(DocumentKeyword).filter_by(keyword_id=keyword_id).all()
            
            total_progress = 0.0
            total_materials = 0
            
            # 计算视频学习进度
            for vk in video_keywords:
                video_progress = session.query(UserVideoProgress).filter_by(
                    user_id=user_id, video_id=vk.video_id
                ).first()
                
                if video_progress:
                    total_progress += video_progress.progress
                total_materials += 1
            
            # 计算文档学习进度
            for dk in document_keywords:
                doc_progress = session.query(DocumentProgress).filter_by(
                    user_id=user_id, document_id=dk.document_id
                ).first()
                
                if doc_progress:
                    total_progress += doc_progress.progress
                total_materials += 1
            
            if total_materials > 0:
                return total_progress / total_materials
            else:
                return 0.0
                
        except Exception as e:
            self.logger.error(f"Error calculating material progress: {str(e)}")
            return 0.0
    
    def _calculate_exercise_score(self, user_id: str, keyword_id: str, session) -> float:
        """
        计算练习表现得分
        """
        try:
            # 获取与知识点相关的题目
            question_keywords = session.query(QuestionKeyword).filter_by(
                keyword_id=keyword_id
            ).all()
            
            if not question_keywords:
                print(f"No questions found for keyword {keyword_id}")
                return 0.0
            
            total_weighted_score = 0.0
            total_weight = 0.0
            
            # 记录题目得分详情
            score_details = []
            
            for qk in question_keywords:
                # 获取用户对该题目的答题记录
                answers = session.query(StudentAnswer).filter_by(
                    student_id=user_id, question_id=qk.question_id
                ).all()
                
                if answers:
                    # 取最高分
                    best_score = max(answer.score for answer in answers)
                    
                    # 获取题目信息以确定权重
                    question = session.query(Question).filter_by(id=qk.question_id).first()
                    if question:
                        max_score = question.max_score or 5.0
                        difficulty = qk.difficulty_level or 3  # 从QuestionKeyword获取难度
                        
                        # 标准化得分
                        normalized_score = best_score / max_score
                        
                        # 应用难度系数
                        difficulty_coefficient = self.DIFFICULTY_COEFFICIENTS.get(difficulty, 1.5)
                        weighted_score = normalized_score * difficulty_coefficient
                        
                        total_weighted_score += weighted_score
                        total_weight += difficulty_coefficient

                        # 记录本题得分详情
                        score_details.append({
                            'question_id': str(qk.question_id),  # 转换UUID为字符串
                            'best_score': float(best_score),  # 确保数值类型
                            'max_score': float(max_score),
                            'normalized_score': float(normalized_score),
                            'difficulty': int(difficulty),
                            'weighted_score': float(weighted_score)
                        })
            
            # 输出得分详情日志
            print(
                f"Exercise score details for user {user_id}, keyword {keyword_id}:\n"
                f"Total questions: {len(question_keywords)}\n"
                f"Answered questions: {len(score_details)}\n"
                f"Total weighted score: {total_weighted_score:.2f}\n"
                f"Total weight: {total_weight:.2f}\n"
                f"Score details: {json.dumps(score_details, indent=2)}"
            )
            
            if total_weight > 0:
                final_score = min(1.0, total_weighted_score / total_weight)
                print(
                    f"Final exercise score for user {user_id}, keyword {keyword_id}: {final_score:.2f}"
                )
                return final_score
            else:
                print(f"No valid answers found for keyword {keyword_id}")
                return 0.0
                
        except Exception as e:
            self.logger.error(f"Error calculating exercise score: {str(e)}")
            return 0.0
    
    def _has_exercises_for_keyword(self, keyword_id: str, session) -> bool:
        """
        检查知识点是否有对应的练习题目
        
        Args:
            keyword_id: 知识点ID
            session: 数据库会话
            
        Returns:
            是否有练习题目
        """
        try:
            # 查询与知识点相关的题目
            question_count = session.query(QuestionKeyword).filter_by(
                keyword_id=keyword_id
            ).count()
            
            return question_count > 0
        except Exception as e:
            self.logger.error(f"Error checking exercises for keyword {keyword_id}: {str(e)}")
            return False
    
    def _has_sub_knowledge_for_keyword(self, keyword_id: str, session) -> bool:
        """
        检查知识点是否有子知识点
        
        Args:
            keyword_id: 知识点ID
            session: 数据库会话
            
        Returns:
            是否有子知识点
        """
        try:
            # 查询以该知识点为源的关系（即其子知识点）
            sub_keyword_count = session.query(KeywordRelation).filter_by(
                source_keyword_id=keyword_id
            ).count()
            
            return sub_keyword_count > 0
        except Exception as e:
            self.logger.error(f"Error checking sub-knowledge for keyword {keyword_id}: {str(e)}")
            return False
    
    def _is_calculation_fresh(self, mastery_record: KnowledgePointMastery, 
                             user_id: str = None, keyword_id: str = None, 
                             use_extended_cache: bool = False) -> bool:
        """
        智能检查掌握程度计算是否还新鲜（不需要重新计算）
        基于多种因素动态确定缓存时间
        """
        if not mastery_record.last_updated:
            return False
        
        # 计算缓存时间
        cache_hours = self._calculate_dynamic_cache_time(mastery_record, user_id, keyword_id, use_extended_cache)
        
        time_diff = datetime.now() - mastery_record.last_updated
        is_fresh = time_diff < timedelta(hours=cache_hours)
        
        if is_fresh:
            print(f"Cache hit: user={user_id}, keyword={keyword_id}, cache_hours={cache_hours:.1f}, age={time_diff}")
        else:
            print(f"Cache miss: user={user_id}, keyword={keyword_id}, cache_hours={cache_hours:.1f}, age={time_diff}")
            
        return is_fresh
    
    def _calculate_dynamic_cache_time(self, mastery_record: KnowledgePointMastery, 
                                    user_id: str = None, keyword_id: str = None,
                                    use_extended_cache: bool = False) -> float:
        """
        动态计算缓存时间，基于以下因素：
        1. 掌握程度高低
        2. 最近学习活跃度
        3. 知识点复杂度
        4. 用户整体活跃度
        """
        try:
            base_hours = self.CACHE_CONFIG['default_cache_hours']
            
            # 如果使用扩展缓存（用于批量预计算），使用更长的缓存时间
            if use_extended_cache:
                base_hours = self.CACHE_CONFIG['batch_cache_hours']
            
            # 因素1：掌握程度 - 掌握度越高，缓存时间越长
            mastery_level = mastery_record.mastery_level or 0.0
            if mastery_level >= 0.85:
                # 高掌握度，缓存时间延长
                mastery_multiplier = 2.0
            elif mastery_level >= 0.6:
                # 中等掌握度，正常缓存
                mastery_multiplier = 1.0
            else:
                # 低掌握度，缩短缓存时间以便及时更新
                mastery_multiplier = 0.5
            
            # 因素2：最近学习活跃度
            activity_multiplier = self._get_learning_activity_multiplier(user_id, keyword_id)
            
            # 因素3：知识点复杂度（子知识点数量）
            complexity_multiplier = self._get_knowledge_complexity_multiplier(keyword_id)
            
            # 计算最终缓存时间
            cache_hours = base_hours * mastery_multiplier * activity_multiplier * complexity_multiplier
            
            # 确保在合理范围内
            min_hours = self.CACHE_CONFIG['min_cache_minutes'] / 60
            max_hours = self.CACHE_CONFIG['low_activity_hours']
            cache_hours = max(min_hours, min(cache_hours, max_hours))
            
            return cache_hours
            
        except Exception as e:
            self.logger.warning(f"Error calculating dynamic cache time: {e}")
            return self.CACHE_CONFIG['default_cache_hours']
    
    def _get_learning_activity_multiplier(self, user_id: str, keyword_id: str) -> float:
        """
        获取学习活跃度乘数
        基于用户在相关知识点的最近学习活动
        """
        try:
            # 查询最近7天的学习活动
            recent_cutoff = datetime.now() - timedelta(days=7)
            
            # 检查视频学习活动
            video_activity = db.session.query(UserVideoProgress).join(
                VideoKeyword, VideoKeyword.video_id == UserVideoProgress.video_id
            ).filter(
                UserVideoProgress.user_id == user_id,
                VideoKeyword.keyword_id == keyword_id,
                UserVideoProgress.update_time >= recent_cutoff
            ).count()
            
            # 检查文档学习活动  
            doc_activity = db.session.query(DocumentProgress).join(
                DocumentKeyword, DocumentKeyword.document_id == DocumentProgress.document_id
            ).filter(
                DocumentProgress.user_id == user_id,
                DocumentKeyword.keyword_id == keyword_id,
                DocumentProgress.last_read_time >= recent_cutoff
            ).count()
            
            # 检查练习活动
            exercise_activity = db.session.query(StudentAnswer).join(
                Question, StudentAnswer.question_id == Question.id
            ).join(
                QuestionKeyword, QuestionKeyword.question_id == Question.id
            ).filter(
                StudentAnswer.student_id == user_id,
                QuestionKeyword.keyword_id == keyword_id,
                StudentAnswer.submit_time >= recent_cutoff
            ).count()
            
            total_activity = video_activity + doc_activity + exercise_activity
            
            if total_activity >= 5:
                # 高活跃度，缩短缓存时间
                return 0.3
            elif total_activity >= 2:
                # 中等活跃度，稍微缩短缓存时间
                return 0.7
            else:
                # 低活跃度，延长缓存时间
                return 1.5
                
        except Exception as e:
            self.logger.warning(f"Error calculating activity multiplier: {e}")
            return 1.0
    
    def _get_knowledge_complexity_multiplier(self, keyword_id: str) -> float:
        """
        获取知识点复杂度乘数
        基于知识点的子知识点数量和关系复杂度
        """
        try:
            # 查询子知识点数量
            child_count = db.session.query(KeywordRelation).filter_by(
                source_keyword_id=keyword_id
            ).count()
            
            # 查询父知识点数量
            parent_count = db.session.query(KeywordRelation).filter_by(
                target_keyword_id=keyword_id
            ).count()
            
            # 计算复杂度
            complexity_score = child_count * 1.0 + parent_count * 0.5
            
            if complexity_score >= 10:
                # 高复杂度，缩短缓存时间以便及时更新依赖
                return 0.6
            elif complexity_score >= 5:
                # 中等复杂度
                return 0.8
            else:
                # 低复杂度，可以延长缓存时间
                return 1.2
                
        except Exception as e:
            self.logger.warning(f"Error calculating complexity multiplier: {e}")
            return 1.0
    
    def batch_calculate_mastery(self, user_id: str, keyword_ids: List[str] = None, 
                              force_recalculate: bool = False, 
                              use_extended_cache: bool = True) -> Dict[str, Dict]:
        """
        批量计算多个知识点的掌握程度（集成Redis缓存）
        
        Args:
            user_id: 用户ID
            keyword_ids: 知识点ID列表，如果为None则计算用户所有相关知识点
            force_recalculate: 是否强制重新计算
            use_extended_cache: 是否使用扩展缓存策略（批量计算时使用更长的缓存时间）
        """
        results = {}
        redis_cache_hits = 0
        db_cache_hits = 0
        calculations_performed = 0
        
        try:
            # 如果未指定知识点，获取用户相关的所有知识点
            if keyword_ids is None:
                keyword_ids = self._get_user_related_keywords(user_id)
            
            total_operations = len(keyword_ids)
            
            # 第一步：检查Redis缓存
            if not force_recalculate:
                # 尝试从Redis获取批量缓存
                batch_cached = self._get_redis_batch_cache(user_id, keyword_ids)
                if batch_cached:
                    # 检查批量缓存是否包含所有需要的知识点
                    if all(kid in batch_cached for kid in keyword_ids):
                        results = {kid: batch_cached[kid] for kid in keyword_ids}
                        redis_cache_hits = len(keyword_ids)
                        print(f"Full Redis batch cache hit for user {user_id}: {len(keyword_ids)} keywords")
                        return results
                
                # 逐个检查Redis缓存
                for keyword_id in keyword_ids:
                    redis_cached = self._get_redis_mastery_cache(user_id, keyword_id)
                    if redis_cached:
                        results[keyword_id] = redis_cached
                        redis_cache_hits += 1
            
            # 第二步：检查数据库缓存（对于Redis中没有的）
            uncached_keywords = [kid for kid in keyword_ids if kid not in results]
            
            if uncached_keywords:
                # 清理缓存和访问记录
                self._calculation_cache.clear()
                self._visited_nodes.clear()
                
                # 批量检查数据库缓存
                cached_results, need_calculation = self._batch_check_cache(
                    user_id, uncached_keywords, force_recalculate, use_extended_cache
                )
                
                # 添加数据库缓存结果并同步到Redis
                for keyword_id, mastery_data in cached_results.items():
                    results[keyword_id] = mastery_data
                    db_cache_hits += 1
                    # 同步到Redis
                    self._set_redis_mastery_cache(user_id, keyword_id, mastery_data)
                
                # 第三步：计算剩余未缓存的知识点
                if need_calculation:
                    # 预加载数据
                    self._preload_batch_data([user_id], need_calculation)
                    
                    # 构建依赖图
                    dependency_graph = self._get_redis_dependency_graph()
                    if not dependency_graph:
                        dependency_graph = self._build_dependency_graph(db.session)
                        self._set_redis_dependency_graph(dependency_graph)
                    
                    # 批量计算
                    calculated_results = self._batch_calculate_optimized(
                        user_id, need_calculation, dependency_graph, force_recalculate
                    )
                    
                    results.update(calculated_results)
                    calculations_performed = len(calculated_results)
                    
                    # 将计算结果同步到Redis
                    for keyword_id, mastery_data in calculated_results.items():
                        self._set_redis_mastery_cache(user_id, keyword_id, mastery_data)
                    
                    # 设置批量缓存
                    if len(results) > 1:
                        self._set_redis_batch_cache(user_id, keyword_ids, results)
            
            # 记录缓存命中率和性能统计
            redis_hit_rate = (redis_cache_hits / total_operations) * 100 if total_operations > 0 else 0
            db_hit_rate = (db_cache_hits / total_operations) * 100 if total_operations > 0 else 0
            calc_rate = (calculations_performed / total_operations) * 100 if total_operations > 0 else 0
            
            print(
                f"Batch mastery calculation for user {user_id}: "
                f"Redis hits: {redis_hit_rate:.1f}% ({redis_cache_hits}/{total_operations}), "
                f"DB hits: {db_hit_rate:.1f}% ({db_cache_hits}/{total_operations}), "
                f"Calculations: {calc_rate:.1f}% ({calculations_performed}/{total_operations})"
            )
            
            return results
                
        except Exception as e:
            self.logger.error(f"Error in batch calculation: {str(e)}")
            return results
    
    def precompute_mastery_for_course(self, user_id: str, course_id: str) -> Dict[str, Any]:
        """
        为指定用户预计算课程中所有知识点的掌握程度
        
        Args:
            user_id: 用户ID
            course_id: 课程ID
            
        Returns:
            计算结果统计信息
        """
        try:
            # 获取课程相关的知识点
            course_keywords = self._get_course_keywords(course_id)
            if not course_keywords:
                self.logger.warning(f"No keywords found for course {course_id}")
                return {
                    'total_calculations': 0, 
                    'user_id': user_id,
                    'course_id': course_id,
                    'keywords': []
                }

            # 批量计算掌握程度
            results = self.batch_calculate_mastery(
                user_id=user_id,
                keyword_ids=course_keywords,
                force_recalculate=False,
                use_extended_cache=True
            )
            
            return {
                'total_calculations': len(results),
                'user_id': user_id,
                'course_id': course_id,
                'keywords': course_keywords,
                'results': results
            }
            
        except Exception as e:
            self.logger.error(f"Error precomputing mastery for course {course_id}: {e}")
            return {
                'total_calculations': 0,
                'user_id': user_id,
                'course_id': course_id,
                'keywords': [],
                'error': str(e)
            }
    
    def _get_course_keywords(self, course_id: str) -> List[str]:
        """
        获取课程相关的所有知识点ID
        """
        try:
            keyword_ids = set()
            
            # 从课程视频获取关键词
            video_keywords = db.session.query(VideoKeyword.keyword_id).join(
                Video, VideoKeyword.video_id == Video.id
            ).filter(Video.course_id == course_id, Video.is_deleted == False).distinct().all()
            keyword_ids.update([str(kw[0]) for kw in video_keywords])
            
            # 从课程文档获取关键词  
            doc_keywords = db.session.query(DocumentKeyword.keyword_id).join(
                Document, DocumentKeyword.document_id == Document.id
            ).filter(Document.course_id == course_id, Document.is_deleted == False).distinct().all()
            keyword_ids.update([str(kw[0]) for kw in doc_keywords])
            
            # 从课程作业题目获取关键词
            from models.models import Assignment
            question_keywords = db.session.query(QuestionKeyword.keyword_id).join(
                Question, QuestionKeyword.question_id == Question.id
            ).join(
                Assignment, Question.assignment_id == Assignment.id
            ).filter(Assignment.course_id == course_id).distinct().all()
            keyword_ids.update([str(kw[0]) for kw in question_keywords])
            
            return list(keyword_ids)
            
        except Exception as e:
            self.logger.error(f"Error getting course keywords: {e}")
            return []

    def _batch_check_cache(self, user_id: str, keyword_ids: List[str], 
                          force_recalculate: bool, use_extended_cache: bool) -> Tuple[Dict[str, Dict], List[str]]:
        """
        批量检查缓存状态
        
        Returns:
            (cached_results, need_calculation_ids)
        """
        cached_results = {}
        need_calculation = []
        
        if force_recalculate:
            return cached_results, keyword_ids
        
        try:
            # 批量查询现有记录
            existing_records = db.session.query(KnowledgePointMastery).filter(
                KnowledgePointMastery.user_id == user_id,
                KnowledgePointMastery.keyword_id.in_(keyword_ids)
            ).all()
            
            existing_map = {record.keyword_id: record for record in existing_records}
            
            for keyword_id in keyword_ids:
                record = existing_map.get(keyword_id)
                if record and self._is_calculation_fresh(record, user_id, keyword_id, use_extended_cache):
                    cached_results[keyword_id] = record.to_dict()
                else:
                    need_calculation.append(keyword_id)
            
            return cached_results, need_calculation
            
        except Exception as e:
            self.logger.error(f"Error in batch cache check: {e}")
            return cached_results, keyword_ids
    
    def batch_calculate_course_mastery(self, student_ids: List[str], keyword_ids: List[str], 
                                      force_recalculate: bool = False) -> Dict[str, Dict[str, Dict]]:
        """
        批量计算多个学生对多个知识点的掌握程度（高度优化版，集成Redis缓存）
        
        Args:
            student_ids: 学生ID列表
            keyword_ids: 知识点ID列表
            force_recalculate: 是否强制重新计算
            
        Returns:
            嵌套字典: {student_id: {keyword_id: mastery_data}}
        """
        results = {}
        redis_cache_hits = 0
        db_cache_hits = 0
        calculations_performed = 0
        total_operations = len(student_ids) * len(keyword_ids)
        
        try:
            # 第一步：批量检查Redis缓存
            for student_id in student_ids:
                results[student_id] = {}
                if not force_recalculate:
                    # 尝试从Redis获取批量缓存
                    batch_cached = self._get_redis_batch_cache(student_id, keyword_ids)
                    if batch_cached:
                        # 检查批量缓存是否包含所有需要的知识点
                        if all(kid in batch_cached for kid in keyword_ids):
                            results[student_id] = {kid: batch_cached[kid] for kid in keyword_ids}
                            redis_cache_hits += len(keyword_ids)
                            continue
                    
                    # 逐个检查Redis缓存
                    for keyword_id in keyword_ids:
                        redis_cached = self._get_redis_mastery_cache(student_id, keyword_id)
                        if redis_cached:
                            results[student_id][keyword_id] = redis_cached
                            redis_cache_hits += 1
            
            # 第二步：批量查询数据库中的现有记录（对于Redis中没有的）
            students_need_db_check = []
            keywords_need_db_check = []
            
            for student_id in student_ids:
                uncached_keywords = [kid for kid in keyword_ids if kid not in results[student_id]]
                if uncached_keywords:
                    students_need_db_check.append(student_id)
                    keywords_need_db_check.extend(uncached_keywords)
            
            if students_need_db_check:
                existing_records = db.session.query(KnowledgePointMastery).filter(
                    KnowledgePointMastery.user_id.in_(students_need_db_check),
                    KnowledgePointMastery.keyword_id.in_(list(set(keywords_need_db_check)))
                ).all()
                
                # 组织现有记录
                existing_dict = {}
                for record in existing_records:
                    if record.user_id not in existing_dict:
                        existing_dict[record.user_id] = {}
                    existing_dict[record.user_id][record.keyword_id] = record
                
                # 检查数据库缓存并同步到Redis
                for student_id in students_need_db_check:
                    uncached_keywords = [kid for kid in keyword_ids if kid not in results[student_id]]
                    cached_results, still_uncached = self._batch_check_cache(
                        student_id, uncached_keywords, force_recalculate, True
                    )
                    
                    # 添加数据库缓存结果并同步到Redis
                    for keyword_id, mastery_data in cached_results.items():
                        results[student_id][keyword_id] = mastery_data
                        db_cache_hits += 1
                        # 同步到Redis
                        self._set_redis_mastery_cache(student_id, keyword_id, mastery_data)
            
            # 第三步：计算剩余未缓存的知识点
            students_need_calculation = []
            for student_id in student_ids:
                uncached_keywords = [kid for kid in keyword_ids if kid not in results[student_id]]
                if uncached_keywords:
                    students_need_calculation.append((student_id, uncached_keywords))
            
            if students_need_calculation:
                # 预加载数据（只为需要计算的学生和知识点）
                all_students_calc = [item[0] for item in students_need_calculation]
                all_keywords_calc = list(set([kid for _, kids in students_need_calculation for kid in kids]))
                self._preload_batch_data(all_students_calc, all_keywords_calc)
                
                # 构建依赖图（只构建一次）
                dependency_graph = self._get_redis_dependency_graph()
                if not dependency_graph:
                    dependency_graph = self._build_dependency_graph(db.session)
                    self._set_redis_dependency_graph(dependency_graph)
                
                # 批量计算
                for student_id, uncached_keywords in students_need_calculation:
                    calculated_results = self._batch_calculate_optimized(
                        student_id, uncached_keywords, dependency_graph, force_recalculate
                    )
                    results[student_id].update(calculated_results)
                    calculations_performed += len(calculated_results)
                    
                    # 将计算结果同步到Redis
                    for keyword_id, mastery_data in calculated_results.items():
                        self._set_redis_mastery_cache(student_id, keyword_id, mastery_data)
                    
                    # 设置批量缓存
                    if len(calculated_results) > 1:
                        self._set_redis_batch_cache(student_id, list(calculated_results.keys()), calculated_results)
            
            # 记录缓存命中率和性能统计
            redis_hit_rate = (redis_cache_hits / total_operations) * 100 if total_operations > 0 else 0
            db_hit_rate = (db_cache_hits / total_operations) * 100 if total_operations > 0 else 0
            calc_rate = (calculations_performed / total_operations) * 100 if total_operations > 0 else 0
            
            print(
                f"Batch calculation completed. "
                f"Redis hits: {redis_hit_rate:.1f}% ({redis_cache_hits}/{total_operations}), "
                f"DB hits: {db_hit_rate:.1f}% ({db_cache_hits}/{total_operations}), "
                f"Calculations: {calc_rate:.1f}% ({calculations_performed}/{total_operations})"
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in batch course mastery calculation: {str(e)}")
            return results
    
    def _preload_batch_data(self, student_ids: List[str], keyword_ids: List[str]):
        """
        预加载批量计算所需的数据，减少后续查询
        """
        try:
            # 预加载视频进度数据
            video_progress_data = db.session.query(UserVideoProgress).filter(
                UserVideoProgress.user_id.in_(student_ids)
            ).all()
            
            # 预加载文档进度数据
            doc_progress_data = db.session.query(DocumentProgress).filter(
                DocumentProgress.user_id.in_(student_ids)
            ).all()
            
            # 预加载学生答案数据
            student_answers = db.session.query(StudentAnswer).filter(
                StudentAnswer.student_id.in_(student_ids)
            ).all()
            
            # 预加载知识点关系数据
            keyword_relations = db.session.query(KeywordRelation).filter(
                or_(
                    KeywordRelation.source_keyword_id.in_(keyword_ids),
                    KeywordRelation.target_keyword_id.in_(keyword_ids)
                )
            ).all()
            
            print(f"Preloaded batch data: videos={len(video_progress_data)}, "
                            f"docs={len(doc_progress_data)}, answers={len(student_answers)}, "
                            f"relations={len(keyword_relations)}")
            
        except Exception as e:
            self.logger.warning(f"Error preloading batch data: {e}")
    
    def _batch_calculate_optimized(self, user_id: str, keyword_ids: List[str], 
                                 dependency_graph: Dict[str, List[str]], 
                                 force_recalculate: bool) -> Dict[str, Dict]:
        """
        优化的批量计算方法，避免重复构建依赖图和重复查询
        """
        results = {}
        
        try:
            # 清理缓存和访问记录
            self._calculation_cache.clear()
            self._visited_nodes.clear()
            
            # 对每个知识点进行计算
            for keyword_id in keyword_ids:
                try:
                    # 使用已构建的依赖图进行计算
                    single_results = self._calculate_mastery_topologically(
                        user_id, keyword_id, dependency_graph, force_recalculate, db.session
                    )
                    
                    # 只取目标知识点的结果
                    if keyword_id in single_results:
                        results[keyword_id] = single_results[keyword_id]
                    else:
                        # 如果拓扑排序没有返回目标知识点，直接计算
                        result = self._calculate_single_keyword_mastery(
                            user_id, keyword_id, {}, force_recalculate, db.session
                        )
                        results[keyword_id] = result
                        
                except Exception as e:
                    self.logger.error(f"Error calculating keyword {keyword_id} for user {user_id}: {e}")
                    results[keyword_id] = {
                        'mastery_level': 0.0,
                        'material_progress': 0.0,
                        'exercise_score': 0.0,
                        'sub_knowledge_contribution': 0.0,
                        'calculation_details': {'error': str(e)}
                    }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in optimized batch calculation: {e}")
            return results

    def get_mastery_overview(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户知识点掌握程度概览
        
        Args:
            user_id: 用户ID
            
        Returns:
            掌握程度概览数据
        """
        try:
            # 获取用户所有掌握程度记录
            mastery_records = KnowledgePointMastery.query.filter_by(
                user_id=user_id
            ).all()
            
            if not mastery_records:
                return {
                    'total_keywords': 0,
                    'mastered_keywords': 0,
                    'average_mastery': 0.0,
                    'mastery_distribution': {
                        'excellent': 0,    # >= 0.9
                        'good': 0,         # >= 0.7
                        'average': 0,      # >= 0.5
                        'poor': 0,         # >= 0.3
                        'very_poor': 0     # < 0.3
                    },
                    'recent_progress': []
                }
            
            # 计算统计信息
            total_keywords = len(mastery_records)
            mastery_levels = [record.mastery_level for record in mastery_records]
            average_mastery = sum(mastery_levels) / total_keywords
            mastered_keywords = len([level for level in mastery_levels if level >= 0.7])
            
            # 掌握程度分布
            distribution = {
                'excellent': len([level for level in mastery_levels if level >= 0.9]),
                'good': len([level for level in mastery_levels if 0.7 <= level < 0.9]),
                'average': len([level for level in mastery_levels if 0.5 <= level < 0.7]),
                'poor': len([level for level in mastery_levels if 0.3 <= level < 0.5]),
                'very_poor': len([level for level in mastery_levels if level < 0.3])
            }
            
            # 最近进度（最近更新的前10个）
            recent_records = sorted(
                mastery_records, 
                key=lambda x: x.last_updated or x.created_at,
                reverse=True
            )[:10]
            
            recent_progress = []
            for record in recent_records:
                keyword = Keyword.query.get(record.keyword_id)
                if keyword:
                    recent_progress.append({
                        'keyword_id': str(record.keyword_id),
                        'keyword_name': keyword.name,
                        'mastery_level': record.mastery_level,
                        'last_updated': record.last_updated.isoformat() if record.last_updated else None
                    })
            
            return {
                'total_keywords': total_keywords,
                'mastered_keywords': mastered_keywords,
                'average_mastery': round(average_mastery, 3),
                'mastery_distribution': distribution,
                'recent_progress': recent_progress
            }
            
        except Exception as e:
            self.logger.error(f"Error getting mastery overview: {e}")
            return {
                'total_keywords': 0,
                'mastered_keywords': 0,
                'average_mastery': 0.0,
                'mastery_distribution': {
                    'excellent': 0, 'good': 0, 'average': 0, 'poor': 0, 'very_poor': 0
                },
                'recent_progress': [],
                'error': str(e)
            }
    
    def _get_user_related_keywords(self, user_id: str) -> List[str]:
        """
        获取用户相关的所有知识点ID
        
        Args:
            user_id: 用户ID
            
        Returns:
            知识点ID列表
        """
        try:
            keyword_ids = set()
            
            # 从视频进度获取
            video_keywords = db.session.query(VideoKeyword.keyword_id)\
                .join(UserVideoProgress, VideoKeyword.video_id == UserVideoProgress.video_id)\
                .filter(UserVideoProgress.user_id == user_id)\
                .distinct().all()
            keyword_ids.update([str(kw[0]) for kw in video_keywords])
            
            # 从文档进度获取
            document_keywords = db.session.query(DocumentKeyword.keyword_id)\
                .join(DocumentProgress, DocumentKeyword.document_id == DocumentProgress.document_id)\
                .filter(DocumentProgress.user_id == user_id)\
                .distinct().all()
            keyword_ids.update([str(kw[0]) for kw in document_keywords])
            
            # 从学生答案获取
            question_keywords = db.session.query(QuestionKeyword.keyword_id)\
                .join(StudentAnswer, QuestionKeyword.question_id == StudentAnswer.question_id)\
                .filter(StudentAnswer.student_id == user_id)\
                .distinct().all()
            keyword_ids.update([str(kw[0]) for kw in question_keywords])
            
            return list(keyword_ids)
            
        except Exception as e:
            self.logger.error(f"Error getting user related keywords: {e}")
            return []