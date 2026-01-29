#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
个性化推荐API路由
提供基于知识点掌握情况的个性化学习推荐接口
"""

import logging
from flask import Blueprint, request, jsonify
from utils.auth import token_required
from services.personalized_recommendation_service import personalized_recommendation_service
from utils.result import Result

logger = logging.getLogger(__name__)

# 创建蓝图
personalized_recommendation_bp = Blueprint('personalized_recommendation', __name__)

@personalized_recommendation_bp.route('/api/personalized-recommendation/learning-path', methods=['GET'])
@token_required
def get_personalized_learning_path():
    """
    获取个性化学习路径推荐
    
    Query Parameters:
        limit: 推荐数量限制，默认10
        force_refresh: 是否强制刷新缓存，默认false
        
    Returns:
        个性化学习路径推荐结果
    """
    try:
        user_id = request.user.get('user_id')
        if not user_id:
            return jsonify(Result.error(401, "未登录")), 401
        
        limit = request.args.get('limit', 10, type=int)
        if limit <= 0 or limit > 50:
            limit = 10
        
        # 检查是否强制刷新
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        
        # 获取个性化学习路径推荐
        recommendations = personalized_recommendation_service.get_personalized_learning_path(
            user_id, limit=limit, force_refresh=force_refresh
        )
        
        return jsonify(Result.success(recommendations, "获取个性化学习路径成功"))
        
    except Exception as e:
        logger.error(f"获取个性化学习路径失败: {str(e)}")
        return jsonify(Result.error(500, f"获取个性化学习路径失败: {str(e)}")), 500


@personalized_recommendation_bp.route('/api/personalized-recommendation/knowledge-point/<keyword_id>', methods=['GET'])
@token_required
def get_knowledge_point_recommendations(keyword_id):
    """
    获取特定知识点的个性化推荐
    
    Args:
        keyword_id: 知识点ID
        
    Returns:
        知识点推荐结果
    """
    try:
        user_id = request.user.get('user_id')
        if not user_id:
            return jsonify(Result.error(401, "未登录")), 401
        
        # 获取知识点推荐
        recommendations = personalized_recommendation_service.get_knowledge_point_recommendations(
            user_id, keyword_id
        )
        
        return jsonify(Result.success(recommendations, "获取知识点推荐成功"))
        
    except Exception as e:
        logger.error(f"获取知识点推荐失败: {str(e)}")
        return jsonify(Result.error(500, f"获取知识点推荐失败: {str(e)}")), 500


@personalized_recommendation_bp.route('/api/personalized-recommendation/next-steps', methods=['GET'])
@token_required
def get_next_learning_steps():
    """
    获取下一步学习建议
    基于用户当前掌握度最高的知识点，推荐接下来应该学习的内容
    
    Query Parameters:
        force_refresh: 是否强制刷新缓存，默认false
    
    Returns:
        下一步学习建议
    """
    try:
        user_id = request.user.get('user_id')
        if not user_id:
            return jsonify(Result.error(401, "未登录")), 401
        
        # 检查是否强制刷新
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        
        # 获取推荐数量限制
        limit = request.args.get('limit', 5, type=int)
        if limit <= 0 or limit > 10:
            limit = 5
        
        # 获取个性化学习路径推荐
        recommendations = personalized_recommendation_service.get_personalized_learning_path(
            user_id, limit=limit, force_refresh=force_refresh
        )
        
        # 提取下一步学习建议
        next_steps = []
        for rec in recommendations.get('learning_path_recommendations', []):
            next_steps.append({
                'from_keyword': rec['source_keyword']['name'],
                'to_keyword': rec['recommended_keyword']['name'],
                'reason': rec['recommendation_reason'],
                'learning_benefits': rec.get('learning_benefits', []),
                'priority_score': rec['priority_score'],
                'resources_summary': {
                    'videos': len(rec['resources']['videos']),
                    'documents': len(rec['resources']['documents']),
                    'questions': len(rec['resources']['questions'])
                },
                'recommended_keyword': rec['recommended_keyword'],
                'resources': rec['resources']
            })
        
        return jsonify(Result.success({
            'next_steps': next_steps,
            'user_mastery_summary': {
                'total_keywords': recommendations.get('user_mastery_overview', {}).get('total_keywords', 0),
                'mastered_keywords': recommendations.get('user_mastery_overview', {}).get('mastered_keywords', 0),
                'average_mastery': recommendations.get('user_mastery_overview', {}).get('average_mastery', 0.0)
            },
            'cache_info': recommendations.get('cache_info', {})
        }, "获取下一步学习建议成功"))
        
    except Exception as e:
        logger.error(f"获取下一步学习建议失败: {str(e)}")
        return jsonify(Result.error(500, f"获取下一步学习建议失败: {str(e)}")), 500


@personalized_recommendation_bp.route('/api/personalized-recommendation/learning-resources/<keyword_id>', methods=['GET'])
@token_required
def get_learning_resources_for_keyword(keyword_id):
    """
    获取特定知识点的学习资源推荐
    
    Args:
        keyword_id: 知识点ID
        
    Returns:
        学习资源推荐
    """
    try:
        user_id = request.user.get('user_id')
        if not user_id:
            return jsonify(Result.error(401, "未登录")), 401
        
        # 获取学习资源
        resources = personalized_recommendation_service._get_learning_resources(keyword_id, user_id)
        
        # 使用LLM生成学习建议
        from models.models import Keyword
        keyword = Keyword.query.get(keyword_id)
        if not keyword:
            return jsonify(Result.error(404, "知识点不存在")), 404
        
        # 生成学习建议
        learning_suggestion = personalized_recommendation_service._generate_recommendation_reason(
            "当前学习进度", keyword.name, 0.5, resources
        )
        
        return jsonify(Result.success({
            'keyword': {
                'id': keyword_id,
                'name': keyword.name,
                'category': keyword.category
            },
            'resources': resources,
            'learning_suggestion': learning_suggestion,
            'resource_summary': {
                'total_videos': len(resources['videos']),
                'total_documents': len(resources['documents']),
                'total_questions': len(resources['questions'])
            }
        }, "获取学习资源推荐成功"))
        
    except Exception as e:
        logger.error(f"获取学习资源推荐失败: {str(e)}")
        return jsonify(Result.error(500, f"获取学习资源推荐失败: {str(e)}")), 500


@personalized_recommendation_bp.route('/api/personalized-recommendation/study-plan', methods=['GET'])
@token_required
def generate_study_plan():
    """
    生成个性化学习计划
    基于用户的掌握情况生成完整的学习计划
    
    Query Parameters:
        days: 学习计划天数，默认7天
        
    Returns:
        个性化学习计划
    """
    try:
        user_id = request.user.get('user_id')
        if not user_id:
            return jsonify(Result.error(401, "未登录")), 401
        
        days = request.args.get('days', 7, type=int)
        if days <= 0 or days > 30:
            days = 7
        
        # 获取学习路径推荐
        recommendations = personalized_recommendation_service.get_personalized_learning_path(
            user_id, limit=days * 2  # 每天可能有多个学习任务
        )
        
        # 生成学习计划
        study_plan = []
        learning_recs = recommendations.get('learning_path_recommendations', [])
        
        for i in range(min(days, len(learning_recs))):
            rec = learning_recs[i]
            day_plan = {
                'day': i + 1,
                'target_keyword': rec['recommended_keyword'],
                'from_keyword': rec['source_keyword']['name'],
                'learning_goal': rec['recommendation_reason'],
                'resources': rec['resources'],
                'estimated_time': _estimate_learning_time(rec['resources']),
                'priority': 'high' if rec['priority_score'] > 0.7 else 'medium' if rec['priority_score'] > 0.4 else 'low'
            }
            study_plan.append(day_plan)
        
        return jsonify(Result.success({
            'study_plan': study_plan,
            'plan_duration_days': days,
            'total_learning_targets': len(study_plan),
            'user_mastery_overview': recommendations.get('user_mastery_overview', {})
        }, "生成个性化学习计划成功"))
        
    except Exception as e:
        logger.error(f"生成个性化学习计划失败: {str(e)}")
        return jsonify(Result.error(500, f"生成个性化学习计划失败: {str(e)}")), 500


@personalized_recommendation_bp.route('/api/personalized-recommendation/cache-info', methods=['GET'])
@token_required
def get_cache_info():
    """
    获取用户推荐缓存信息
    
    Returns:
        缓存信息
    """
    try:
        user_id = request.user.get('user_id')
        if not user_id:
            return jsonify(Result.error(401, "未登录")), 401
        
        cache_info = personalized_recommendation_service.get_cache_info(user_id)
        
        if cache_info is None:
            return jsonify(Result.success({
                'is_cached': False,
                'message': '暂无缓存数据'
            }, "获取缓存信息成功"))
        
        return jsonify(Result.success(cache_info, "获取缓存信息成功"))
        
    except Exception as e:
        logger.error(f"获取缓存信息失败: {str(e)}")
        return jsonify(Result.error(500, f"获取缓存信息失败: {str(e)}")), 500


@personalized_recommendation_bp.route('/api/personalized-recommendation/refresh', methods=['POST'])
@token_required
def refresh_recommendations():
    """
    强制刷新用户推荐
    
    Returns:
        刷新后的推荐结果
    """
    try:
        user_id = request.user.get('user_id')
        if not user_id:
            return jsonify(Result.error(401, "未登录")), 401
        
        limit = request.json.get('limit', 10) if request.json else 10
        
        # 强制刷新推荐
        recommendations = personalized_recommendation_service.refresh_user_recommendations(user_id, limit)
        
        return jsonify(Result.success(recommendations, "推荐已刷新"))
        
    except Exception as e:
        logger.error(f"刷新推荐失败: {str(e)}")
        return jsonify(Result.error(500, f"刷新推荐失败: {str(e)}")), 500


@personalized_recommendation_bp.route('/api/personalized-recommendation/invalidate-cache', methods=['DELETE'])
@token_required
def invalidate_user_cache():
    """
    清除用户推荐缓存
    
    Returns:
        清除结果
    """
    try:
        user_id = request.user.get('user_id')
        if not user_id:
            return jsonify(Result.error(401, "未登录")), 401
        
        success = personalized_recommendation_service._invalidate_user_cache(user_id)
        
        if success:
            return jsonify(Result.success({'cleared': True}, "缓存已清除"))
        else:
            return jsonify(Result.error(500, "缓存清除失败")), 500
        
    except Exception as e:
        logger.error(f"清除缓存失败: {str(e)}")
        return jsonify(Result.error(500, f"清除缓存失败: {str(e)}")), 500

def _estimate_learning_time(resources: dict) -> str:
    """
    估算学习时间
    
    Args:
        resources: 学习资源字典
        
    Returns:
        估算的学习时间字符串
    """
    total_minutes = 0
    
    # 视频时间
    for video in resources.get('videos', []):
        if video.get('duration'):
            # 假设duration是秒数
            total_minutes += video['duration'] / 60
    
    # 文档阅读时间（假设每个文档15分钟）
    total_minutes += len(resources.get('documents', [])) * 15
    
    # 练习时间（假设每道题3分钟）
    total_minutes += len(resources.get('questions', [])) * 3
    
    if total_minutes < 60:
        return f"{int(total_minutes)}分钟"
    else:
        hours = int(total_minutes // 60)
        minutes = int(total_minutes % 60)
        return f"{hours}小时{minutes}分钟" if minutes > 0 else f"{hours}小时"