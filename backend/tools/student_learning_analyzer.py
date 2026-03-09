#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Student Learning Analysis Tool
Provides learning progress tracking, knowledge point mastery analysis and AI-assisted learning advice.
"""

from typing import Dict, List, Any, Tuple, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, desc
from models.models import (
    db, KnowledgePointMastery, Keyword, KeywordRelation,
    UserVideoProgress, DocumentProgress, StudentAnswer,
    Video, Document, Question, Assignment, Course
)
from services.mastery_calculator import MasteryCalculator
from services.personalized_recommendation_service import personalized_recommendation_service
# from services.llm_service import LLMService  # 已移除LLM依赖
from .base_tool import BaseTool
from .permission_utils import get_user_role, filter_courses_by_permission
import logging

logger = logging.getLogger(__name__)

class StudentLearningInput(BaseModel):
    """学生学习分析工具的输入参数模型"""
    query: str = Field(default="", description="学生标识符（学生ID或学生姓名）。为空字符串时分析当前用户自己的学习情况，非空时供教师查看指定学生的学习情况")

class StudentLearningAnalyzer(BaseTool):
    """学生学习分析工具类"""
    
    name = "student_learning_analysis"
    description = "分析学生的学习情况，包括学习进度、知识点掌握情况和个性化学习建议。参数为空字符串时表示分析学生自己的学习情况；教师可以传入学生姓名或ID来查看指定学生的学习情况。"
    
    def __init__(self, user_id: str = None):
        super().__init__(user_id=user_id)
        self.mastery_calculator = MasteryCalculator()
        # 不要在初始化时就通知工具启动，应该在search方法中通知


    
    def search(self, query: str = "") -> str:
        """分析学生学习状态
        
        Args:
            query: 学生标识符
                   - 为空字符串时：分析当前用户自己的学习情况
                   - 非空时：学生ID或学生姓名，供教师查看指定学生的学习情况
            
        Returns:
            学习状态分析结果，包含:
            - 整体学习进度
            - 最强/最弱知识点
            - AI学习建议
        """
        try:
            # 添加工具启动通知
            self._notify_tool_start(self.get_display_info())
            
            print(f"[FLOW] ===== StudentLearningAnalyzer.search 开始执行 =====")
            print(f"[FLOW] 输入参数 query: '{query}'")
            print(f"[FLOW] 参数类型: {type(query)}")
            print(f"[FLOW] 当前用户ID: {self.user_id}")
            print(f"[FLOW] 用户ID类型: {type(self.user_id)}")
            
            # 强制刷新日志输出
            import sys
            sys.stdout.flush()
            
            # 确定目标学生ID
            print(f"[FLOW] 开始确定目标学生ID...")
            if not query or query.strip() == "":
                # 空字符串表示查看自己的学习情况
                target_student_id = self.user_id
                student_identifier = "我"
                print(f"[FLOW] 查看自己的学习情况，target_student_id: {target_student_id}")
            else:
                # 非空值表示教师查看指定学生
                student_identifier = query.strip()
                print(f"[FLOW] 准备解析学生标识符: {student_identifier}")
                target_student_id = self._resolve_student_id(student_identifier)
                print(f"[FLOW] 查看指定学生 {student_identifier}，target_student_id: {target_student_id}")
            
            print(f"[FLOW] 最终确定的target_student_id: {target_student_id}")
            
            # 强制刷新日志输出
            sys.stdout.flush()
            if not target_student_id:
                if not query or query.strip() == "":
                    error_msg = "无法获取当前用户信息"
                else:
                    error_msg = f"无法找到学生：{student_identifier}"
                print(f"[FLOW] {error_msg}")
                self._notify_tool_result({
                    "success": False,
                    "message": error_msg,
                    "user_id": None
                })
                return error_msg
            
            # 权限检查
            if not self.has_user_access(target_student_id):
                user_role = get_user_role(self.user_id) if self.user_id else None
                if user_role == 'student':
                    return "学生只能查看自己的学习分析"
                else:
                    return "您没有权限查看此学生的学习分析"
            
            print(f"[FLOW] 开始分析学生 {target_student_id} 的学习情况")
            
            # 确保在应用上下文中执行分析
            def analyze_in_context():
                # 分析学习状态
                analysis_result = self._analyze_learning_status(target_student_id)
                return analysis_result
            
            analysis_result = self._execute_with_app_context(analyze_in_context)
            
            if not analysis_result:
                error_msg = "学习状态分析返回空结果"
                print(f"[ERROR] {error_msg}")
                self._notify_tool_result({
                    "success": False,
                    "message": error_msg,
                    "user_id": target_student_id
                })
                return error_msg
            
            # 格式化分析结果
            result_text = f"学习状态分析结果：\n\n"
            
            # 1. 整体进度
            progress = analysis_result['learning_progress']
            result_text += f"1. 学习进度：\n"
            result_text += f"- 视频学习：{progress['video_progress']['percentage']}% ({progress['video_progress']['completed']}/{progress['video_progress']['total']})\n"
            result_text += f"- 文档阅读：{progress['document_progress']['percentage']}% ({progress['document_progress']['completed']}/{progress['document_progress']['total']})\n"
            result_text += f"- 作业完成：{progress['assignment_progress']['percentage']}% ({progress['assignment_progress']['completed']}/{progress['assignment_progress']['total']})\n\n"
            
            # 2. 知识点掌握情况
            result_text += f"2. 知识点掌握情况：\n"
            result_text += "最擅长的知识点：\n"
            for point in analysis_result['strongest_points'][:3]:  # 只显示前3个
                result_text += f"- {point['name']} (掌握度: {point['mastery_level']}%)\n"
            
            result_text += "\n最需要提高的知识点：\n"
            for point in analysis_result['weakest_points'][:3]:  # 只显示前3个
                result_text += f"- {point['name']} (掌握度: {point['mastery_level']}%)\n"
            
            # 3. 学习建议（基于数据分析）
            if analysis_result.get('learning_suggestions'):
                result_text += f"\n3. 学习建议：\n{analysis_result['learning_suggestions']}\n"
                
            # 4. 技能缺口和补充任务推荐
            if analysis_result.get('skill_gaps_and_recommendations'):
                result_text += f"\n4. 技能缺口与推荐任务：\n{analysis_result['skill_gaps_and_recommendations']}\n"
            
            # 通知工具执行结果
            self._notify_tool_result({
                "success": True,
                "message": "学习状态分析完成",
                "analysis_type": "comprehensive",
                "user_id": target_student_id
            })
            
            return result_text
            
        except Exception as e:
            error_msg = f'分析学习状态失败: {str(e)}'
            logger.error(error_msg)
            self._notify_tool_result({
                "success": False,
                "message": error_msg,
                "user_id": getattr(self, 'target_student_id', None)
            })
            return error_msg
    
    def _analyze_learning_status(self, user_id: str) -> Dict[str, Any]:
        """分析学生学习状态"""
        try:
            print(f"[FLOW] _analyze_learning_status 开始，user_id: {user_id}")
            
            # 获取知识点掌握度概览
            mastery_overview = self.mastery_calculator.get_mastery_overview(user_id)
            print(f"[FLOW] 获取掌握度概览完成: {type(mastery_overview)}")
            
            # 获取学习进度数据
            progress_data = self._get_learning_progress(user_id)
            print(f"[FLOW] 获取学习进度完成: {type(progress_data)}")
            
            # 获取最强和最弱知识点
            strongest_points, weakest_points = self._analyze_knowledge_points(user_id)
            print(f"[FLOW] 分析知识点完成: strongest={len(strongest_points)}, weakest={len(weakest_points)}")
            
            # 获取技能缺口和推荐 (个性化学习路径)
            skill_gaps_str = self._get_skill_gaps_and_recommendations(user_id)

            result = {
                'mastery_overview': mastery_overview,
                'learning_progress': progress_data,
                'strongest_points': strongest_points,
                'weakest_points': weakest_points,
                'skill_gaps_and_recommendations': skill_gaps_str
            }
            
            print(f"[FLOW] _analyze_learning_status 完成，返回结果: {type(result)}")
            return result
            
        except Exception as e:
            logger.error(f'分析学习状态失败: {str(e)}')
            raise
    
    def _get_learning_progress(self, user_id: str) -> Dict[str, Any]:
        """获取学习进度数据"""
        def query_progress():
            try:
                # 统计视频观看进度
                video_progress = db.session.query(
                    func.count(Video.id).label('total_videos'),
                    func.count(UserVideoProgress.id).label('watched_videos')
                ).outerjoin(
                    UserVideoProgress,
                    and_(
                        UserVideoProgress.video_id == Video.id,
                        UserVideoProgress.user_id == user_id,
                        UserVideoProgress.progress >= 0.9  # 90%以上算完成
                    )
                ).first()
                
                # 统计文档学习进度
                doc_progress = db.session.query(
                    func.count(Document.id).label('total_docs'),
                    func.count(DocumentProgress.id).label('read_docs')
                ).outerjoin(
                    DocumentProgress,
                    and_(
                        DocumentProgress.document_id == Document.id,
                        DocumentProgress.user_id == user_id
                    )
                ).first()
                
                # 统计作业完成情况
                assignment_stats = db.session.query(
                    func.count(Assignment.id).label('total_assignments'),
                    func.count(StudentAnswer.id).label('submitted_assignments')
                ).outerjoin(
                    StudentAnswer,
                    and_(
                        StudentAnswer.assignment_id == Assignment.id,
                        StudentAnswer.student_id == user_id
                    )
                ).first()
                
                return {
                    'video_progress': {
                        'total': video_progress.total_videos or 0,
                        'completed': video_progress.watched_videos or 0,
                        'percentage': round(video_progress.watched_videos / video_progress.total_videos * 100, 1) if video_progress.total_videos else 0
                    },
                    'document_progress': {
                        'total': doc_progress.total_docs or 0,
                        'completed': doc_progress.read_docs or 0,
                        'percentage': round(doc_progress.read_docs / doc_progress.total_docs * 100, 1) if doc_progress.total_docs else 0
                    },
                    'assignment_progress': {
                        'total': assignment_stats.total_assignments or 0,
                        'completed': assignment_stats.submitted_assignments or 0,
                        'percentage': round(assignment_stats.submitted_assignments / assignment_stats.total_assignments * 100, 1) if assignment_stats.total_assignments else 0
                    }
                }
                
            except Exception as e:
                logger.error(f'获取学习进度失败: {str(e)}')
                raise
        
        return self._execute_with_app_context(query_progress)
    
    def _analyze_knowledge_points(self, user_id: str) -> Tuple[List[Dict], List[Dict]]:
        """分析最强和最弱知识点"""
        try:
            # 获取所有知识点掌握度记录
            mastery_records = KnowledgePointMastery.query.filter_by(user_id=user_id).all()
            
            # 按掌握度排序
            sorted_records = sorted(mastery_records, key=lambda x: x.mastery_level, reverse=True)
            
            # 获取知识点详细信息
            strongest = []
            weakest = []
            
            # 提取前5个最强知识点
            for record in sorted_records[:5]:
                keyword = Keyword.query.get(record.keyword_id)
                if keyword:
                    strongest.append({
                        'keyword_id': keyword.id,
                        'name': keyword.name,
                        'mastery_level': record.mastery_level,
                        'last_updated': record.last_updated
                    })
            
            # 提取后5个最弱知识点
            for record in sorted_records[-5:]:
                keyword = Keyword.query.get(record.keyword_id)
                if keyword:
                    weakest.append({
                        'keyword_id': keyword.id,
                        'name': keyword.name,
                        'mastery_level': record.mastery_level,
                        'last_updated': record.last_updated
                    })
            
            return strongest, weakest
            
        except Exception as e:
            logger.error(f'分析知识点强弱失败: {str(e)}')
            raise
            
    def _get_skill_gaps_and_recommendations(self, user_id: str) -> str:
        """获取技能缺口和任务推荐"""
        try:
            # 获取个性化学习路径推荐
            # 设置force_refresh=False以使用缓存(如果有)
            recommendations_data = personalized_recommendation_service.get_personalized_learning_path(
                user_id=user_id, limit=3, force_refresh=False
            )
            
            if not recommendations_data or not recommendations_data.get('learning_path_recommendations'):
                return "暂无足够的学习数据来分析技能缺口和生成推荐。建议学生多完成一些练习和视频学习。"
                
            recommendations = recommendations_data['learning_path_recommendations']
            
            result_str = ""
            for i, rec in enumerate(recommendations, 1):
                # source_keyword是已掌握的，recommended_keyword是需要学习的(技能缺口)
                source_name = rec.get('source_keyword_name', '基础知识')
                target_name = rec.get('recommended_keyword_name', '新知识点')
                reason = rec.get('recommendation_reason', '建议学习以完善知识体系')
                
                result_str += f"[{i}] 鉴于已掌握「{source_name}」，发现「{target_name}」方面存在技能缺口。\n"
                result_str += f"    建议: {reason}\n"
                
                # 添加具体好处
                benefits = rec.get('learning_benefits', [])
                if benefits:
                    result_str += f"    预期收益: {', '.join(benefits[:2])}\n"
                    
                # 检查可用资源
                resources = rec.get('learning_resources', {})
                if resources:
                    res_str = []
                    if resources.get('videos', 0) > 0:
                        res_str.append(f"{resources['videos']}个视频")
                    if resources.get('documents', 0) > 0:
                        res_str.append(f"{resources['documents']}个文档")
                    if resources.get('questions', 0) > 0:
                        res_str.append(f"{resources['questions']}道练习")
                        
                    if res_str:
                        result_str += f"    可用相关学习资源: {', '.join(res_str)}\n"
            
            return result_str
            
        except Exception as e:
            logger.error(f'获取技能缺口和推荐失败: {str(e)}')
            return f"获取推荐信息时出现问题: {str(e)}"
    
    def _generate_learning_advice(self, user_id: str,
                                strongest_points: List[Dict],
                                weakest_points: List[Dict],
                                progress_data: Dict) -> str:
        """生成AI学习建议"""
        try:
            # 构建提示信息
            prompt = f"""作为一个教育顾问，请根据以下学生的学习数据生成个性化的学习建议：
            
            1. 最擅长的知识点：
            {', '.join(point['name'] for point in strongest_points)}
            
            2. 最薄弱的知识点：
            {', '.join(point['name'] for point in weakest_points)}
            
            3. 学习进度：
            - 视频完成度：{progress_data['video_progress']['percentage']}
            - 文档阅读完成度：{progress_data['document_progress']['percentage']}
            - 作业提交完成度：{progress_data['assignment_progress']['percentage']}
            
            请提供具体的学习建议，包括：
            1. 如何巩固已掌握的知识点
            2. 如何提高薄弱知识点的掌握程度
            3. 学习进度的改进建议
            """
            
            # 调用LLM生成建议
            advice = self.llm_service.generate_response(prompt)
            
            return advice
            
        except Exception as e:
            logger.error(f'生成学习建议失败: {str(e)}')
            raise
    
    
    def get_display_info(self) -> Dict[str, Any]:
        """获取工具展示信息"""
        return {
            "tool_name": "学习状态分析",
            "tool_icon": "mdi-school",
            "tool_color": "success",
            "description": "分析学生的学习情况，提供进度统计、知识点分析和个性化建议。学生可查看自己的情况，教师可查看任一学生的情况。",
            "context": {
                "supports_student_identifier": True,
                "supports_name_query": True,
                "role_based_access": True,
                "analysis_types": ["progress", "mastery", "advice"]
            },
            "status_message": "准备分析学习状态..."
        }
    
    def _resolve_student_id(self, student_identifier: str) -> Optional[str]:
        """解析学生标识符，返回学生ID"""
        if not student_identifier:
            return None
        
        # 如果是"我"或"自己"，返回当前用户ID
        if student_identifier.lower() in ['我', '自己', 'me', 'myself']:
            return self.user_id
        
        def query_student():
            from models.models import Users
            import uuid
            
            # 先尝试作为UUID查询
            try:
                student_uuid = uuid.UUID(student_identifier)
                student = Users.query.filter_by(
                    id=student_uuid, 
                    role='student', 
                    is_deleted=False
                ).first()
                if student:
                    return str(student.id)
            except ValueError:
                pass
            
            # 如果不是有效UUID，尝试作为用户名查找
            student = Users.query.filter(
                Users.username.ilike(f"%{student_identifier}%"),
                Users.role == 'student',
                Users.is_deleted == False
            ).first()
            
            return str(student.id) if student else None
        
        return self._execute_with_app_context(query_student)