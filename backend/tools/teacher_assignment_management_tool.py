#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teacher Assignment Management Tool
Provides functionality for teachers to manage assignments intelligently.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_, desc, asc, func
from datetime import datetime, timedelta
from models.models import db, Assignment, Question, StudentAnswer, Course, Users, StudentCourseEnrollment
from .base_tool import BaseTool
from .permission_utils import get_user_role
from services.llm_service import LLMService
from services.assignment_grading_service import AssignmentGradingService
import logging

logger = logging.getLogger(__name__)

class TeacherAssignmentManagementInput(BaseModel):
    """教师作业管理工具的输入参数模型"""
    action: str = Field(description="操作类型：'list'(列出作业), 'analyze'(分析作业), 'suggest'(智能布置建议), 'grade_stats'(批改统计)")
    course_id: Optional[str] = Field(default=None, description="课程ID（可选）")
    assignment_id: Optional[str] = Field(default=None, description="作业ID（用于分析特定作业）")

class TeacherAssignmentManagementTool(BaseTool):
    """教师作业管理工具类"""
    
    name = "teacher_assignment_management"
    description = "教师作业管理工具，支持智能布置、自动批改、数据分析。可以列出作业、分析作业完成情况、获取智能布置建议、查看批改统计等。"
    
    def __init__(self, user_id: str = None):
        super().__init__(user_id=user_id)
        self.llm_service = LLMService()
        self.grading_service = AssignmentGradingService()
    
    def search(self, action: str, course_id: Optional[str] = None, assignment_id: Optional[str] = None) -> str:
        """执行作业管理操作
        
        Args:
            action: 操作类型
            course_id: 课程ID（可选）
            assignment_id: 作业ID（可选）
            
        Returns:
            操作结果信息
        """
        try:
            # 添加工具启动通知
            self._notify_tool_start(self.get_display_info())
            
            print(f"[FLOW] ===== TeacherAssignmentManagementTool.search 开始执行 =====")
            print(f"[FLOW] 参数 - action: '{action}', course_id: '{course_id}', assignment_id: '{assignment_id}'")
            print(f"[FLOW] 当前用户ID: {self.user_id}")
            
            if not self.user_id:
                return "无法获取用户信息，请先登录"
            
            # 权限检查：确保是教师
            user_role = get_user_role(self.user_id)
            if user_role != 'teacher':
                return "只有教师可以使用作业管理功能"
            
            # 根据操作类型执行相应功能
            def execute_action():
                if action == 'list':
                    return self._list_assignments(course_id)
                elif action == 'analyze':
                    return self._analyze_assignment(assignment_id)
                elif action == 'suggest':
                    return self._suggest_assignment_creation(course_id)
                elif action == 'grade_stats':
                    return self._get_grading_statistics(course_id, assignment_id)
                else:
                    return f"不支持的操作类型: {action}。支持的操作: list, analyze, suggest, grade_stats"
            
            result = self._execute_with_app_context(execute_action)
            
            # 通知工具执行结果
            self._notify_tool_result({
                "success": True,
                "message": f"作业管理操作 '{action}' 完成",
                "action": action,
                "course_id": course_id,
                "assignment_id": assignment_id
            })
            
            return result
            
        except Exception as e:
            error_msg = f'作业管理操作失败: {str(e)}'
            logger.error(error_msg)
            self._notify_tool_result({
                "success": False,
                "message": error_msg
            })
            return error_msg
    
    def _list_assignments(self, course_id: Optional[str] = None) -> str:
        """列出教师的作业"""
        try:
            query = db.session.query(
                Assignment.id,
                Assignment.title,
                Assignment.status,
                Assignment.due_date,
                Assignment.publish_time,
                Course.name.label('course_name'),
                func.count(Question.id).label('question_count')
            ).join(
                Course, Assignment.course_id == Course.id
            ).outerjoin(
                Question, Assignment.id == Question.assignment_id
            ).filter(
                Assignment.teacher_id == self.user_id,
                Assignment.is_deleted == False
            )
            
            if course_id:
                query = query.filter(Assignment.course_id == course_id)
            
            assignments = query.group_by(
                Assignment.id, Assignment.title, Assignment.status,
                Assignment.due_date, Assignment.publish_time, Course.name
            ).order_by(desc(Assignment.create_time)).all()
            
            if not assignments:
                return "您暂无作业" + (f"（课程: {course_id}）" if course_id else "")
            
            result_text = f"📋 您的作业列表"
            if course_id:
                result_text += f"（课程: {course_id}）"
            result_text += f"：\n\n"
            
            for i, assignment in enumerate(assignments, 1):
                status_emoji = {
                    'draft': '📝',
                    'published': '📢',
                    'closed': '🔒'
                }.get(assignment.status, '❓')
                
                result_text += f"{i}. {status_emoji} **{assignment.title}**\n"
                result_text += f"   课程: {assignment.course_name}\n"
                result_text += f"   状态: {assignment.status}\n"
                result_text += f"   题目数量: {assignment.question_count}题\n"
                
                if assignment.due_date:
                    due_date_str = assignment.due_date.strftime('%Y-%m-%d %H:%M')
                    if assignment.due_date < datetime.now():
                        result_text += f"   截止时间: {due_date_str} ⏰已过期\n"
                    else:
                        result_text += f"   截止时间: {due_date_str}\n"
                
                if assignment.publish_time:
                    publish_time_str = assignment.publish_time.strftime('%Y-%m-%d %H:%M')
                    result_text += f"   发布时间: {publish_time_str}\n"
                
                result_text += "\n"
            
            return result_text
            
        except Exception as e:
            logger.error(f'列出作业失败: {str(e)}')
            raise
    
    def _analyze_assignment(self, assignment_id: Optional[str] = None) -> str:
        """分析作业完成情况"""
        try:
            if not assignment_id:
                return "请提供要分析的作业ID"
            
            # 获取作业基本信息
            assignment = db.session.query(Assignment).filter(
                Assignment.id == assignment_id,
                Assignment.teacher_id == self.user_id,
                Assignment.is_deleted == False
            ).first()
            
            if not assignment:
                return f"未找到作业 {assignment_id} 或您没有权限查看"
            
            # 获取课程注册学生数
            enrolled_students = db.session.query(StudentCourseEnrollment).join(
                Users, StudentCourseEnrollment.student_id == Users.id
            ).filter(
                StudentCourseEnrollment.course_id == assignment.course_id,
                Users.is_deleted == False
            ).count()
            
            # 获取作业题目数
            question_count = db.session.query(Question).filter(
                Question.assignment_id == assignment_id
            ).count()
            
            # 获取学生答题情况
            submitted_students = db.session.query(
                func.count(func.distinct(StudentAnswer.student_id))
            ).filter(
                StudentAnswer.assignment_id == assignment_id
            ).scalar() or 0
            
            # 获取平均分
            avg_score = db.session.query(
                func.avg(StudentAnswer.score)
            ).filter(
                StudentAnswer.assignment_id == assignment_id,
                StudentAnswer.score.isnot(None)
            ).scalar() or 0
            
            # 获取完成率
            completion_rate = (submitted_students / enrolled_students * 100) if enrolled_students > 0 else 0
            
            # 获取各题目完成情况
            question_stats = db.session.query(
                Question.id,
                Question.content,
                Question.type,
                func.count(StudentAnswer.id).label('answer_count'),
                func.avg(StudentAnswer.score).label('avg_score')
            ).outerjoin(
                StudentAnswer, and_(
                    StudentAnswer.question_id == Question.id,
                    StudentAnswer.assignment_id == assignment_id
                )
            ).filter(
                Question.assignment_id == assignment_id
            ).group_by(Question.id, Question.content, Question.type).all()
            
            result_text = f"📊 作业《{assignment.title}》分析报告：\n\n"
            result_text += f"📈 **基本统计**：\n"
            result_text += f"- 注册学生数：{enrolled_students}人\n"
            result_text += f"- 已提交学生数：{submitted_students}人\n"
            result_text += f"- 完成率：{completion_rate:.1f}%\n"
            result_text += f"- 题目总数：{question_count}题\n"
            result_text += f"- 平均分：{avg_score:.1f}分\n\n"
            
            if question_stats:
                result_text += f"📝 **各题完成情况**：\n"
                for i, stat in enumerate(question_stats, 1):
                    question_completion = (stat.answer_count / enrolled_students * 100) if enrolled_students > 0 else 0
                    result_text += f"{i}. {stat.type}题 - 完成率: {question_completion:.1f}%, 平均分: {stat.avg_score or 0:.1f}\n"
                    result_text += f"   题目: {stat.content[:50]}{'...' if len(stat.content) > 50 else ''}\n"
            
            # 截止时间分析
            if assignment.due_date:
                if assignment.due_date < datetime.now():
                    days_overdue = (datetime.now() - assignment.due_date).days
                    result_text += f"\n⏰ **时间状态**：已过期 {days_overdue} 天"
                else:
                    days_left = (assignment.due_date - datetime.now()).days
                    result_text += f"\n⏰ **时间状态**：还有 {days_left} 天到期"
            
            return result_text
            
        except Exception as e:
            logger.error(f'分析作业失败: {str(e)}')
            raise
    
    def _suggest_assignment_creation(self, course_id: Optional[str] = None) -> str:
        """智能布置作业建议"""
        try:
            if not course_id:
                return "请提供课程ID以获取智能布置建议"
            
            # 获取课程信息
            course = db.session.query(Course).filter(
                Course.id == course_id,
                Course.is_deleted == False
            ).first()
            
            if not course:
                return f"未找到课程 {course_id}"
            
            # 获取课程的知识点
            from models.models import Keyword, VideoKeyword, Video, DocumentKeyword, Document
            
            course_keywords = db.session.query(
                Keyword.name,
                func.count(func.distinct(Video.id)).label('video_count'),
                func.count(func.distinct(Document.id)).label('doc_count')
            ).outerjoin(
                VideoKeyword, Keyword.id == VideoKeyword.keyword_id
            ).outerjoin(
                Video, and_(
                    VideoKeyword.video_id == Video.id,
                    Video.course_id == course_id
                )
            ).outerjoin(
                DocumentKeyword, Keyword.id == DocumentKeyword.keyword_id
            ).outerjoin(
                Document, and_(
                    DocumentKeyword.document_id == Document.id,
                    Document.course_id == course_id
                )
            ).group_by(Keyword.id, Keyword.name).limit(10).all()
            
            # 获取最近的作业情况
            recent_assignments = db.session.query(Assignment).filter(
                Assignment.course_id == course_id,
                Assignment.teacher_id == self.user_id,
                Assignment.is_deleted == False
            ).order_by(desc(Assignment.create_time)).limit(3).all()
            
            # 构建AI建议提示
            prompt = f"""作为一名教师助手，请为课程《{course.name}》提供智能作业布置建议。

课程信息：
- 课程名称：{course.name}
- 课程描述：{course.description or '无'}

主要知识点：
{chr(10).join([f"- {kw.name} (视频:{kw.video_count}个, 文档:{kw.doc_count}个)" for kw in course_keywords[:5]])}

最近作业情况：
{chr(10).join([f"- 《{a.title}》 (状态:{a.status}, 截止:{a.due_date.strftime('%Y-%m-%d') if a.due_date else '无'})" for a in recent_assignments])}

请提供以下建议：
1. 推荐的作业主题和难度
2. 建议的题目类型和数量
3. 合适的截止时间
4. 应该覆盖的知识点
5. 作业设计的注意事项

请用中文回答，内容要具体实用。"""
            
            # 调用LLM生成建议
            try:
                ai_suggestions = self.llm_service.get_completion(prompt)
            except Exception as e:
                logger.warning(f"AI建议生成失败: {e}")
                ai_suggestions = "AI建议服务暂时不可用，请稍后再试。"
            
            result_text = f"🎯 课程《{course.name}》智能作业布置建议：\n\n"
            result_text += f"📚 **课程概况**：\n"
            result_text += f"- 主要知识点：{len(course_keywords)}个\n"
            result_text += f"- 最近作业数：{len(recent_assignments)}个\n\n"
            
            result_text += f"🤖 **AI智能建议**：\n"
            result_text += ai_suggestions
            
            if course_keywords:
                result_text += f"\n\n📋 **可选知识点**：\n"
                for kw in course_keywords[:5]:
                    result_text += f"- {kw.name} (资源丰富度: 视频{kw.video_count}+文档{kw.doc_count})\n"
            
            return result_text
            
        except Exception as e:
            logger.error(f'生成作业建议失败: {str(e)}')
            raise
    
    def _get_grading_statistics(self, course_id: Optional[str] = None, assignment_id: Optional[str] = None) -> str:
        """获取批改统计"""
        try:
            # 基础查询
            query = db.session.query(
                Assignment.id,
                Assignment.title,
                Course.name.label('course_name'),
                func.count(StudentAnswer.id).label('total_answers'),
                func.count(func.distinct(StudentAnswer.student_id)).label('student_count'),
                func.avg(StudentAnswer.score).label('avg_score'),
                func.max(StudentAnswer.score).label('max_score'),
                func.min(StudentAnswer.score).label('min_score')
            ).join(
                Course, Assignment.course_id == Course.id
            ).outerjoin(
                StudentAnswer, StudentAnswer.assignment_id == Assignment.id
            ).filter(
                Assignment.teacher_id == self.user_id,
                Assignment.is_deleted == False
            )
            
            if course_id:
                query = query.filter(Assignment.course_id == course_id)
            
            if assignment_id:
                query = query.filter(Assignment.id == assignment_id)
            
            stats = query.group_by(
                Assignment.id, Assignment.title, Course.name
            ).order_by(desc(Assignment.create_time)).all()
            
            if not stats:
                return "没有找到相关的批改统计数据"
            
            result_text = f"📊 批改统计报告：\n\n"
            
            for i, stat in enumerate(stats, 1):
                result_text += f"{i}. **{stat.title}** ({stat.course_name})\n"
                result_text += f"   参与学生：{stat.student_count or 0}人\n"
                result_text += f"   答题总数：{stat.total_answers or 0}题次\n"
                
                if stat.avg_score is not None:
                    result_text += f"   平均分：{stat.avg_score:.1f}分\n"
                    result_text += f"   最高分：{stat.max_score or 0:.1f}分\n"
                    result_text += f"   最低分：{stat.min_score or 0:.1f}分\n"
                else:
                    result_text += f"   暂无评分数据\n"
                
                result_text += "\n"
            
            # 总体统计
            total_students = sum(stat.student_count or 0 for stat in stats)
            total_answers = sum(stat.total_answers or 0 for stat in stats)
            
            result_text += f"📈 **总体概况**：\n"
            result_text += f"- 作业总数：{len(stats)}个\n"
            result_text += f"- 参与学生总计：{total_students}人次\n"
            result_text += f"- 答题总计：{total_answers}题次\n"
            
            return result_text
            
        except Exception as e:
            logger.error(f'获取批改统计失败: {str(e)}')
            raise
    
    def get_display_info(self) -> Dict[str, Any]:
        """获取工具展示信息"""
        return {
            "tool_name": "作业管理助手",
            "tool_icon": "mdi-clipboard-check",
            "tool_color": "warning",
            "description": "智能作业管理工具，支持作业列表查看、完成情况分析、智能布置建议和批改统计。",
            "context": {
                "supports_assignment_list": True,
                "supports_analysis": True,
                "supports_ai_suggestions": True,
                "supports_grading_stats": True,
                "teacher_only": True
            },
            "status_message": "准备执行作业管理操作..."
        }
