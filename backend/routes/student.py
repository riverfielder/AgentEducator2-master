import os
import traceback
from flask import Blueprint, request, jsonify, current_app
from models.models import db, Course, Users, UserPermission, StudentCourseEnrollment, Video, UserVideoProgress
from utils.result import Result
from utils.auth import token_required, get_current_user_id
from sqlalchemy import or_
from datetime import datetime, timedelta
import os
import traceback

# 创建学生相关的蓝图
student_bp = Blueprint("student", __name__)

def format_last_study_time(last_study_time):
    """格式化最后学习时间"""
    if not last_study_time:
        return "未知"
    
    now = datetime.now()
    diff = now - last_study_time
    
    if diff.days == 0:
        if diff.seconds < 3600:
            return f"{diff.seconds // 60}分钟前"
        else:
            return f"{diff.seconds // 3600}小时前"
    elif diff.days == 1:
        return "昨天"
    else:
        return f"{diff.days}天前"

@student_bp.route('/courses', methods=['GET'])
def list_student_courses():
    """
    获取学生可访问的课程列表接口
    可选参数: page, pageSize, public (是否只获取公开课程), search (搜索知识点)
    未登录用户只能看到公开课程，已登录用户可以看到公开课程和自己有权限访问的课程
    """
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 10, type=int)
        public_only = request.args.get('public', 'false').lower() == 'true'
        search = request.args.get('search', '').strip()  # 新增搜索参数
        
        # 获取当前用户ID (从JWT获取)
        user_id = get_current_user_id()
        
        # 构建基本查询 - 只查询非删除的课程
        query = Course.query.filter_by(is_deleted=False)
        
        # 添加搜索条件
        if search:
            query = query.filter(Course.name.like(f'%{search}%'))
        
        if not user_id or public_only:
            # 未登录用户或明确请求公开课程，只能看到公开课程
            query = query.filter_by(is_public=True)
        else:
            # 已登录用户，可以看到:
            # 1. 公开课程
            # 2. 自己有权限访问的课程
            # 3. 自己已选修的课程
            
            # 查询用户的权限设置
            user_permission = UserPermission.query.filter_by(user_id=user_id).first()
            allowed_course_ids = []
            
            if user_permission:
                allowed_course_ids = user_permission.get_course_access()
            
            # 查询用户已选修的课程
            enrolled_courses = StudentCourseEnrollment.query.filter_by(student_id=user_id).all()
            enrolled_course_ids = [ec.course_id for ec in enrolled_courses]
            
            # 合并可访问的课程ID
            accessible_course_ids = list(set(allowed_course_ids + enrolled_course_ids))
            
            if accessible_course_ids:
                # 查询公开课程或用户有权限的课程
                query = query.filter(or_(
                    Course.is_public == True,  # 公开课程
                    Course.id.in_(accessible_course_ids)  # 用户有权限的课程
                ))
            else:
                # 没有特殊权限，只能看到公开课程
                query = query.filter_by(is_public=True)
        
        # 计算总数
        total = query.count()
        
        # 分页查询
        courses = query.order_by(Course.create_time.desc()) \
                      .offset((page - 1) * page_size) \
                      .limit(page_size) \
                      .all()
          # 构建响应数据
        course_list = []
        
        # 批量查询所有课程的学习人数（基于视频观看记录）
        course_ids = [course.id for course in courses]
        learner_counts = {}
        if course_ids:
            learner_count_query = db.session.query(
                Video.course_id,
                db.func.count(UserVideoProgress.user_id.distinct()).label('learner_count')
            ).join(
                UserVideoProgress, Video.id == UserVideoProgress.video_id
            ).filter(
                Video.course_id.in_(course_ids),
                Video.is_deleted == False,
                UserVideoProgress.last_position > 0  # 至少有观看记录
            ).group_by(Video.course_id).all()
            
            learner_counts = {course_id: count for course_id, count in learner_count_query}
        
        for course in courses:
            # 使用ORM关系获取教师信息
            teacher_info = {"id": 0, "name": "未分配", "avatar": None}
            if course.teacher:
                teacher_info = {
                    "id": course.teacher.id, 
                    "name": course.teacher.username,
                    "avatar": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{course.teacher.avatar}" or course.teacher.avatar or "/temp_img/avatar_1.jpg"
                }
            
            # 获取基于视频观看记录的学习人数
            actual_student_count = learner_counts.get(course.id, 0)
            
            course_list.append({
                "id": course.id,
                "name": course.name,
                "code": course.code,
                "description": course.description or "",
                "imageUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{course.image_url}" or course.image_url,
                "startDate": course.start_date if course.start_date else None,
                "endDate": course.end_date if course.end_date else None,
                "hours": course.hours,
                "studentCount": actual_student_count,
                "status": course.status,
                "semester": course.semester,
                "teacherInfo": teacher_info,
                "category": "未分类"  # 可根据需要添加分类
            })
        
        return jsonify(Result.success({
            "total": total,
            "page": page,
            "pageSize": page_size,
            "list": course_list
        }, "获取课程列表成功"))
        
    except Exception as e:
        import traceback
        current_app.logger.error(f"获取课程列表错误: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(400, f"获取课程列表失败: {str(e)}"))

@student_bp.route('/recommended-courses', methods=['GET'])
@token_required
def get_recommended_courses():
    """
    获取推荐课程列表接口
    基于协同过滤算法推荐课程：根据用户观看时长计算相似度，推荐相似用户观看过但当前用户未观看的课程
    """
    try:
        # 获取当前用户ID (从JWT获取)
        user_id = request.user.get('user_id')
        if not user_id:
            return jsonify(Result.error(401, "未登录"))
        
        # 1. 获取当前用户的课程观看时长数据
        current_user_watch_data = db.session.query(
            Video.course_id,
            db.func.sum(UserVideoProgress.last_position).label('total_watch_time')
        ).join(
            UserVideoProgress, Video.id == UserVideoProgress.video_id
        ).filter(
            UserVideoProgress.user_id == user_id,
            UserVideoProgress.last_position > 0
        ).group_by(Video.course_id).all()
        
        current_user_courses = {course_id: watch_time for course_id, watch_time in current_user_watch_data}
        
        recommended_courses = []
        
        if current_user_courses:
            # 2. 基于观看时长的协同过滤
            # 找到观看了相同课程的其他用户，并计算相似度
            similar_users_data = db.session.query(
                UserVideoProgress.user_id,
                Video.course_id,
                db.func.sum(UserVideoProgress.last_position).label('total_watch_time')
            ).join(
                Video, UserVideoProgress.video_id == Video.id
            ).filter(
                Video.course_id.in_(list(current_user_courses.keys())),
                UserVideoProgress.user_id != user_id,
                UserVideoProgress.last_position > 0
            ).group_by(
                UserVideoProgress.user_id, Video.course_id
            ).all()
            
            # 计算用户相似度
            user_similarities = {}
            for user_id_other, course_id, watch_time in similar_users_data:
                if user_id_other not in user_similarities:
                    user_similarities[user_id_other] = 0
                
                # 使用余弦相似度的简化版本：观看时长的相关性
                current_watch = current_user_courses.get(course_id, 0)
                if current_watch > 0 and watch_time > 0:
                    # 计算观看时长的相似度 (范围0-1)
                    min_time = min(current_watch, watch_time)
                    max_time = max(current_watch, watch_time)
                    similarity = min_time / max_time if max_time > 0 else 0
                    user_similarities[user_id_other] += similarity
            
            # 获取最相似的用户
            similar_users = sorted(user_similarities.items(), key=lambda x: x[1], reverse=True)[:10]
            similar_user_ids = [user_id for user_id, _ in similar_users]
            
            if similar_user_ids:
                # 3. 获取相似用户观看过但当前用户未观看的课程
                other_courses_query = db.session.query(
                    Video.course_id,
                    db.func.sum(UserVideoProgress.last_position).label('total_similar_watch_time'),
                    db.func.count(UserVideoProgress.user_id.distinct()).label('similar_user_count'
                )).join(
                    UserVideoProgress, Video.id == UserVideoProgress.video_id
                ).filter(
                    UserVideoProgress.user_id.in_(similar_user_ids),
                    UserVideoProgress.last_position > 0,
                    ~Video.course_id.in_(list(current_user_courses.keys()))  # 排除当前用户已观看的课程
                ).group_by(Video.course_id).all()
                  # 获取推荐课程的详细信息
                recommended_course_ids = [course_id for course_id, _, _ in other_courses_query]
                
                if recommended_course_ids:
                    courses_info = db.session.query(
                        Course.id,
                        Course.name,
                        Course.code,
                        Course.image_url,
                        Course.hours,
                        Course.teacher_id,
                        Course.is_public
                    ).filter(
                        Course.id.in_(recommended_course_ids),
                        Course.is_deleted == False
                    ).all()
                    
                    # 创建课程信息映射
                    course_info_map = {course.id: course for course in courses_info}
                    
                    # 批量查询推荐课程的学习人数
                    learner_counts = {}
                    if recommended_course_ids:
                        learner_count_query = db.session.query(
                            Video.course_id,
                            db.func.count(UserVideoProgress.user_id.distinct()).label('learner_count')
                        ).join(
                            UserVideoProgress, Video.id == UserVideoProgress.video_id
                        ).filter(
                            Video.course_id.in_(recommended_course_ids),
                            Video.is_deleted == False,
                            UserVideoProgress.last_position > 0
                        ).group_by(Video.course_id).all()
                        
                        learner_counts = {course_id: count for course_id, count in learner_count_query}
                    
                    # 按推荐度排序并构建推荐列表
                    for course_id, total_watch_time, user_count in sorted(
                        other_courses_query, 
                        key=lambda x: (x[1], x[2]), 
                        reverse=True
                    )[:4]:
                        course_info = course_info_map.get(course_id)
                        if not course_info:
                            continue
                        teacher_info = {"id": 0, "name": "未分配", "avatar": None}
                        if course_info.teacher_id:
                            teacher = Users.query.get(course_info.teacher_id)
                            if teacher:
                                teacher_info = {
                                    "id": teacher.id, 
                                    "name": teacher.username,
                                    "avatar": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{teacher.avatar}" or teacher.avatar or "/temp_img/avatar_1.jpg"
                                }                        # 计算推荐评分（基于观看时长和相似用户数量）
                        watch_hours = (total_watch_time or 0) / 3600
                        # 获取基于视频观看记录的学习人数
                        actual_student_count = learner_counts.get(course_id, 0)
                        
                        recommended_courses.append({
                            "id": course_info.id,
                            "name": course_info.name,
                            "code": course_info.code,
                            "imageUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{course_info.image_url}" or course_info.image_url,
                            "hours": course_info.hours,
                            "studentCount": actual_student_count,
                            "teacherInfo": teacher_info,
                            "category": "协同推荐",
                            "similarityScore": user_count,
                            "isPublic": course_info.is_public
                        })
        # 4. 过滤当前用户能访问的课程
        user_permission = UserPermission.query.filter_by(user_id=user_id).first()
        allowed_course_ids = []
        if user_permission:
            allowed_course_ids = user_permission.get_course_access()
        
        # 查询用户已选修的课程
        enrolled_courses = StudentCourseEnrollment.query.filter_by(student_id=user_id).all()
        enrolled_course_ids = [ec.course_id for ec in enrolled_courses]
        
        # 合并可访问的课程ID
        accessible_course_ids = list(set(allowed_course_ids + enrolled_course_ids))
        
        # 过滤推荐课程，只保留用户可访问的
        filtered_recommendations = []
        for course in recommended_courses:
            # 可以访问的条件：公开课程 或 在用户权限范围内
            if course["isPublic"] or (accessible_course_ids and course["id"] in accessible_course_ids):
                # 移除内部字段
                course.pop("isPublic", None)
                filtered_recommendations.append(course)
        
        recommended_courses = filtered_recommendations
        
        # 5. 如果协同过滤推荐不足4个，用热门课程补充
        if len(recommended_courses) < 4:            # 获取热门课程（按实际学习人数排序）作为补充推荐
            fallback_count = 4 - len(recommended_courses)
            
            # 排除已推荐的课程和已观看的课程
            exclude_course_ids = [course["id"] for course in recommended_courses] + list(current_user_courses.keys())
            
            # 查询课程的实际学习人数
            popular_courses_query = db.session.query(
                Course.id,
                Course.name,
                Course.code,
                Course.image_url,
                Course.hours,
                Course.teacher_id,
                Course.is_public,
                db.func.count(UserVideoProgress.user_id.distinct()).label('learner_count')
            ).join(
                Video, Course.id == Video.course_id
            ).join(
                UserVideoProgress, Video.id == UserVideoProgress.video_id
            ).filter(
                Course.is_deleted == False,
                Video.is_deleted == False,
                UserVideoProgress.last_position > 0,
                ~Course.id.in_(exclude_course_ids) if exclude_course_ids else True
            )
            
            # 应用权限过滤
            if accessible_course_ids:
                popular_courses_query = popular_courses_query.filter(
                    or_(
                        Course.is_public == True,
                        Course.id.in_(accessible_course_ids)
                    )
                )
            else:
                popular_courses_query = popular_courses_query.filter(Course.is_public == True)
            
            popular_courses = popular_courses_query.group_by(
                Course.id
            ).order_by(
                db.desc('learner_count')
            ).limit(fallback_count).all()
            
            for course_data in popular_courses:
                teacher_info = {"id": 0, "name": "未分配", "avatar": None}
                if course_data.teacher_id:
                    teacher = Users.query.get(course_data.teacher_id)
                    if teacher:
                        teacher_info = {
                            "id": teacher.id, 
                            "name": teacher.username,
                            "avatar": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{teacher.avatar}" or teacher.avatar or "/temp_img/avatar_1.jpg"
                        }
                
                recommended_courses.append({
                    "id": course_data.id,
                    "name": course_data.name,
                    "code": course_data.code,
                    "imageUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{course_data.image_url}" or course_data.image_url,
                    "hours": course_data.hours,
                    "studentCount": course_data.learner_count,
                    "teacherInfo": teacher_info,
                    "category": "热门推荐",
                    "similarityScore": 0
                })
        
        return jsonify(Result.success(recommended_courses, "获取推荐课程成功"))
        
    except Exception as e:
        import traceback
        current_app.logger.error(f"获取推荐课程错误: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(400, f"获取推荐课程失败: {str(e)}"))

@student_bp.route('/homepage-data', methods=['GET'])
def get_homepage_data():
    """
    获取首页数据接口
    包含：大家都在学、继续学习、从上次中断的地方继续
    """
    try:
        # 获取当前用户ID (从JWT获取，可能为None)
        user_id = get_current_user_id()
        
        result_data = {}
        
        # 1. 大家都在学 - 所有账号的学习记录加起来最长的课程（总观看时长最多）
        popular_courses_query = db.session.query(
            Course.id,
            Course.name,
            Course.code,
            Course.image_url,
            Course.hours,
            Course.student_count,
            Course.teacher_id,
            db.func.sum(UserVideoProgress.last_position).label('total_watch_time'),
            db.func.count(UserVideoProgress.user_id.distinct()).label('learner_count')
        ).join(
            Video, Course.id == Video.course_id
        ).join(
            UserVideoProgress, Video.id == UserVideoProgress.video_id
        ).filter(
            Course.is_deleted == False,
            Video.is_deleted == False,
            Course.is_public == True  # 只统计公开课程
        ).group_by(
            Course.id
        ).order_by(
            db.desc('total_watch_time')
        ).limit(4).all()
        popular_courses = []
        for course_data in popular_courses_query:
            # 获取教师信息
            teacher = Users.query.get(course_data.teacher_id)
            teacher_info = {"id": 0, "name": "未分配", "avatar": None}
            if teacher:
                teacher_info = {
                    "id": teacher.id, 
                    "name": teacher.username,
                    "avatar": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{teacher.avatar}" or teacher.avatar or "/temp_img/avatar_1.jpg"
                }
            
            # 计算总观看时长（转换为小时）
            total_hours = round((course_data.total_watch_time or 0) / 3600, 1)
            
            popular_courses.append({
                "id": course_data.id,
                "name": course_data.name,
                "code": course_data.code,
                "imageUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{course_data.image_url}" or course_data.image_url,
                "teacherInfo": teacher_info,
                "totalWatchTime": total_hours,
                "learnerCount": course_data.learner_count,
                "category": "大家都在学"
            })
        
        result_data["popularCourses"] = popular_courses
          # 2. 继续学习 - 当前用户已经学习最长时间的课程
        continue_learning_courses = []
        if user_id:
            continue_courses_query = db.session.query(
                Course.id,
                Course.name,
                Course.code,
                Course.image_url,
                Course.hours,
                Course.teacher_id,
                db.func.sum(UserVideoProgress.last_position).label('user_watch_time'),
                db.func.count(UserVideoProgress.video_id).label('watched_videos'),
                db.func.max(UserVideoProgress.update_time).label('last_study_time')
            ).join(
                Video, Course.id == Video.course_id
            ).join(
                UserVideoProgress, Video.id == UserVideoProgress.video_id
            ).filter(
                Course.is_deleted == False,
                Video.is_deleted == False,
                UserVideoProgress.user_id == user_id,
            ).group_by(
                Course.id
            ).order_by(
                db.desc('user_watch_time')
            ).limit(3).all()
            
            # 批量查询继续学习课程的实际学习人数（与 learner_count 逻辑一致）
            continue_course_ids = [course_data.id for course_data in continue_courses_query]
            continue_learner_counts = {}
            if continue_course_ids:
                continue_learner_count_query = db.session.query(
                    Video.course_id,
                    db.func.count(UserVideoProgress.user_id.distinct()).label('learner_count')
                ).join(
                    UserVideoProgress, Video.id == UserVideoProgress.video_id
                ).filter(
                    Video.course_id.in_(continue_course_ids),
                    Video.is_deleted == False,
                    UserVideoProgress.last_position > 0  # 至少有观看记录
                ).group_by(Video.course_id).all()
                
                continue_learner_counts = {course_id: count for course_id, count in continue_learner_count_query}
            
            for course_data in continue_courses_query:
                # 获取教师信息
                teacher = Users.query.get(course_data.teacher_id)
                teacher_info = {"id": 0, "name": "未分配", "avatar": None}
                if teacher:
                    teacher_info = {
                        "id": teacher.id, 
                        "name": teacher.username,
                        "avatar": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{teacher.avatar}" or teacher.avatar or "/temp_img/avatar_1.jpg"
                    }
                  # 计算用户观看时长（转换为小时）
                user_hours = round((course_data.user_watch_time or 0) / 3600, 1)
                
                # 计算学习进度百分比（基于已完成的视频数量，与learning-progress接口保持一致）
                total_videos = Video.query.filter_by(course_id=course_data.id, is_deleted=False).count()
                
                # 查询用户在该课程中已完成的视频数量
                completed_videos = db.session.query(
                    db.func.count(UserVideoProgress.id)
                ).join(
                    Video, UserVideoProgress.video_id == Video.id
                ).filter(
                    Video.course_id == course_data.id,
                    Video.is_deleted == False,
                    UserVideoProgress.user_id == user_id,
                    UserVideoProgress.completed == True
                ).scalar() or 0
                
                progress_percent = round((completed_videos / total_videos * 100) if total_videos > 0 else 0, 1)
                
                # 获取基于视频观看记录的实际学习人数（与 learner_count 逻辑一致）
                actual_student_count = continue_learner_counts.get(course_data.id, 0)
                
                continue_learning_courses.append({
                    "id": course_data.id,
                    "name": course_data.name,
                    "code": course_data.code,
                    "imageUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{course_data.image_url}" or course_data.image_url,
                    "hours": course_data.hours,
                    "studentCount": actual_student_count,
                    "teacherInfo": teacher_info,
                    "userWatchTime": user_hours,
                    "watchedVideos": course_data.watched_videos,  # 有观看记录的视频数量
                    "completedVideos": completed_videos,  # 已完成的视频数量（新增）
                    "totalVideos": total_videos,  # 总视频数量（新增）
                    "lastStudyTime": course_data.last_study_time.isoformat() if course_data.last_study_time else None,
                    "progressPercent": progress_percent,  # 基于已完成视频的进度
                    "category": "继续学习"
                })
        
        result_data["continueLearningCourses"] = continue_learning_courses
          # 3. 从上次中断的地方继续 - 用户最近观看但未完成的视频（只展示最新的一条）
        recent_videos = []
        if user_id:
            recent_videos_query = db.session.query(
                Video.id,
                Video.title,
                Video.cover_url,
                Video.duration,
                Video.course_id,
                Course.name.label('course_name'),
                UserVideoProgress.last_position,
                UserVideoProgress.progress,
                UserVideoProgress.update_time,
                UserVideoProgress.completed
            ).join(
                Course, Video.course_id == Course.id
            ).join(
                UserVideoProgress, Video.id == UserVideoProgress.video_id
            ).filter(
                Video.is_deleted == False,
                Course.is_deleted == False,
                UserVideoProgress.user_id == user_id,
                UserVideoProgress.completed == False,  # 未完成观看
                UserVideoProgress.last_position > 30  # 至少观看了30秒
            ).order_by(
                db.desc(UserVideoProgress.update_time)
            ).limit(1).all()  # 只获取最新的一条记录
            
            for video_data in recent_videos_query:
                # 计算观看进度百分比
                progress_percent = round(video_data.progress * 100, 1) if video_data.progress else 0
                
                # 格式化观看位置为 mm:ss 格式
                last_pos_minutes = int(video_data.last_position // 60)
                last_pos_seconds = int(video_data.last_position % 60)
                last_position_formatted = f"{last_pos_minutes:02d}:{last_pos_seconds:02d}"
                
                # 格式化总时长
                duration_minutes = int(video_data.duration // 60)
                duration_seconds = int(video_data.duration % 60)
                duration_formatted = f"{duration_minutes:02d}:{duration_seconds:02d}"
                
                recent_videos.append({
                    "videoId": video_data.id,
                    "courseId": video_data.course_id,
                    "title": video_data.title,
                    "courseName": video_data.course_name,
                    "coverUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{video_data.cover_url}" or video_data.cover_url,
                    "duration": video_data.duration,
                    "durationFormatted": duration_formatted,
                    "lastPosition": video_data.last_position,
                    "lastPositionFormatted": last_position_formatted,
                    "progressPercent": progress_percent,
                    "lastWatchTime": video_data.update_time.isoformat() if video_data.update_time else None,
                    "watchUrl": f"/course/{video_data.course_id}/video/{video_data.id}?t={int(video_data.last_position)}"
                })
        
        result_data["recentVideos"] = recent_videos
        
        return jsonify(Result.success(result_data, "获取首页数据成功"))
        
    except Exception as e:
        import traceback
        current_app.logger.error(f"获取首页数据错误: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(400, f"获取首页数据失败: {str(e)}"))

@student_bp.route('/learning-progress', methods=['GET'])
@token_required
def get_learning_progress():
    """
    获取学生学习进度数据接口
    包含：在学课程数、学习时长、已获证书、平均评分、课程进度列表
    """
    try:
        # 获取当前用户ID
        user_id = request.user.get('user_id')
        if not user_id:
            return jsonify(Result.error(401, "未登录"))
        
        # 1. 统计数据
        # 在学课程数 - 用户有观看记录且课程仍在进行的课程
        active_courses_count = db.session.query(
            db.func.count(db.distinct(Video.course_id))
        ).join(
            Course, Video.course_id == Course.id
        ).filter(
            Course.is_deleted == False,
            Course.status.in_([0, 1])  # 即将开始或进行中
        ).scalar() or 0
        
        # 总学习时长（小时）
        total_study_hours = db.session.query(
            db.func.sum(UserVideoProgress.last_position)
        ).filter(
            UserVideoProgress.user_id == user_id,
            UserVideoProgress.last_position > 0
        ).scalar() or 0
        total_study_hours = round(total_study_hours / 3600, 1)
          # 知识点掌握程度统计
        from models.models import KnowledgePointMastery
        mastery_stats = db.session.query(
            db.func.count(KnowledgePointMastery.id).label('total_points'),
            db.func.avg(KnowledgePointMastery.mastery_level).label('avg_mastery'),
            db.func.count(db.case((KnowledgePointMastery.mastery_level >= 0.5, 1))).label('mastered_points')
        ).filter(
            KnowledgePointMastery.user_id == user_id
        ).first()
        
        total_knowledge_points = mastery_stats.total_points or 0
        avg_mastery_level = round((mastery_stats.avg_mastery or 0) * 100, 1)  # 转换为百分比
        mastered_points = mastery_stats.mastered_points or 0
          # 2. 课程进度列表
        courses_progress = db.session.query(
            Course.id,
            Course.name,
            Course.image_url,
            Course.hours,
            Course.end_date,
            db.func.count(Video.id).label('total_videos'),
            db.func.count(
                db.case((UserVideoProgress.completed == True, 1), else_=None)
            ).label('completed_videos'),
            db.func.sum(UserVideoProgress.last_position).label('watch_time'),
            db.func.max(UserVideoProgress.update_time).label('last_study_time')
        ).join(
            Video, Course.id == Video.course_id
        ).outerjoin(
            UserVideoProgress,
            db.and_(
                Video.id == UserVideoProgress.video_id,
                UserVideoProgress.user_id == user_id
            )
        ).filter(
            Course.is_deleted == False,
            Video.is_deleted == False
        ).group_by(Course.id).having(
            db.func.sum(UserVideoProgress.last_position) > 0  # 只显示有观看记录的课程
        ).order_by(
            db.desc('last_study_time')
        ).all()
        
        course_list = []
        for course_data in courses_progress:
            # 计算进度百分比
            if course_data.total_videos > 0:
                video_progress = (course_data.completed_videos / course_data.total_videos) * 100
            else:
                video_progress = 0
            
            # 根据视频进度计算课时进度
            completed_hours = round((video_progress / 100) * course_data.hours, 1)
            
            # 计算剩余天数
            remaining_days = 0
            if course_data.end_date:
                from datetime import datetime
                end_date = datetime.fromtimestamp(course_data.end_date / 1000)  # 假设时间戳是毫秒
                remaining_days = max(0, (end_date - datetime.now()).days)
            
            # 格式化最后学习时间
            last_study_formatted = "未知"
            if course_data.last_study_time:
                from datetime import datetime, timedelta
                now = datetime.now()
                diff = now - course_data.last_study_time
                
                if diff.days == 0:
                    if diff.seconds < 3600:
                        last_study_formatted = f"{diff.seconds // 60}分钟前"
                    else:
                        last_study_formatted = f"{diff.seconds // 3600}小时前"
                elif diff.days == 1:
                    last_study_formatted = "昨天"
                else:
                    last_study_formatted = f"{diff.days}天前"
            
            course_list.append({
                "id": course_data.id,
                "name": course_data.name,
                "image": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{course_data.image_url}" or course_data.image_url,
                "completedLessons": completed_hours,
                "totalLessons": course_data.hours,
                "progress": round(video_progress, 1),
                "lastStudyTime": last_study_formatted,
                "remainingDays": remaining_days
            })
        
        result_data = {
            "stats": {
                "activeCourses": active_courses_count,
                "studyHours": total_study_hours,
                "totalKnowledgePoints": total_knowledge_points,
            "avgMasteryLevel": avg_mastery_level,
            "masteredPoints": mastered_points
            },
            "courses": course_list
        }
        
        return jsonify(Result.success(result_data, "获取学习进度成功"))
        
    except Exception as e:
        current_app.logger.error(f"获取学习进度错误: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(400, f"获取学习进度失败: {str(e)}"))
