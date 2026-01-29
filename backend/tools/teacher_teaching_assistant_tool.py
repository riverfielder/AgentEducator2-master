#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teacher Teaching Assistant Tool
Provides learning analytics for students and classes.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy import and_, or_, desc, asc, func, case
from datetime import datetime, timedelta
from models.models import (
    db, Course, Users, StudentCourseEnrollment, UserVideoProgress, 
    DocumentProgress, KnowledgePointMastery, Assignment, StudentAnswer,
    Video, Document, Keyword
)
from .base_tool import BaseTool
from .permission_utils import get_user_role
from services.llm_service import LLMService
from services.mastery_calculator import MasteryCalculator
import logging

logger = logging.getLogger(__name__)

class TeacherTeachingAssistantInput(BaseModel):
    """教师教学辅助工具的输入参数模型"""
    analysis_type: str = Field(description="分析类型：'student'(单个学生分析), 'class'(班级分析), 'course'(课程分析), 'compare'(对比分析)")
    course_id: str = Field(default=None, description="课程ID")
    student_id: Optional[str] = Field(default=None, description="学生ID（用于单个学生分析）")
    time_range: Optional[str] = Field(default="30", description="时间范围（天数，默认30天）")

class TeacherTeachingAssistantTool(BaseTool):
    """教师教学辅助工具类"""
    
    name = "teacher_teaching_assistant"
    description = "教师教学辅助工具，提供学生和班级的学情分析。支持单个学生分析、班级整体分析、课程进度分析和对比分析等功能。"
    
    def __init__(self, user_id: str = None):
        super().__init__(user_id=user_id)
        self.llm_service = LLMService()
        self.mastery_calculator = MasteryCalculator()
    
    def search(self, analysis_type: str, course_id: Optional[str] = None, 
               student_id: Optional[str] = None, time_range: Optional[str] = "30") -> str:
        """执行教学分析操作
        
        Args:
            analysis_type: 分析类型
            course_id: 课程ID
            student_id: 学生ID
            time_range: 时间范围（天数）
            
        Returns:
            分析结果信息
        """
        try:
            # 添加工具启动通知
            self._notify_tool_start(self.get_display_info())
            
            print(f"[FLOW] ===== TeacherTeachingAssistantTool.search 开始执行 =====")
            print(f"[FLOW] 参数 - analysis_type: '{analysis_type}', course_id: '{course_id}', student_id: '{student_id}'")
            print(f"[FLOW] 当前用户ID: {self.user_id}")
            
            if not self.user_id:
                return "无法获取用户信息，请先登录"
            
            # 权限检查：确保是教师
            user_role = get_user_role(self.user_id)
            if user_role != 'teacher':
                return "只有教师可以使用教学辅助功能"
            
            # 解析时间范围
            try:
                days = int(time_range) if time_range else 30
                start_date = datetime.now() - timedelta(days=days)
            except ValueError:
                days = 30
                start_date = datetime.now() - timedelta(days=30)
            
            # 根据分析类型执行相应功能
            def execute_analysis():
                if analysis_type == 'student':
                    return self._analyze_student(student_id, course_id, start_date)
                elif analysis_type == 'class':
                    return self._analyze_class(course_id, start_date)
                elif analysis_type == 'course':
                    return self._analyze_course(course_id, start_date)
                elif analysis_type == 'compare':
                    return self._compare_analysis(course_id, start_date)
                else:
                    return f"不支持的分析类型: {analysis_type}。支持的类型: student, class, course, compare"
            
            result = self._execute_with_app_context(execute_analysis)
            
            # 通知工具执行结果
            self._notify_tool_result({
                "success": True,
                "message": f"教学分析 '{analysis_type}' 完成",
                "analysis_type": analysis_type,
                "course_id": course_id,
                "student_id": student_id,
                "time_range_days": days
            })
            
            return result
            
        except Exception as e:
            error_msg = f'教学分析失败: {str(e)}'
            logger.error(error_msg)
            self._notify_tool_result({
                "success": False,
                "message": error_msg
            })
            return error_msg
    
    def _analyze_student(self, student_id: Optional[str], course_id: Optional[str], start_date: datetime) -> str:
        """分析单个学生的学情"""
        try:
            if not student_id:
                return "请提供要分析的学生ID"
            
            # 获取学生基本信息
            student = db.session.query(Users).filter(
                Users.id == student_id,
                Users.role == 'student',
                Users.is_deleted == False
            ).first()
            
            if not student:
                return f"未找到学生 {student_id}"
            
            # 获取学生注册的课程（如果指定了course_id则只分析该课程）
            enrollment_query = db.session.query(
                StudentCourseEnrollment.course_id,
                Course.name.label('course_name')
            ).join(
                Course, StudentCourseEnrollment.course_id == Course.id
            ).filter(
                StudentCourseEnrollment.student_id == student_id
            )
            
            if course_id:
                enrollment_query = enrollment_query.filter(StudentCourseEnrollment.course_id == course_id)
            
            enrollments = enrollment_query.all()
            
            if not enrollments:
                course_msg = f"课程 {course_id}" if course_id else "任何课程"
                return f"学生 {student.username} 没有注册 {course_msg}"
            
            result_text = f"👨‍🎓 学生《{student.username}》学情分析报告：\n\n"
            
            for enrollment in enrollments:
                course_name = enrollment.course_name
                course_id_current = enrollment.course_id
                
                result_text += f"📚 **{course_name}** 学习情况：\n"
                
                # 视频学习进度
                video_progress = db.session.query(
                    func.count(UserVideoProgress.id).label('watched_count'),
                    func.avg(UserVideoProgress.progress).label('avg_progress'),
                    func.count(Video.id).label('total_videos')
                ).select_from(Video).outerjoin(
                    UserVideoProgress, and_(
                        UserVideoProgress.video_id == Video.id,
                        UserVideoProgress.user_id == student_id
                    )
                ).filter(
                    Video.course_id == course_id_current,
                    Video.is_deleted == False
                ).first()
                
                watched_count = video_progress.watched_count or 0
                total_videos = video_progress.total_videos or 0
                avg_progress = video_progress.avg_progress or 0
                
                result_text += f"  🎥 视频学习：已观看 {watched_count}/{total_videos} 个视频，平均进度 {avg_progress:.1%}\n"
                
                # 文档学习进度
                doc_progress = db.session.query(
                    func.count(DocumentProgress.id).label('read_count'),
                    func.avg(DocumentProgress.progress).label('avg_progress'),
                    func.count(Document.id).label('total_docs')
                ).select_from(Document).outerjoin(
                    DocumentProgress, and_(
                        DocumentProgress.document_id == Document.id,
                        DocumentProgress.user_id == student_id
                    )
                ).filter(
                    Document.course_id == course_id_current,
                    Document.is_deleted == False
                ).first()
                
                read_count = doc_progress.read_count or 0
                total_docs = doc_progress.total_docs or 0
                doc_avg_progress = doc_progress.avg_progress or 0
                
                result_text += f"  📖 文档学习：已阅读 {read_count}/{total_docs} 个文档，平均进度 {doc_avg_progress:.1%}\n"
                
                # 作业完成情况
                assignment_stats = db.session.query(
                    func.count(func.distinct(Assignment.id)).label('total_assignments'),
                    func.count(func.distinct(StudentAnswer.assignment_id)).label('submitted_assignments'),
                    func.avg(StudentAnswer.score).label('avg_score')
                ).select_from(Assignment).outerjoin(
                    StudentAnswer, and_(
                        StudentAnswer.assignment_id == Assignment.id,
                        StudentAnswer.student_id == student_id
                    )
                ).filter(
                    Assignment.course_id == course_id_current,
                    Assignment.is_deleted == False
                ).first()
                
                total_assignments = assignment_stats.total_assignments or 0
                submitted_assignments = assignment_stats.submitted_assignments or 0
                avg_score = assignment_stats.avg_score or 0
                
                result_text += f"  📝 作业情况：已提交 {submitted_assignments}/{total_assignments} 个作业，平均分 {avg_score:.1f}\n"
                
                # 知识点掌握情况
                mastery_stats = db.session.query(
                    func.count(KnowledgePointMastery.id).label('total_masteries'),
                    func.avg(KnowledgePointMastery.mastery_level).label('avg_mastery')
                ).join(
                    Keyword, KnowledgePointMastery.keyword_id == Keyword.id
                ).filter(
                    KnowledgePointMastery.user_id == student_id
                ).first()
                
                total_masteries = mastery_stats.total_masteries or 0
                avg_mastery = mastery_stats.avg_mastery or 0
                
                result_text += f"  🧠 知识掌握：已学习 {total_masteries} 个知识点，平均掌握度 {avg_mastery:.1%}\n\n"
            
            # 最近活动
            recent_activities = []
            
            # 最近视频观看
            recent_videos = db.session.query(
                UserVideoProgress.update_time,
                Video.title,
                Course.name.label('course_name')
            ).join(
                Video, UserVideoProgress.video_id == Video.id
            ).join(
                Course, Video.course_id == Course.id
            ).filter(
                UserVideoProgress.user_id == student_id,
                UserVideoProgress.update_time >= start_date
            ).order_by(desc(UserVideoProgress.update_time)).limit(5).all()
            
            if recent_videos:
                result_text += f"🕒 **最近活动**：\n"
                for activity in recent_videos:
                    time_str = activity.update_time.strftime('%m-%d %H:%M')
                    result_text += f"  {time_str} - 观看视频《{activity.title[:30]}...》({activity.course_name})\n"
            
            return result_text
            
        except Exception as e:
            logger.error(f'分析学生学情失败: {str(e)}')
            raise
    
    def _analyze_class(self, course_id: Optional[str], start_date: datetime) -> str:
        """分析班级整体学情"""
        try:
            if not course_id:
                return "请提供要分析的课程ID"
            
            # 获取课程信息
            course = db.session.query(Course).filter(
                Course.id == course_id,
                Course.is_deleted == False
            ).first()
            
            if not course:
                return f"未找到课程 {course_id}"
            
            # 获取注册学生
            students = db.session.query(
                Users.id,
                Users.username
            ).join(
                StudentCourseEnrollment, StudentCourseEnrollment.student_id == Users.id
            ).filter(
                StudentCourseEnrollment.course_id == course_id,
                Users.role == 'student',
                Users.is_deleted == False
            ).all()
            
            if not students:
                return f"课程《{course.name}》暂无注册学生"
            
            result_text = f"🏫 课程《{course.name}》班级学情分析：\n\n"
            result_text += f"👥 **班级概况**：\n"
            result_text += f"- 注册学生：{len(students)}人\n\n"
            
            # 整体学习进度统计
            video_stats = db.session.query(
                func.count(func.distinct(Video.id)).label('total_videos'),
                func.count(UserVideoProgress.id).label('total_watches'),
                func.avg(UserVideoProgress.progress).label('avg_progress')
            ).select_from(Video).outerjoin(
                UserVideoProgress, and_(
                    UserVideoProgress.video_id == Video.id,
                    UserVideoProgress.user_id.in_([s.id for s in students])
                )
            ).filter(
                Video.course_id == course_id,
                Video.is_deleted == False
            ).first()
            
            total_videos = video_stats.total_videos or 0
            total_watches = video_stats.total_watches or 0
            avg_video_progress = video_stats.avg_progress or 0
            
            result_text += f"🎥 **视频学习统计**：\n"
            result_text += f"- 课程视频总数：{total_videos}个\n"
            result_text += f"- 学生观看次数：{total_watches}次\n"
            result_text += f"- 平均观看进度：{avg_video_progress:.1%}\n"
            result_text += f"- 人均观看视频：{total_watches/len(students):.1f}个\n\n"
            
            # 作业完成统计
            assignment_stats = db.session.query(
                func.count(func.distinct(Assignment.id)).label('total_assignments'),
                func.count(StudentAnswer.id).label('total_submissions'),
                func.avg(StudentAnswer.score).label('avg_score')
            ).select_from(Assignment).outerjoin(
                StudentAnswer, and_(
                    StudentAnswer.assignment_id == Assignment.id,
                    StudentAnswer.student_id.in_([s.id for s in students])
                )
            ).filter(
                Assignment.course_id == course_id,
                Assignment.is_deleted == False
            ).first()
            
            total_assignments = assignment_stats.total_assignments or 0
            total_submissions = assignment_stats.total_submissions or 0
            class_avg_score = assignment_stats.avg_score or 0
            
            result_text += f"📝 **作业完成统计**：\n"
            result_text += f"- 课程作业总数：{total_assignments}个\n"
            result_text += f"- 学生提交次数：{total_submissions}次\n"
            result_text += f"- 班级平均分：{class_avg_score:.1f}分\n"
            
            if total_assignments > 0:
                avg_completion_rate = total_submissions / (total_assignments * len(students)) * 100
                result_text += f"- 平均完成率：{avg_completion_rate:.1f}%\n"
            
            result_text += "\n"
            
            # 学习活跃度分析
            active_students = db.session.query(
                func.count(func.distinct(UserVideoProgress.user_id))
            ).filter(
                UserVideoProgress.user_id.in_([s.id for s in students]),
                UserVideoProgress.update_time >= start_date
            ).scalar() or 0
            
            result_text += f"📈 **学习活跃度**（最近{(datetime.now() - start_date).days}天）：\n"
            result_text += f"- 活跃学生：{active_students}/{len(students)}人 ({active_students/len(students)*100:.1f}%)\n"
            
            # 成绩分布
            score_distribution = db.session.query(
                func.count(StudentAnswer.id).label('count'),
                case([
                    (StudentAnswer.score >= 90, '优秀(90+)'),
                    (StudentAnswer.score >= 80, '良好(80-89)'),
                    (StudentAnswer.score >= 70, '中等(70-79)'),
                    (StudentAnswer.score >= 60, '及格(60-69)'),
                ], else_='不及格(<60)').label('grade_range')
            ).join(
                Assignment, StudentAnswer.assignment_id == Assignment.id
            ).filter(
                Assignment.course_id == course_id,
                StudentAnswer.student_id.in_([s.id for s in students]),
                StudentAnswer.score.isnot(None)
            ).group_by('grade_range').all()
            
            if score_distribution:
                result_text += f"\n📊 **成绩分布**：\n"
                for dist in score_distribution:
                    result_text += f"- {dist.grade_range}：{dist.count}人次\n"
            
            return result_text
            
        except Exception as e:
            logger.error(f'分析班级学情失败: {str(e)}')
            raise
    
    def _analyze_course(self, course_id: Optional[str], start_date: datetime) -> str:
        """分析课程进度"""
        try:
            if not course_id:
                return "请提供要分析的课程ID"
            
            course = db.session.query(Course).filter(
                Course.id == course_id,
                Course.is_deleted == False
            ).first()
            
            if not course:
                return f"未找到课程 {course_id}"
            
            result_text = f"📚 课程《{course.name}》进度分析：\n\n"
            
            # 课程资源统计
            video_count = db.session.query(Video).filter(
                Video.course_id == course_id,
                Video.is_deleted == False
            ).count()
            
            doc_count = db.session.query(Document).filter(
                Document.course_id == course_id,
                Document.is_deleted == False
            ).count()
            
            assignment_count = db.session.query(Assignment).filter(
                Assignment.course_id == course_id,
                Assignment.is_deleted == False
            ).count()
            
            result_text += f"📦 **课程资源**：\n"
            result_text += f"- 视频：{video_count}个\n"
            result_text += f"- 文档：{doc_count}个\n"
            result_text += f"- 作业：{assignment_count}个\n\n"
            
            # 学习进度概览
            enrolled_count = db.session.query(StudentCourseEnrollment).join(
                Users, StudentCourseEnrollment.student_id == Users.id
            ).filter(
                StudentCourseEnrollment.course_id == course_id,
                Users.is_deleted == False
            ).count()
            
            # 视频观看情况
            video_engagement = db.session.query(
                Video.title,
                func.count(UserVideoProgress.id).label('watch_count'),
                func.avg(UserVideoProgress.progress).label('avg_progress')
            ).outerjoin(
                UserVideoProgress, UserVideoProgress.video_id == Video.id
            ).filter(
                Video.course_id == course_id,
                Video.is_deleted == False
            ).group_by(Video.id, Video.title).order_by(desc('watch_count')).limit(5).all()
            
            if video_engagement:
                result_text += f"🎥 **热门视频**（观看次数）：\n"
                for i, video in enumerate(video_engagement, 1):
                    watch_rate = (video.watch_count / enrolled_count * 100) if enrolled_count > 0 else 0
                    result_text += f"{i}. {video.title[:30]}... - {video.watch_count}次观看 ({watch_rate:.1f}%), 平均进度{video.avg_progress or 0:.1%}\n"
                result_text += "\n"
            
            # 作业完成情况
            assignment_engagement = db.session.query(
                Assignment.title,
                Assignment.due_date,
                func.count(func.distinct(StudentAnswer.student_id)).label('submission_count')
            ).outerjoin(
                StudentAnswer, StudentAnswer.assignment_id == Assignment.id
            ).filter(
                Assignment.course_id == course_id,
                Assignment.is_deleted == False
            ).group_by(Assignment.id, Assignment.title, Assignment.due_date).order_by(desc('submission_count')).all()
            
            if assignment_engagement:
                result_text += f"📝 **作业完成情况**：\n"
                for assignment in assignment_engagement:
                    completion_rate = (assignment.submission_count / enrolled_count * 100) if enrolled_count > 0 else 0
                    status = ""
                    if assignment.due_date and assignment.due_date < datetime.now():
                        status = " ⏰已截止"
                    result_text += f"- {assignment.title[:30]}... - {assignment.submission_count}/{enrolled_count}人完成 ({completion_rate:.1f}%){status}\n"
                result_text += "\n"
            
            return result_text
            
        except Exception as e:
            logger.error(f'分析课程进度失败: {str(e)}')
            raise
    
    def _compare_analysis(self, course_id: Optional[str], start_date: datetime) -> str:
        """对比分析"""
        try:
            if course_id:
                # 单课程的班级内对比
                return self._compare_students_in_course(course_id, start_date)
            else:
                # 教师所有课程的对比
                return self._compare_teacher_courses(start_date)
        
        except Exception as e:
            logger.error(f'对比分析失败: {str(e)}')
            raise
    
    def _compare_students_in_course(self, course_id: str, start_date: datetime) -> str:
        """对比课程内学生表现"""
        try:
            course = db.session.query(Course).filter(
                Course.id == course_id,
                Course.is_deleted == False
            ).first()
            
            if not course:
                return f"未找到课程 {course_id}"
            
            # 获取学生表现数据
            student_performance = db.session.query(
                Users.id,
                Users.username,
                func.count(func.distinct(UserVideoProgress.video_id)).label('videos_watched'),
                func.avg(UserVideoProgress.progress).label('avg_video_progress'),
                func.count(func.distinct(StudentAnswer.assignment_id)).label('assignments_submitted'),
                func.avg(StudentAnswer.score).label('avg_score')
            ).select_from(Users).join(
                StudentCourseEnrollment, StudentCourseEnrollment.student_id == Users.id
            ).outerjoin(
                UserVideoProgress, and_(
                    UserVideoProgress.user_id == Users.id,
                    UserVideoProgress.update_time >= start_date
                )
            ).outerjoin(
                Video, and_(
                    Video.id == UserVideoProgress.video_id,
                    Video.course_id == course_id
                )
            ).outerjoin(
                StudentAnswer, StudentAnswer.student_id == Users.id
            ).outerjoin(
                Assignment, and_(
                    Assignment.id == StudentAnswer.assignment_id,
                    Assignment.course_id == course_id
                )
            ).filter(
                StudentCourseEnrollment.course_id == course_id,
                Users.role == 'student',
                Users.is_deleted == False
            ).group_by(Users.id, Users.username).order_by(desc('avg_score')).all()
            
            if not student_performance:
                return f"课程《{course.name}》暂无学生数据"
            
            result_text = f"📊 课程《{course.name}》学生对比分析：\n\n"
            result_text += f"排名 | 学生姓名 | 视频观看 | 作业提交 | 平均分\n"
            result_text += f"{'='*50}\n"
            
            for i, perf in enumerate(student_performance[:10], 1):  # 只显示前10名
                videos_watched = perf.videos_watched or 0
                assignments_submitted = perf.assignments_submitted or 0
                avg_score = perf.avg_score or 0
                
                # 添加表现等级
                if avg_score >= 90:
                    grade_emoji = "🏆"
                elif avg_score >= 80:
                    grade_emoji = "🥈"
                elif avg_score >= 70:
                    grade_emoji = "🥉"
                else:
                    grade_emoji = "📚"
                
                result_text += f"{i:2d}. {grade_emoji} {perf.username[:10]:<10} | {videos_watched:2d}个视频 | {assignments_submitted:2d}个作业 | {avg_score:5.1f}分\n"
            
            # 班级统计
            avg_videos = sum(p.videos_watched or 0 for p in student_performance) / len(student_performance)
            avg_assignments = sum(p.assignments_submitted or 0 for p in student_performance) / len(student_performance)
            class_avg_score = sum(p.avg_score or 0 for p in student_performance) / len(student_performance)
            
            result_text += f"\n📈 **班级平均水平**：\n"
            result_text += f"- 平均观看视频：{avg_videos:.1f}个\n"
            result_text += f"- 平均提交作业：{avg_assignments:.1f}个\n"
            result_text += f"- 班级平均分：{class_avg_score:.1f}分\n"
            
            return result_text
            
        except Exception as e:
            logger.error(f'对比课程学生表现失败: {str(e)}')
            raise
    
    def _compare_teacher_courses(self, start_date: datetime) -> str:
        """对比教师的所有课程"""
        try:
            # 获取教师的课程
            courses = db.session.query(Course).filter(
                Course.teacher_id == self.user_id,
                Course.is_deleted == False
            ).all()
            
            if not courses:
                return "您暂无课程数据"
            
            result_text = f"📊 您的课程对比分析：\n\n"
            
            course_stats = []
            for course in courses:
                # 统计每个课程的数据
                student_count = db.session.query(StudentCourseEnrollment).join(
                    Users, StudentCourseEnrollment.student_id == Users.id
                ).filter(
                    StudentCourseEnrollment.course_id == course.id,
                    Users.is_deleted == False
                ).count()
                
                video_engagement = db.session.query(
                    func.count(UserVideoProgress.id)
                ).join(
                    Video, UserVideoProgress.video_id == Video.id
                ).filter(
                    Video.course_id == course.id,
                    UserVideoProgress.update_time >= start_date
                ).scalar() or 0
                
                assignment_submissions = db.session.query(
                    func.count(StudentAnswer.id),
                    func.avg(StudentAnswer.score)
                ).join(
                    Assignment, StudentAnswer.assignment_id == Assignment.id
                ).filter(
                    Assignment.course_id == course.id
                ).first()
                
                submission_count = assignment_submissions[0] or 0
                avg_score = assignment_submissions[1] or 0
                
                course_stats.append({
                    'name': course.name,
                    'student_count': student_count,
                    'video_engagement': video_engagement,
                    'submission_count': submission_count,
                    'avg_score': avg_score,
                    'engagement_rate': video_engagement / student_count if student_count > 0 else 0
                })
            
            # 按平均分排序
            course_stats.sort(key=lambda x: x['avg_score'], reverse=True)
            
            result_text += f"课程名称 | 学生数 | 视频观看 | 作业提交 | 平均分\n"
            result_text += f"{'='*55}\n"
            
            for stat in course_stats:
                result_text += f"{stat['name'][:12]:<12} | {stat['student_count']:3d}人 | {stat['video_engagement']:4d}次 | {stat['submission_count']:4d}次 | {stat['avg_score']:5.1f}分\n"
            
            return result_text
            
        except Exception as e:
            logger.error(f'对比教师课程失败: {str(e)}')
            raise
    
    def get_display_info(self) -> Dict[str, Any]:
        """获取工具展示信息"""
        return {
            "tool_name": "教学辅助分析",
            "tool_icon": "mdi-chart-line",
            "tool_color": "success",
            "description": "教师教学辅助工具，提供学生和班级的全方位学情分析，支持单个学生分析、班级分析、课程分析和对比分析。",
            "context": {
                "supports_student_analysis": True,
                "supports_class_analysis": True,
                "supports_course_analysis": True,
                "supports_comparison": True,
                "teacher_only": True
            },
            "status_message": "准备执行教学分析..."
        }
