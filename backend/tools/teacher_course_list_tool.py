"""教师课程列表工具"""

import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from .base_tool import BaseTool


class TeacherCourseListInput(BaseModel):
    """教师课程列表工具的输入参数模型"""
    list_type: str = Field(default="all", description="列表类型：all(所有课程)、active(活跃课程)、detailed(详细信息)")


class TeacherCourseListTool(BaseTool):
    """教师课程列表工具"""
    
    name = "teacher_course_list"
    description = "获取当前教师的课程列表信息，包括课程名称、学生数量、视频和文档资源统计。当用户询问'我有哪些课程'、'我的课程'、'课程列表'、'我教的课程'等问题时，必须使用此工具。"
    
    def __init__(self, user_id: str = None):
        super().__init__(user_id=user_id)
        
    def get_display_info(self) -> Dict[str, Any]:
        """获取前端展示信息"""
        return {
            "tool_name": "课程列表查询",
            "tool_icon": "mdi-book-multiple",
            "tool_color": "primary",
            "description": "查询您的课程列表和基本信息",
            "context": {
                "supports_course_list": True,
                "supports_course_stats": True
            },
            "status_message": "正在获取您的课程列表..."
        }
    
    def search(self, list_type: str = "all") -> str:
        """实现BaseTool要求的search方法"""
        return self.get_teacher_courses(list_type)
    
    def get_teacher_courses(self, list_type: str = "all") -> str:
        """获取教师的课程列表"""
        try:
            print(f"[FLOW] TeacherCourseListTool.get_teacher_courses 开始执行")
            print(f"[FLOW] 参数 - list_type: {list_type}, user_id: {self.user_id}")
            
            # 更新展示信息
            display_info = self.get_display_info()
            self._notify_tool_start(display_info)
            
            # 获取教师课程信息
            courses_info = self._get_teacher_courses_from_db()
            
            if not courses_info:
                result_msg = "您目前没有分配任何课程。请联系管理员确认课程分配情况。"
                print(f"[FLOW] {result_msg}")
                self._notify_tool_result({
                    "success": False,
                    "message": result_msg,
                    "courses_count": 0
                })
                return result_msg
            
            # 格式化课程信息
            formatted_result = self._format_course_list(courses_info, list_type)
            
            print(f"[FLOW] 成功获取 {len(courses_info)} 个课程")
            print(f"[DEBUG] 格式化后的结果: {formatted_result[:200]}...")
            self._notify_tool_result({
                "success": True,
                "message": f"成功获取课程列表",
                "courses_count": len(courses_info)
            })
            
            return formatted_result
            
        except Exception as e:
            error_msg = f"获取课程列表失败: {str(e)}"
            print(f"[FLOW] {error_msg}")
            self._notify_tool_result({
                "success": False,
                "message": error_msg,
                "courses_count": 0
            })
            return error_msg
    
    def _get_teacher_courses_from_db(self) -> List[Dict[str, Any]]:
        """从数据库获取教师课程信息"""
        try:
            from models.models import Course, Video, Document, db
            from sqlalchemy import func
            
            def get_courses():
                # 先查询教师的课程基本信息
                courses_query = db.session.query(Course).filter(
                    Course.teacher_id == self.user_id,
                    Course.is_deleted == False
                ).all()
                
                print(f"[DEBUG] 查询到 {len(courses_query)} 个课程")
                
                courses_info = []
                for course in courses_query:
                    # 分别查询视频和文档数量
                    video_count = db.session.query(Video).filter(
                        Video.course_id == course.id,
                        Video.is_deleted == False
                    ).count()
                    
                    document_count = db.session.query(Document).filter(
                        Document.course_id == course.id,
                        Document.is_deleted == False
                    ).count()
                    
                    # 查询学生数量
                    from models.models import StudentCourseEnrollment, Users
                    student_count = db.session.query(StudentCourseEnrollment).join(
                        Users, StudentCourseEnrollment.student_id == Users.id
                    ).filter(
                        StudentCourseEnrollment.course_id == course.id,
                        Users.is_deleted == False
                    ).count()
                    
                    print(f"[DEBUG] 课程 {course.name}: video_count={video_count}, document_count={document_count}, student_count={student_count}")
                    
                    courses_info.append({
                        'id': course.id,
                        'name': course.name,
                        'description': course.description,
                        'created_at': course.create_time,
                        'video_count': video_count,
                        'document_count': document_count,
                        'student_count': student_count
                    })
                
                return courses_info
            
            return self._execute_with_app_context(get_courses)
            
        except Exception as e:
            print(f"[ERROR] 从数据库获取课程信息失败: {e}")
            return []
    
    def _format_course_list(self, courses_info: List[Dict[str, Any]], list_type: str) -> str:
        """格式化课程列表信息"""
        if not courses_info:
            return "您目前没有分配任何课程。"
        
        result_lines = [f"您共有 {len(courses_info)} 个课程：\n"]
        
        for i, course in enumerate(courses_info, 1):
            course_name = course.get('name', '未知课程')
            course_id = course.get('id', '')
            
            if list_type == "detailed":
                # 详细信息模式
                video_count = course.get('video_count', 0)
                document_count = course.get('document_count', 0)
                student_count = course.get('student_count', 0)
                created_at = course.get('created_at', '')
                description = course.get('description', '暂无描述')
                
                result_lines.append(
                    f"{i}. 【{course_name}】\n"
                    f"   - 课程ID: {course_id}\n"
                    f"   - 描述: {description}\n"
                    f"   - 学生数量: {student_count} 人\n"
                    f"   - 教学资源: {video_count} 个视频, {document_count} 个文档\n"
                    f"   - 创建时间: {created_at}\n"
                )
            else:
                # 简单列表模式
                student_count = course.get('student_count', 0)
                video_count = course.get('video_count', 0)
                document_count = course.get('document_count', 0)
                
                result_lines.append(
                    f"{i}. 【{course_name}】(ID: {course_id}) - {student_count} 名学生, {video_count} 个视频, {document_count} 个文档"
                )
        
        result_lines.append("\n您可以询问具体课程的详细信息，或者对某个课程进行深入分析。")
        
        return "\n".join(result_lines)

# 导出工具类
__all__ = ['TeacherCourseListTool'] 