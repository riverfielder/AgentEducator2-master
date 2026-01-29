"""学生作业查询工具"""

import json
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from .base_tool import BaseTool
from .db_utils import execute_with_app_context, find_entity_by_name


class AssignmentSearchInput(BaseModel):
    """作业查询工具的输入参数模型"""
    course_identifier: Optional[str] = Field(
        default=None, 
        description="课程标识符（课程名称或ID），可选。如果不提供或无效，则列出学生所有作业。"
    )


class AssignmentRetrievalTool(BaseTool):
    """学生作业查询工具"""
    
    name = "list_assignment"
    description = "查看当前学生的作业信息和具体内容。可以指定课程标识符来查看特定课程的作业，或不指定来查看所有作业。返回作业的详细信息包括课程、截止日期、题目列表等。当你回复的时候，简要说明这个作业涉及的知识点和要求，**不要给出答案和复述原题**。"
    
    def __init__(self, user_id: str = None):
        super().__init__(user_id=user_id)  # 正确传递user_id给基类
        
    def get_display_info(self) -> Dict[str, Any]:
        """获取前端展示信息"""
        return {
            "tool_name": "作业信息查询",
            "tool_icon": "mdi-clipboard-text",
            "tool_color": "primary",
            "description": "查看当前学生的作业信息，包括课程、截止日期、题目等",
            "context": {
                "supports_course_filter": True,
                "returns_assignment_details": True,
                "user_specific": True
            },
            "status_message": "正在查询作业信息..."
        }
    
    def _find_course_by_name(self, name: str) -> Optional[str]:
        """通过名称查找课程ID"""
        try:
            from models.models import Course
            return find_entity_by_name(Course, name, lambda c: c.name)
        except Exception as e:
            print(f"[ERROR] 通过名称查找课程失败: {e}")
            return None
    
    def _resolve_course_id(self, course_identifier: Optional[str]) -> Optional[str]:
        """解析课程标识符，返回课程ID"""
        if not course_identifier:
            return None
            
        def query_course():
            from models.models import Course
            import uuid
            
            # 先尝试作为UUID查询
            try:
                course_uuid = uuid.UUID(course_identifier)
                course = Course.query.filter_by(id=course_uuid, is_deleted=False).first()
                if course:
                    return str(course.id)
            except ValueError:
                pass
            
            # 如果不是有效UUID，尝试作为名称查找
            course = Course.query.filter(
                Course.name.ilike(f"%{course_identifier}%"),
                Course.is_deleted == False
            ).first()
            
            return str(course.id) if course else None
        
        return execute_with_app_context(query_course)
    
    def _get_student_assignments(self, course_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取学生的作业信息"""
        def query_assignments():
            from models.models import Assignment, Course, Question, StudentAnswer, StudentCourseEnrollment
            import uuid
            
            print(f"[PERMISSIONS] AssignmentRetrievalTool: 开始查询作业，用户ID: {self.user_id}")
            print(f"[PERMISSIONS] AssignmentRetrievalTool: 可访问课程数量: {len(self.accessible_courses)}")
            print(f"[PERMISSIONS] AssignmentRetrievalTool: 可访问课程: {list(self.accessible_courses)[:5]}...")  # 只显示前5个
            
            if not self.user_id:
                print(f"[ERROR] 无用户ID")
                return []
            
            try:
                user_id_str = str(self.user_id)
            except ValueError:
                print(f"[ERROR] 无效的用户ID: {self.user_id}")
                return []
            
            # 获取当前时间
            current_time = datetime.now()
            
            # 构建基础查询 - 使用权限过滤的课程
            query = Assignment.query.join(Course).filter(
                Assignment.is_deleted == False,
                Assignment.status == 'published',  # 只显示已发布的作业
                Assignment.publish_time <= current_time,  # 确保已到发布时间
                Course.is_deleted == False
            )
            
            # 根据权限过滤课程
            if self.accessible_courses:
                query = query.filter(Course.id.in_(self.accessible_courses))
            else:
                # 如果没有可访问的课程，返回空结果
                return []
            
            # 如果指定了课程ID，添加额外过滤
            if course_id and self.has_course_access(course_id):
                try:
                    course_uuid = uuid.UUID(course_id)
                    query = query.filter(Assignment.course_id == course_uuid)
                except ValueError:
                    print(f"[ERROR] 无效的课程ID: {course_id}")
                    return []
            
            assignments = query.order_by(Assignment.due_date.asc()).all()
            
            result = []
            for assignment in assignments:
                # 获取作业的题目信息
                questions = Question.query.filter_by(
                    assignment_id=assignment.id
                ).order_by(Question.order_num).all()
                
                # 获取学生的答题情况
                student_answers = StudentAnswer.query.filter_by(
                    student_id=user_id_str,
                    assignment_id=assignment.id
                ).all()
                
                # 计算完成状态
                total_questions = len(questions)
                answered_questions = len(student_answers)
                completion_rate = (answered_questions / total_questions * 100) if total_questions > 0 else 0
                
                # 判断是否已截止
                current_time = datetime.now()
                is_overdue = current_time > assignment.due_date
                
                # 计算总分和已得分
                total_score = sum(q.max_score for q in questions)
                earned_score = sum(answer.score for answer in student_answers if answer.score is not None)
                
                assignment_info = {
                    "id": str(assignment.id),
                    "title": assignment.title,
                    "course": {
                        "id": str(assignment.course.id),
                        "name": assignment.course.name,
                        "code": assignment.course.code
                    },
                    "due_date": assignment.due_date.isoformat(),
                    "publish_time": assignment.publish_time.isoformat() if assignment.publish_time else None,
                    "status": assignment.status,
                    "is_overdue": is_overdue,
                    "completion_status": {
                        "total_questions": total_questions,
                        "answered_questions": answered_questions,
                        "completion_rate": round(completion_rate, 2),
                        "is_completed": answered_questions == total_questions
                    },
                    "score_info": {
                        "total_score": total_score,
                        "earned_score": earned_score if earned_score is not None else 0,
                        "percentage": round((earned_score / total_score * 100) if total_score > 0 and earned_score is not None else 0, 2)
                    },
                    "questions": [
                        {
                            "id": str(q.id),
                            "type": q.type,
                            "content": q.content,
                            "order_num": q.order_num,
                            "max_score": q.max_score,
                            "options": json.loads(q.options) if q.options else None,
                            #"reference": q.reference,
                            #"explanation": q.explanation
                        } for q in questions
                    ]
                }
                
                result.append(assignment_info)
            
            return result
        
        return execute_with_app_context(query_assignments)
    
    def search(self, course_identifier: Optional[str] = None) -> str:
        """搜索学生作业信息"""
        try:
            # 通知前端工具开始执行
            self._notify_tool_start(self.get_display_info())
            
            # 解析课程标识符
            course_id = None
            if course_identifier:
                course_id = self._resolve_course_id(course_identifier)
                if not course_id:
                    return json.dumps({
                        "success": False,
                        "message": f"未找到课程: {course_identifier}",
                        "data": []
                    }, ensure_ascii=False, indent=2)
            
            # 获取作业信息
            assignments = self._get_student_assignments(course_id)
            
            # 构建结果
            result = {
                "success": True,
                "message": "查询成功",
                "data": {
                    "assignments": assignments,
                    "summary": {
                        "total_assignments": len(assignments),
                        "completed_assignments": len([a for a in assignments if a["completion_status"]["is_completed"]]),
                        "overdue_assignments": len([a for a in assignments if a["is_overdue"]]),
                        "course_filter": course_identifier if course_identifier else "全部课程"
                    }
                }
            }
            
            # 通知前端工具执行结果
            self._notify_tool_result({
                "success": True,
                "message": f"找到 {len(assignments)} 个作业",
                "assignments_found": len(assignments),
                "course_filter": course_identifier if course_identifier else "全部课程",
                "completed_count": result["data"]["summary"]["completed_assignments"],
                "overdue_count": result["data"]["summary"]["overdue_assignments"]
            })
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            error_msg = f"查询作业信息失败: {str(e)}"
            self._notify_tool_result({
                "success": False,
                "message": error_msg,
                "assignments_found": 0
            })
            error_result = {
                "success": False,
                "message": error_msg,
                "data": []
            }
            return json.dumps(error_result, ensure_ascii=False, indent=2)