"""课程访问权限服务模块"""
from models.models import Users, StudentCourseEnrollment, Course


class CourseAccessService:
    """课程访问权限服务"""
    
    @staticmethod
    def get_accessible_course_ids(user_id):
        """获取用户可访问的课程ID列表"""
        user = Users.query.filter_by(id=user_id, is_deleted=False).first()
        if not user:
            return []
        
        # 获取已注册的课程
        enrolled_courses = StudentCourseEnrollment.query.filter_by(student_id=user.id).all()
        enrolled_course_ids = [ec.course_id for ec in enrolled_courses]
        
        # 获取公开课程
        public_courses = Course.query.filter_by(is_public=True).all()
        public_course_ids = [pc.id for pc in public_courses]
        
        # 合并去重
        accessible_course_ids = list(set(enrolled_course_ids + public_course_ids))
        return accessible_course_ids


# 全局课程访问服务实例
course_access_service = CourseAccessService()
