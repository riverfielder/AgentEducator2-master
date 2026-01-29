"""权限检查工具函数"""

from typing import List, Optional, Set
from models.models import Users, StudentCourseEnrollment, Course
from .db_utils import execute_with_app_context


def get_user_role(user_id: str) -> Optional[str]:
    """获取用户角色"""
    def query_user_role():
        user = Users.query.filter_by(id=user_id, is_deleted=False).first()
        return user.role if user else None
    
    return execute_with_app_context(query_user_role)


def get_student_accessible_courses(user_id: str) -> Set[str]:
    """获取学生有权限访问的课程ID列表"""
    def query_accessible_courses():
        enrollments = StudentCourseEnrollment.query.filter_by(student_id=user_id).all()
        return {str(enrollment.course_id) for enrollment in enrollments}
    
    return execute_with_app_context(query_accessible_courses)


def get_teacher_accessible_courses(user_id: str) -> Set[str]:
    """获取教师有权限访问的课程ID列表"""
    def query_teacher_courses():
        #for demo only: teacher can access all courses
        courses = Course.query.filter_by(is_deleted=False).all()
        return {str(course.id) for course in courses}
    
    return execute_with_app_context(query_teacher_courses)


def check_course_access_permission(user_id: str, course_id: str) -> bool:
    """检查用户是否有访问指定课程的权限"""
    if not user_id or not course_id:
        return False
    
    user_role = get_user_role(user_id)
    if not user_role:
        return False
    
    if user_role == 'student':
        accessible_courses = get_student_accessible_courses(user_id)
        return course_id in accessible_courses
    elif user_role == 'teacher':
        # 教师可以访问自己教授的课程
        teacher_courses = get_teacher_accessible_courses(user_id)
        # 也可以访问学生能访问的课程（用于查看学生学习情况）
        student_courses = get_student_accessible_courses(user_id)
        return course_id in teacher_courses or course_id in student_courses
    
    return False


def check_video_access_permission(user_id: str, video_id: str) -> bool:
    """检查用户是否有访问指定视频的权限"""
    def query_video_course():
        from models.models import Video
        video = Video.query.filter_by(id=video_id, is_deleted=False).first()
        return str(video.course_id) if video else None
    
    course_id = execute_with_app_context(query_video_course)
    if not course_id:
        return False
    
    return check_course_access_permission(user_id, course_id)


def check_document_access_permission(user_id: str, document_id: str) -> bool:
    """检查用户是否有访问指定文档的权限"""
    def query_document_course():
        from models.models import Document
        document = Document.query.filter_by(id=document_id, is_deleted=False).first()
        return str(document.course_id) if document else None
    
    course_id = execute_with_app_context(query_document_course)
    if not course_id:
        return False
    
    return check_course_access_permission(user_id, course_id)


def filter_courses_by_permission(user_id: str, course_ids: List[str]) -> List[str]:
    """根据用户权限过滤课程列表"""
    if not user_id:
        return []
    
    user_role = get_user_role(user_id)
    if not user_role:
        return []
    
    if user_role == 'student':
        accessible_courses = get_student_accessible_courses(user_id)
        return [cid for cid in course_ids if cid in accessible_courses]
    elif user_role == 'teacher':
        # 教师可以访问所有课程（管理员级别）
        return course_ids
    
    return []


def filter_videos_by_permission(user_id: str, video_ids: List[str]) -> List[str]:
    """根据用户权限过滤视频列表"""
    if not user_id:
        return []
    
    user_role = get_user_role(user_id)
    if not user_role:
        return []
    
    if user_role == 'teacher':
        # 教师可以访问所有视频
        return video_ids
    
    # 学生需要逐个检查视频权限
    accessible_videos = []
    for video_id in video_ids:
        if check_video_access_permission(user_id, video_id):
            accessible_videos.append(video_id)
    
    return accessible_videos


def filter_documents_by_permission(user_id: str, document_ids: List[str]) -> List[str]:
    """根据用户权限过滤文档列表"""
    if not user_id:
        return []
    
    user_role = get_user_role(user_id)
    if not user_role:
        return []
    
    if user_role == 'teacher':
        # 教师可以访问所有文档
        return document_ids
    
    # 学生需要逐个检查文档权限
    accessible_documents = []
    for document_id in document_ids:
        if check_document_access_permission(user_id, document_id):
            accessible_documents.append(document_id)
    
    return accessible_documents
