"""基础工具类"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Set
import json
from .global_index_manager import global_source_index_manager


class BaseTool(ABC):
    """工具基类"""
    
    def __init__(self, user_id: str = None):
        self.user_id = user_id  # 用户ID，用于权限控制
        self.retrieved_docs = []  # 存储检索到的文档
        self.streaming_callback = None  # 流式回调引用
        
        # 权限控制核心属性
        self.accessible_courses: Set[str] = set()  # 有权限访问的课程ID集合
        self.accessible_users: Set[str] = set()    # 有权限访问的用户ID集合（用于学习分析等）
        
        # 初始化权限
        self._initialize_permissions()
    
    def set_streaming_callback(self, callback):
        """设置流式回调"""
        self.streaming_callback = callback
    
    def _notify_tool_start(self, display_info: Dict[str, Any]):
        """通知前端工具开始执行"""
        print(f"[TOOL_NOTIFY] {self.__class__.__name__} 发送工具开始通知: {display_info.get('tool_name', 'Unknown')}")
        print(f"[TOOL_NOTIFY] streaming_callback 存在: {self.streaming_callback is not None}")
        
        if self.streaming_callback:
            notification = {
                "type": "tool_start",
                "data": display_info
            }
            # 发送工具开始通知 - 使用特殊方法绕过token缓存
            if hasattr(self.streaming_callback, 'send_tool_event'):
                self.streaming_callback.send_tool_event(f"\n[TOOL_EVENT]{json.dumps(notification)}[/TOOL_EVENT]\n")
                print(f"[TOOL_NOTIFY] 使用 send_tool_event 发送工具开始通知")
            else:
                # 兼容性：如果没有特殊方法，使用原来的方式
                self.streaming_callback.on_llm_new_token(f"\n[TOOL_EVENT]{json.dumps(notification)}[/TOOL_EVENT]\n")
                print(f"[TOOL_NOTIFY] 使用 on_llm_new_token 发送工具开始通知")
        else:
            print(f"[TOOL_NOTIFY] ⚠️ 没有streaming_callback，无法发送工具通知")
    
    def _notify_tool_result(self, result_info: Dict[str, Any]):
        """通知前端工具执行结果"""
        print(f"[TOOL_NOTIFY] {self.__class__.__name__} 发送工具结果通知: {result_info.get('message', 'Unknown')}")
        
        if self.streaming_callback:
            notification = {
                "type": "tool_result", 
                "data": result_info
            }
            # 发送工具结果通知 - 使用特殊方法绕过token缓存
            if hasattr(self.streaming_callback, 'send_tool_event'):
                self.streaming_callback.send_tool_event(f"\n[TOOL_EVENT]{json.dumps(notification)}[/TOOL_EVENT]\n")
                print(f"[TOOL_NOTIFY] 使用 send_tool_event 发送工具结果通知")
            else:
                # 兼容性：如果没有特殊方法，使用原来的方式
                self.streaming_callback.on_llm_new_token(f"\n[TOOL_EVENT]{json.dumps(notification)}[/TOOL_EVENT]\n")
                print(f"[TOOL_NOTIFY] 使用 on_llm_new_token 发送工具结果通知")
        else:
            print(f"[TOOL_NOTIFY] ⚠️ 没有streaming_callback，无法发送工具结果通知")
    
    def clear_docs(self):
        """清空已检索的文档"""
        self.retrieved_docs.clear()
    
    def store_docs(self, docs: list, max_docs: int = None):
        """存储文档并分配全局序号"""
        if max_docs:
            docs_to_store = docs[:max_docs]
        else:
            docs_to_store = docs
        
        # 分配全局序号
        docs_with_indices = global_source_index_manager.assign_indices(docs_to_store)
        self.retrieved_docs.extend(docs_with_indices)
        
        print(f"[FLOW] {self.__class__.__name__} 存储了 {len(docs_to_store)} 个文档")
        print(f"[FLOW] 当前retrieved_docs总数: {len(self.retrieved_docs)}")
        
        return docs_with_indices
    
    def _execute_with_app_context(self, func):
        """在应用上下文中执行函数"""
        from flask import has_app_context
        
        if not has_app_context():
            from flask import current_app
            try:
                app = current_app._get_current_object()
            except:
                from app import create_app
                app = create_app()
            
            with app.app_context():
                return func()
        else:
            return func()

    def _initialize_permissions(self):
        """初始化用户权限"""
        if not self.user_id:
            print(f"[PERMISSIONS] {self.__class__.__name__}: 无user_id，跳过权限初始化")
            return
        
        try:
            from .permission_utils import (
                get_user_role, get_student_accessible_courses, 
                get_teacher_accessible_courses
            )
            
            user_role = get_user_role(self.user_id)
            print(f"[PERMISSIONS] {self.__class__.__name__}: 用户 {self.user_id} 角色为 {user_role}")
            
            if not user_role:
                print(f"[PERMISSIONS] {self.__class__.__name__}: 无法获取用户角色")
                return
            
            if user_role == 'student':
                # 学生只能访问已注册的课程
                self.accessible_courses = get_student_accessible_courses(self.user_id)
                # 学生只能访问自己的用户数据
                self.accessible_users = {self.user_id}
                print(f"[PERMISSIONS] {self.__class__.__name__}: 学生可访问 {len(self.accessible_courses)} 个课程")
                
            elif user_role == 'teacher':
                # 教师可以访问所有课程
                self.accessible_courses = self._get_all_courses()
                # 教师可以访问所有学生的数据
                self.accessible_users = self._get_all_students()
                print(f"[PERMISSIONS] {self.__class__.__name__}: 教师可访问 {len(self.accessible_courses)} 个课程, {len(self.accessible_users)} 个学生")
                
        except Exception as e:
            print(f"[ERROR] {self.__class__.__name__} 初始化权限失败: {e}")
            # 失败时设置为空集合，确保安全
            self.accessible_courses = set()
            self.accessible_users = set()
    
    def _get_all_courses(self) -> Set[str]:
        """获取所有课程ID"""
        def query_all_courses():
            from models.models import Course
            courses = Course.query.filter_by(is_deleted=False).all()
            return {str(course.id) for course in courses}
        
        return self._execute_with_app_context(query_all_courses)
    
    def _get_all_students(self) -> Set[str]:
        """获取所有学生ID"""
        def query_all_students():
            from models.models import Users
            students = Users.query.filter_by(role='student', is_deleted=False).all()
            return {str(student.id) for student in students}
        
        return self._execute_with_app_context(query_all_students)
    
    def has_course_access(self, course_id: str) -> bool:
        """检查是否有访问指定课程的权限"""
        return course_id in self.accessible_courses
    
    def has_user_access(self, target_user_id: str) -> bool:
        """检查是否有访问指定用户数据的权限"""
        return target_user_id in self.accessible_users
    
    def filter_courses_by_access(self, course_ids: List[str]) -> List[str]:
        """根据权限过滤课程列表"""
        return [cid for cid in course_ids if cid in self.accessible_courses]
    
    def get_accessible_course_filter(self) -> str:
        """获取可访问课程的SQL过滤条件"""
        if not self.accessible_courses:
            return "FALSE"  # 无权限时返回永假条件
        
        course_ids = "', '".join(self.accessible_courses)
        return f"course_id IN ('{course_ids}')"

    @abstractmethod
    def search(self, query: str) -> str:
        """搜索方法，子类需要实现"""
        pass
    
    @abstractmethod
    def get_display_info(self) -> Dict[str, Any]:
        """获取前端展示信息，子类需要实现"""
        pass
