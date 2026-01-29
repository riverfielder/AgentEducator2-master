"""
教师端智能助手服务
基于现有的agent_qa_service扩展，提供教师专用的AI助手功能
"""

import traceback
import logging
from typing import List, Dict, Any, Optional

from .agent_qa_service import agent_qa_service
from .llm_service import llm_service

# 创建专门的日志记录器
teacher_agent_logger = logging.getLogger('teacher_agent')
teacher_agent_logger.setLevel(logging.INFO)

class TeacherAgentService:
    """教师端智能助手服务"""
    
    def __init__(self):
        self.base_agent_service = agent_qa_service
        print("[TEACHER_AGENT] 教师端智能助手服务初始化完成")
    
    def create_teacher_agent(self, teacher_id: str, qa_mode: str = 'teacher_general', 
                           references: List[Dict] = None, streaming_callback=None):
        """
        创建教师端专用Agent
        
        Args:
            teacher_id: 教师ID
            qa_mode: 教师端QA模式
            references: 引用的课程、学生等资源
            streaming_callback: 流式回调
        """
        try:
            print(f"[TEACHER_AGENT] 创建教师端Agent: teacher_id={teacher_id}, qa_mode={qa_mode}")
            
            # 构建教师端上下文
            teacher_context = self._build_teacher_context(teacher_id, qa_mode, references)
            
            
            agent_executor, error = self.base_agent_service.create_qa_agent(
                video_context=teacher_context.get('video_context'),
                course_context=teacher_context.get('course_context'),
                document_context=teacher_context.get('document_context'),
                history=teacher_context.get('history'),
                streaming_callback=streaming_callback,
                user_id=teacher_id
            )
            
            if error:
                print(f"[TEACHER_AGENT] ❌ 创建教师端Agent失败: {error}")
                return None, error
            
            # 为Agent添加教师端特定配置
            if agent_executor:
                agent_executor._teacher_id = teacher_id
                agent_executor._qa_mode = qa_mode
                agent_executor._references = references or []
                print(f"[TEACHER_AGENT] ✅ 教师端Agent创建成功")
            
            return agent_executor, None
            
        except Exception as e:
            error_msg = f"创建教师端Agent失败: {str(e)}"
            print(f"[TEACHER_AGENT] ❌ {error_msg}")
            traceback.print_exc()
            return None, error_msg
    
    def _build_teacher_context(self, teacher_id: str, qa_mode: str, references: List[Dict]) -> Dict[str, Any]:
        """
        构建教师端上下文信息
        
        Args:
            teacher_id: 教师ID
            qa_mode: QA模式
            references: 引用资源
            
        Returns:
            包含各种上下文信息的字典
        """
        context = {
            'video_context': '',
            'course_context': '',
            'document_context': '',
            'history': []
        }
        
        try:
            # 根据QA模式构建不同的上下文
            if qa_mode == 'course_analysis':
                context['course_context'] = self._build_course_analysis_context(references)
            elif qa_mode == 'content_analysis':
                context['video_context'] = self._build_content_analysis_context(references)
            elif qa_mode == 'student_insights':
                context['document_context'] = self._build_student_insights_context(references)
            elif qa_mode == 'all':
                # 综合模式：包含所有类型的上下文
                context['course_context'] = self._build_course_analysis_context(references)
                context['video_context'] = self._build_content_analysis_context(references)
                context['document_context'] = self._build_student_insights_context(references)
            
            # 添加教师端通用上下文
            context['teacher_context'] = f"TEACHER_ID:{teacher_id}|QA_MODE:{qa_mode}|ROLE:teacher"
            
            print(f"[TEACHER_AGENT] 构建教师端上下文完成: qa_mode={qa_mode}, references_count={len(references) if references else 0}")
            
        except Exception as e:
            print(f"[TEACHER_AGENT] ⚠️ 构建教师端上下文时出错: {str(e)}")
        
        return context
    
    def _build_course_analysis_context(self, references: List[Dict]) -> str:
        """构建课程分析上下文"""
        if not references:
            return ""
        
        course_refs = [ref for ref in references if ref.get('type') == 'course']
        if not course_refs:
            return ""
        
        try:
            from models.models import Course, Video, db
            
            context_parts = []
            for course_ref in course_refs:
                course_id = course_ref.get('id')
                course = db.session.query(Course).get(course_id)
                
                if course:
                    # 获取基本信息
                    info = f"COURSE_ID:{course.id}|NAME:{course.name}|DESC:{course.description}|STUDENTS:{course.student_count}"
                    
                    # 获取视频统计
                    video_count = db.session.query(Video).filter(Video.course_id == course_id).count()
                    info += f"|VIDEO_COUNT:{video_count}"
                    
                    context_parts.append(info)
            
            return "\\n".join(context_parts)
            
        except Exception as e:
            print(f"[TEACHER_AGENT] ⚠️ 构建课程分析上下文失败: {str(e)}")
            return ""
    
    def _build_content_analysis_context(self, references: List[Dict]) -> str:
        """构建内容分析上下文"""
        if not references:
            return ""
        
        video_refs = [ref for ref in references if ref.get('type') == 'video']
        if not video_refs:
            return ""
        
        try:
            from models.models import Video, VideoSummary, db
            
            context_parts = []
            for video_ref in video_refs:
                video_id = video_ref.get('id')
                video = db.session.query(Video).get(video_id)
                
                if video:
                    info = f"VIDEO_ID:{video.id}|TITLE:{video.title}|VIEW_COUNT:{video.view_count}|COMPLETION_RATE:{video.completion_rate}"
                    
                    # 获取视频摘要
                    summary = db.session.query(VideoSummary).filter(VideoSummary.video_id == video_id).first()
                    if summary:
                        if summary.whole_summary:
                            info += f"|SUMMARY:{summary.whole_summary[:500]}..." # 限制长度
                        if summary.keywords:
                            info += f"|KEYWORDS:{summary.keywords}"
                            
                    context_parts.append(info)
            
            return "\\n".join(context_parts)
            
        except Exception as e:
            print(f"[TEACHER_AGENT] ⚠️ 构建内容分析上下文失败: {str(e)}")
            return ""
    
    def _build_student_insights_context(self, references: List[Dict]) -> str:
        """构建学生洞察上下文"""
        if not references:
            return ""
        
        student_refs = [ref for ref in references if ref.get('type') == 'student']
        if not student_refs:
            return ""
        
        try:
            from models.models import Users, UserVideoProgress, db
            from sqlalchemy import func
            
            context_parts = []
            for student_ref in student_refs:
                student_id = student_ref.get('id')
                student = db.session.query(Users).get(student_id)
                
                if student:
                    info = f"STUDENT_ID:{student.id}|NAME:{student.username}|CLASS:{student.class_name}"
                    
                    # 获取学习进度统计
                    completed_videos = db.session.query(UserVideoProgress).filter(
                        UserVideoProgress.user_id == student_id,
                        UserVideoProgress.completed == True
                    ).count()
                    
                    info += f"|COMPLETED_VIDEOS:{completed_videos}"
                    
                    context_parts.append(info)
            
            return "\\n".join(context_parts)
            
        except Exception as e:
            print(f"[TEACHER_AGENT] ⚠️ 构建学生洞察上下文失败: {str(e)}")
            return ""
    
    def query_teacher_agent(self, agent_executor, question: str, history: List[Dict] = None) -> Dict[str, Any]:
        """
        使用教师端Agent进行查询（复用学生端的流式实现）
        
        Args:
            agent_executor: Agent执行器
            question: 问题
            history: 对话历史
            
        Returns:
            查询结果
        """
        try:
            print(f"[TEACHER_AGENT] 执行教师端查询: question={question[:50]}...")
            
            # 添加教师端特定的问题处理逻辑
            enhanced_question = self._enhance_teacher_question(agent_executor, question)
            
            # 直接使用agent_qa_service的流式方法，与学生端保持一致
            if history:
                result = agent_qa_service.query_with_history(
                    agent_executor, enhanced_question, history
                )
            else:
                result = agent_qa_service.query(agent_executor, enhanced_question)
            
            # 后处理教师端结果
            enhanced_result = self._enhance_teacher_result(agent_executor, result)
            
            print(f"[TEACHER_AGENT] ✅ 教师端查询完成")
            return enhanced_result
            
        except Exception as e:
            error_msg = f"教师端查询失败: {str(e)}"
            print(f"[TEACHER_AGENT] ❌ {error_msg}")
            traceback.print_exc()
            return {
                "result": f"查询失败: {str(e)}",
                "source_documents": [],
                "intermediate_steps": []
            }
    
    def _enhance_teacher_question(self, agent_executor, question: str) -> str:
        """增强教师端问题（添加教师视角的上下文）"""
        qa_mode = getattr(agent_executor, '_qa_mode', 'teacher_general')
        
        # 根据QA模式添加不同的前缀
        mode_prefixes = {
            'course_analysis': '作为教师，请从课程分析角度回答：',
            'content_analysis': '作为教师，请从内容分析角度回答：',
            'student_insights': '作为教师，请从学生洞察角度回答：',
            'all': '作为教师，请从综合教学角度回答：',
            'teacher_general': '作为教师，请回答：'
        }
        
        prefix = mode_prefixes.get(qa_mode, '作为教师，请回答：')
        enhanced_question = f"{prefix}{question}"
        
        print(f"[TEACHER_AGENT] 问题增强: {qa_mode} -> {enhanced_question[:100]}...")
        return enhanced_question
    
    def _enhance_teacher_result(self, agent_executor, result: Dict[str, Any]) -> Dict[str, Any]:
        """增强教师端结果（添加教师特定的分析）"""
        try:
            # 添加教师端特定的元数据
            result['teacher_metadata'] = {
                'teacher_id': getattr(agent_executor, '_teacher_id', None),
                'qa_mode': getattr(agent_executor, '_qa_mode', 'teacher_general'),
                'references_count': len(getattr(agent_executor, '_references', []))
            }
            
            # TODO: 添加更多教师端特定的结果增强逻辑
            # 例如：教学建议、学生洞察、课程分析等
            
            return result
            
        except Exception as e:
            print(f"[TEACHER_AGENT] ⚠️ 结果增强时出错: {str(e)}")
            return result
    
    def _get_teacher_courses(self, teacher_id: str) -> List[str]:
        """获取教师的课程列表"""
        try:
            from models.models import Course, User
            from models.models import db
            
            # 查询教师的课程
            teacher_courses = db.session.query(Course).filter(
                Course.teacher_id == teacher_id
            ).all()
            
            course_ids = [course.id for course in teacher_courses]
            print(f"[TEACHER_AGENT] 教师 {teacher_id} 的课程: {course_ids}")
            
            return course_ids
            
        except Exception as e:
            print(f"[TEACHER_AGENT] ⚠️ 获取教师课程失败: {str(e)}")
            return []
    
    def get_teacher_tools(self, teacher_id: str) -> List[Dict[str, Any]]:
        """
        获取教师端可用工具列表
        
        Args:
            teacher_id: 教师ID
            
        Returns:
            工具列表
        """
        try:
            print(f"[TEACHER_AGENT] 获取教师端工具: teacher_id={teacher_id}")
            
            # 获取教师的课程列表
            teacher_courses = self._get_teacher_courses(teacher_id)
            
            tools = [
                {
                    'name': 'teacher_course_list',
                    'display_name': '课程列表查询',
                    'description': '查询您的课程列表和基本信息',
                    'icon': 'mdi-book-multiple',
                    'enabled': True,
                    'courses_count': len(teacher_courses),
                    'status': 'ready'
                },
                {
                    'name': 'teaching_guidance',
                    'display_name': '教学安排指导',
                    'description': '基于课程内容提供教学规划建议',
                    'icon': 'mdi-clipboard-text-clock',
                    'enabled': len(teacher_courses) > 0,
                    'courses_count': len(teacher_courses),
                    'status': 'ready'
                },
                {
                    'name': 'course_search',
                    'display_name': '课程内容检索',
                    'description': '在您的课程中搜索相关教学内容',
                    'icon': 'mdi-book-search',
                    'enabled': len(teacher_courses) > 0,
                    'courses_count': len(teacher_courses),
                    'status': 'ready'
                },
                {
                    'name': 'video_search',
                    'display_name': '视频内容检索',
                    'description': '在您的课程视频中搜索相关片段',
                    'icon': 'mdi-video-search',
                    'enabled': len(teacher_courses) > 0,
                    'courses_count': len(teacher_courses),
                    'status': 'ready'
                },
                {
                    'name': 'document_search',
                    'display_name': '文档内容检索',
                    'description': '在您的课程文档中搜索相关资料',
                    'icon': 'mdi-file-document-search',
                    'enabled': len(teacher_courses) > 0,
                    'courses_count': len(teacher_courses),
                    'status': 'ready'
                },
                {
                    'name': 'general_search',
                    'display_name': '综合搜索',
                    'description': '在所有可访问的教学资源中搜索',
                    'icon': 'mdi-magnify',
                    'enabled': True,
                    'courses_count': len(teacher_courses),
                    'status': 'ready'
                },
                {
                    'name': 'student_learning_analysis',
                    'display_name': '学生学习分析',
                    'description': '分析学生的学习进度和掌握情况',
                    'icon': 'mdi-chart-line',
                    'enabled': len(teacher_courses) > 0,
                    'courses_count': len(teacher_courses),
                    'status': 'ready'
                }
            ]
            
            print(f"[TEACHER_AGENT] 获取教师端工具完成: tools_count={len(tools)}, courses_count={len(teacher_courses)}")
            return tools
            
        except Exception as e:
            print(f"[TEACHER_AGENT] ❌ 获取教师端工具失败: {str(e)}")
            return []

# 全局教师端智能助手服务实例
teacher_agent_service = TeacherAgentService() 