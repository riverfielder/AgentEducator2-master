# filepath: backend/routes/teacher_dashboard.py
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from sqlalchemy import and_, or_, func, desc
from models.models import (
    Course, db, Users, Video, VideoComment, StudentCourseEnrollment, CommentLike
)
from utils.result import Result
from utils.auth import token_required
import os
import json

teacher_dashboard_bp = Blueprint('teacher_dashboard', __name__)

def is_teacher_or_admin(user):
    """检查用户是否为教师或管理员"""
    if not user:
        return False
    return user.role in ['teacher', 'admin']

@teacher_dashboard_bp.route('/schedule', methods=['GET'])
@token_required
def get_course_schedule():
    """
    获取课程日程
    """
    try:
        user_id = request.user.get('user_id')
        user = Users.query.filter_by(id=user_id, is_deleted=False).first()
        
        if not is_teacher_or_admin(user):
            return jsonify(Result.error(403, "无权访问，需要教师或管理员权限"))
        
        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        view_type = request.args.get('view_type', 'month')  # month, week, day
        
        # 构建查询 - 如果是教师，只显示自己的课程；管理员显示所有课程
        if user.role == 'teacher':
            courses_query = Course.query.filter_by(teacher_id=user_id, is_deleted=False)
        else:
            courses_query = Course.query.filter_by(is_deleted=False)
        
        # 根据日期范围过滤
        if start_date and end_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                # 这里可以根据课程的开始和结束时间进行过滤
                # 由于数据库中没有明确的课程时间字段，我们使用创建时间作为示例
                courses_query = courses_query.filter(
                    and_(
                        Course.create_time >= start_dt,
                        Course.create_time <= end_dt
                    )
                )
            except ValueError:
                return jsonify(Result.error(400, "日期格式错误"))
        
        courses = courses_query.all()
        
        # 构建课程日程数据
        schedule_events = []
        for course in courses:
            # 获取课程统计
            video_count = Video.query.filter_by(course_id=course.id, is_deleted=False).count()
            enrolled_count = db.session.query(StudentCourseEnrollment).join(
                Users, StudentCourseEnrollment.student_id == Users.id
            ).filter(
                StudentCourseEnrollment.course_id == course.id,
                Users.is_deleted == False
            ).count()
            
            # 根据课程状态确定颜色
            color_map = {
                'active': '#4CAF50',     # 绿色 - 进行中
                'upcoming': '#2196F3',   # 蓝色 - 即将开始
                'completed': '#9E9E9E'   # 灰色 - 已结束
            }
            
            # 生成课程事件（这里可以根据实际的课程时间表调整）
            # 目前使用模拟数据，实际应用中应该有具体的上课时间
            event = {
                'id': str(course.id),
                'title': course.name,
                'description': course.description or '',
                'start': course.create_time.isoformat(),
                'end': (course.create_time + timedelta(hours=2)).isoformat(),  # 假设每节课2小时
                'color': color_map.get(course.status, '#757575'),
                'status': course.status,
                'teacher': course.teacher.username if course.teacher else '未分配',
                'videoCount': video_count,
                'enrolledCount': enrolled_count,
                'location': '在线教室',  # 可以从课程表中获取实际教室信息
                'category': (lambda desc: (json.loads(desc).get('category', ['未分类']) if desc else ['未分类'])(course.description)),
                'extendedProps': {
                    'courseId': str(course.id),
                    'teacherId': str(course.teacher_id) if course.teacher_id else None,
                    'status': course.status,
                    'videoCount': video_count,
                    'enrolledCount': enrolled_count
                }
            }
            schedule_events.append(event)
        
        # 获取今日统计
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # 今日课程统计
        today_courses = [e for e in schedule_events 
                        if today_start <= datetime.fromisoformat(e['start'].replace('Z', '+00:00')) <= today_end]
        
        # 即将到来的课程
        upcoming_courses = [e for e in schedule_events 
                           if datetime.fromisoformat(e['start'].replace('Z', '+00:00')) > datetime.now()][:5]
        
        summary = {
            'totalCourses': len(schedule_events),
            'todayCourses': len(today_courses),
            'activeCourses': len([e for e in schedule_events if e['status'] == 'active']),
            'upcomingCourses': len([e for e in schedule_events if e['status'] == 'upcoming']),
            'nextCourses': upcoming_courses
        }
        
        return jsonify(Result.success({
            'events': schedule_events,
            'summary': summary,
            'viewType': view_type
        }, "获取课程日程成功"))
        
    except Exception as e:
        return jsonify(Result.error(500, f"获取课程日程失败: {str(e)}"))

@teacher_dashboard_bp.route('/messages', methods=['GET'])
@token_required
def get_teacher_messages():
    """
    获取教师消息列表（学生评论）
    """
    try:
        user_id = request.user.get('user_id')
        user = Users.query.filter_by(id=user_id, is_deleted=False).first()
        
        if not is_teacher_or_admin(user):
            return jsonify(Result.error(403, "无权访问，需要教师或管理员权限"))
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 20, type=int)
        status = request.args.get('status', 'all')  # all, unread, replied
        course_id = request.args.get('course_id')
        keyword = request.args.get('keyword', '')
        
        # 新增：只显示7天内的评论
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        # 构建查询 - 获取教师相关课程的学生评论（不包括教师和管理员的评论）
        if user.role == 'teacher':
            # 教师只能看到自己课程的学生评论
            comments_query = db.session.query(VideoComment).join(
                Video, VideoComment.video_id == Video.id
            ).join(
                Course, Video.course_id == Course.id
            ).join(
                Users, VideoComment.user_id == Users.id
            ).filter(
                and_(
                    Course.teacher_id == user_id,
                    VideoComment.is_deleted == False,
                    Users.role == 'student',  # 只显示学生的评论
                    VideoComment.parent_id.is_(None),  # 只显示主评论，不包括回复
                    VideoComment.create_time >= seven_days_ago  # 只显示7天内的
                )
            )
        else:
            # 管理员可以看到所有学生评论
            comments_query = db.session.query(VideoComment).join(
                Video, VideoComment.video_id == Video.id
            ).join(
                Course, Video.course_id == Course.id
            ).join(
                Users, VideoComment.user_id == Users.id
            ).filter(
                and_(
                    VideoComment.is_deleted == False,
                    Users.role == 'student',  # 只显示学生的评论
                    VideoComment.parent_id.is_(None),  # 只显示主评论，不包括回复
                    VideoComment.create_time >= seven_days_ago  # 只显示7天内的
                )
            )
        
        # 按课程ID过滤
        if course_id and course_id != 'all':
            comments_query = comments_query.filter(Course.id == course_id)
        
        # 知识点搜索
        if keyword:
            comments_query = comments_query.filter(
                or_(
                    VideoComment.content.contains(keyword),
                    Video.title.contains(keyword)
                )
            )
          # 状态过滤
        if status == 'unread':
            # 获取未被教师回复的评论
            teacher_replied_comment_ids = db.session.query(VideoComment.parent_id).join(
                Users, VideoComment.user_id == Users.id
            ).filter(
                VideoComment.parent_id.isnot(None),
                Users.role.in_(['teacher', 'admin']),
                VideoComment.is_deleted == False
            ).distinct().subquery()
            
            comments_query = comments_query.filter(
                VideoComment.id.notin_(
                    db.session.query(teacher_replied_comment_ids.c.parent_id).filter(
                        teacher_replied_comment_ids.c.parent_id.isnot(None)
                    )
                )
            )
        elif status == 'replied':
            # 获取已被教师回复的评论
            teacher_replied_comment_ids = db.session.query(VideoComment.parent_id).join(
                Users, VideoComment.user_id == Users.id
            ).filter(
                VideoComment.parent_id.isnot(None),
                Users.role.in_(['teacher', 'admin']),
                VideoComment.is_deleted == False
            ).distinct().subquery()
            
            comments_query = comments_query.filter(
                VideoComment.id.in_(
                    db.session.query(teacher_replied_comment_ids.c.parent_id).filter(
                        teacher_replied_comment_ids.c.parent_id.isnot(None)
                    )
                )
            )
        
        # 获取总数
        total = comments_query.count()
        
        # 分页查询
        comments = comments_query.order_by(VideoComment.create_time.desc()) \
                                .offset((page - 1) * page_size) \
                                .limit(page_size) \
                                .all()
        
        # 构建消息列表
        message_list = []
        for comment in comments:
            # 获取回复数量
            reply_count = VideoComment.query.filter_by(
                parent_id=comment.id, 
                is_deleted=False
            ).count()
            
            # 获取最新回复
            latest_reply = VideoComment.query.filter_by(
                parent_id=comment.id, 
                is_deleted=False
            ).order_by(VideoComment.create_time.desc()).first()
              # 检查是否有教师回复
            has_teacher_reply = False
            if reply_count > 0:
                # 检查回复中是否有教师或管理员的回复
                teacher_reply_count = VideoComment.query.join(
                    Users, VideoComment.user_id == Users.id
                ).filter(
                    VideoComment.parent_id == comment.id,
                    VideoComment.is_deleted == False,
                    Users.role.in_(['teacher', 'admin'])
                ).count()
                has_teacher_reply = teacher_reply_count > 0
              # 处理学生头像URL
            student_avatar = None
            if comment.user and comment.user.avatar:
                # 统一处理头像URL，确保正确的路径
                if comment.user.avatar.startswith('http'):
                    # 已经是完整URL
                    student_avatar = comment.user.avatar
                elif comment.user.avatar.startswith('/'):
                    # 以/开头的绝对路径，添加服务器前缀
                    student_avatar = f"http://localhost:5000{comment.user.avatar}"
                else:
                    # 相对路径，需要添加完整的静态文件路径
                    student_avatar = f"http://localhost:5000/static/{comment.user.avatar}"
            
            message_list.append({
                'id': comment.id,
                'content': comment.content,
                'studentName': comment.user.username if comment.user else '未知学生',
                'studentAvatar': student_avatar,
                'videoTitle': comment.video.title if comment.video else '未知视频',
                'videoId': comment.video_id,
                'courseName': comment.video.course.name if comment.video and comment.video.course else '未知课程',
                'courseId': str(comment.video.course.id) if comment.video and comment.video.course else None,
                'timePoint': comment.time_point,
                'createTime': comment.create_time.isoformat(),
                'likes': comment.likes,
                'replyCount': reply_count,
                'hasTeacherReply': has_teacher_reply,
                'isUnread': not has_teacher_reply,  # 如果没有教师回复，则为未读
                'priority': 'high' if comment.likes > 10 else 'normal',
                'latestReplyTime': latest_reply.create_time.isoformat() if latest_reply else None
            })
        
        # 获取统计信息
        total_unread = len([m for m in message_list if m['isUnread']])
        total_replied = len([m for m in message_list if m['hasTeacherReply']])
        
        return jsonify(Result.success({
            'total': total,
            'page': page,
            'pageSize': page_size,
            'list': message_list,
            'statistics': {
                'totalMessages': total,
                'unreadCount': total_unread,
                'repliedCount': total_replied,
                'todayMessages': len([m for m in message_list 
                                    if (datetime.now() - datetime.fromisoformat(m['createTime'])).days == 0])
            }
        }, "获取消息列表成功"))
        
    except Exception as e:
        return jsonify(Result.error(500, f"获取消息列表失败: {str(e)}"))

@teacher_dashboard_bp.route('/messages/<comment_id>/reply', methods=['POST'])
@token_required
def reply_to_message(comment_id):
    """
    回复学生消息
    """
    try:
        user_id = request.user.get('user_id')
        user = Users.query.filter_by(id=user_id, is_deleted=False).first()
        
        if not is_teacher_or_admin(user):
            return jsonify(Result.error(403, "无权访问，需要教师或管理员权限"))
        
        # 检查原评论是否存在
        original_comment = VideoComment.query.get(comment_id)
        if not original_comment or original_comment.is_deleted:
            return jsonify(Result.error(404, "评论不存在"))
        
        # 获取请求数据
        data = request.get_json()
        content = data.get('content')
        
        if not content:
            return jsonify(Result.error(400, "回复内容不能为空"))
        
        # 创建回复
        reply = VideoComment(
            content=content,
            video_id=original_comment.video_id,
            user_id=user_id,
            parent_id=comment_id,
            time_point=original_comment.time_point,  # 继承原评论的时间点
            create_time=datetime.now(),
            likes=0,
            is_deleted=False
        )
        
        db.session.add(reply)
        db.session.commit()
        
        return jsonify(Result.success({
            'id': reply.id,
            'content': reply.content,
            'createTime': reply.create_time.isoformat(),
            'teacherName': user.username
        }, "回复成功"))
        
    except Exception as e:
        db.session.rollback()
        return jsonify(Result.error(500, f"回复失败: {str(e)}"))

@teacher_dashboard_bp.route('/courses', methods=['GET'])
@token_required
def get_teacher_courses():
    """
    获取教师课程列表（用于筛选）
    """
    try:
        user_id = request.user.get('user_id')
        user = Users.query.filter_by(id=user_id, is_deleted=False).first()
        
        if not is_teacher_or_admin(user):
            return jsonify(Result.error(403, "无权访问，需要教师或管理员权限"))
        
        if user.role == 'teacher':
            courses = Course.query.filter_by(teacher_id=user_id, is_deleted=False).all()
        else:
            courses = Course.query.filter_by(is_deleted=False).all()
        
        course_list = []
        for course in courses:
            course_list.append({
                'id': str(course.id),
                'name': course.name,
                'status': course.status,
                'studentCount': db.session.query(StudentCourseEnrollment).join(
                    Users, StudentCourseEnrollment.student_id == Users.id
                ).filter(
                    StudentCourseEnrollment.course_id == course.id,
                    Users.is_deleted == False
                ).count()
            })
        
        return jsonify(Result.success(course_list, "获取课程列表成功"))
        
    except Exception as e:
        return jsonify(Result.error(500, f"获取课程列表失败: {str(e)}"))
