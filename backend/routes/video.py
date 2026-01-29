from flask import Blueprint, request, jsonify, current_app
from models.models import VideoKeyframe, VideoVectorIndex, db, Video, VideoComment, UserVideoProgress, Course, Users, VideoProcessingTask, CommentLike, VideoKeyword, VideoSummary
from utils.result import Result
from datetime import datetime
from sqlalchemy import desc, or_
from sqlalchemy.orm import joinedload
from utils.auth import get_current_user_id, token_required, is_teacher_or_admin
import uuid
import os
from sqlalchemy import func

# 创建视频相关的蓝图
video_bp = Blueprint("video", __name__)

@video_bp.route('', methods=['GET'])
@token_required
def get_videos():
    """
    获取视频列表接口
    """
    try:
        # 获取查询参数
        course_id = request.args.get('courseId', type=str)  # 修改为str类型，因为UUID在URL中以字符串形式传递
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 100, type=int)
        
        # 获取当前用户ID (现在从JWT获取)
        user_id = request.user.get('user_id')
        
        # 将字符串UUID转换为UUID对象（如果需要）
        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                return jsonify(Result.error(400, "用户ID格式不正确"))
        
        # 构建查询 - 只查询当前用户的课程中的视频
        if course_id:
            try:
                # 转换为UUID对象进行过滤
                course_uuid = uuid.UUID(course_id)
                # 验证课程是否属于当前用户
                course = Course.query.filter_by(id=course_uuid, teacher_id=user_id, is_deleted=False).first()
                if not course:
                    return jsonify(Result.error(403, "无权访问该课程的视频"))
                query = Video.query.filter_by(course_id=course_uuid, is_deleted=False)
            except ValueError:
                # 如果UUID格式错误，返回错误信息
                return jsonify(Result.error(400, "课程ID格式不正确"))
        else:
            # 获取用户的所有课程
            user_courses = Course.query.filter_by(teacher_id=user_id, is_deleted=False).all()
            course_ids = [course.id for course in user_courses]
            
            # 只查询用户课程中的视频
            query = Video.query.filter(
                Video.course_id.in_(course_ids),
                Video.is_deleted == False
            )
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        videos = query.order_by(Video.upload_time.desc()) \
                      .offset((page - 1) * page_size) \
                      .limit(page_size) \
                      .all()
        
        # 获取用户的观看进度
        video_ids = [video.id for video in videos]
        user_progress = {}
        
        if user_id:
            progress_records = UserVideoProgress.query.filter(
                UserVideoProgress.user_id == user_id,
                UserVideoProgress.video_id.in_(video_ids)
            ).all()
            
            for record in progress_records:
                user_progress[record.video_id] = {
                    "progress": record.progress,
                    "last_position": record.last_position,
                    "completed": record.completed
                }
        
        # 获取视频处理状态
        processing_status_map = {}
        if video_ids:
            # 查询每个视频的最新处理任务状态
            latest_tasks = db.session.query(VideoProcessingTask.video_id, VideoProcessingTask.status)\
                .filter(VideoProcessingTask.video_id.in_(video_ids))\
                .order_by(VideoProcessingTask.video_id, VideoProcessingTask.start_time.desc())\
                .all()
            
            # 获取每个视频的最新状态
            for video_id, status in latest_tasks:
                if video_id not in processing_status_map:
                    processing_status_map[video_id] = status
        
        # 构建响应数据
        video_list = []
        for video in videos:
            # 获取视频的观看状态
            progress_info = user_progress.get(video.id, {})
            has_watched = video.id in user_progress
            watch_progress = progress_info.get("progress", 0)
            
            # 获取处理状态
            processing_status = processing_status_map.get(video.id, 'unprocessed')
            
            video_list.append({
                "id": video.id,
                "title": video.title,
                "description": video.description,
                "coverUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{video.cover_url}" or video.cover_url,
                "duration": video.duration,
                "uploadTime": video.upload_time.isoformat(),
                "viewCount": video.view_count,
                "commentCount": video.comment_count,
                "hasWatched": has_watched,
                "watchProgress": watch_progress,
                "chapterId": str(video.chapter_id) if video.chapter_id else None,
                "courseId": str(video.course_id),
                "processingStatus": processing_status
            })
        
        return jsonify(Result.success({
            "total": total,
            "page": page,
            "pageSize": page_size,
            "list": video_list
        }, "获取视频列表成功"))
        
    except Exception as e:
        current_app.logger.error(f"获取视频列表错误: {str(e)}")
        return jsonify(Result.error(400, f"获取视频列表失败: {str(e)}"))

@video_bp.route('/<video_id>', methods=['GET'])
@token_required
def get_video_detail(video_id):
    """
    获取视频详情接口
    """
    try:
        # 获取当前用户ID (现在从JWT获取)
        user_id = request.user.get('user_id')
        
        # 查询视频，包括关联的课程信息
        video = Video.query.options(
            joinedload(Video.course)
        ).get(video_id)
        
        # 检查视频是否存在
        if not video or video.is_deleted:
            return jsonify(Result.error(404, "视频不存在"))
        
        # 获取用户观看进度
        user_progress = None
        if user_id:
            user_progress = UserVideoProgress.query.filter_by(
                user_id=user_id,
                video_id=video_id
            ).first()
        
        # 使用ORM关系获取课程名称和教师信息
        course_name = video.course.name if video.course else "未知课程"
        teacher_name = video.course.teacher.username if (video.course and video.course.teacher) else "未分配"
        
        # 检查是否存在视频总结
        has_summary = video.summary is not None
        
        # 如果有总结，获取章节信息
        if has_summary and video.summary.sections:
            chapters = video.summary.get_sections()
        else:
            # 默认章节
            chapters = [{"title": "简介", "timePoint": 0}]
          # 构建视频详情
        watch_progress = user_progress.progress if user_progress else 0
        last_watch_time = user_progress.last_position if user_progress else 0
        
        import dotenv
        dotenv.load_dotenv()
          # 获取有效的播放地址
        play_url = video.effective_play_url
        
        # 如果是调试模式，使用本地地址
        if os.getenv('IS_DEBUG') == 'True':
            play_url = f"http://localhost:5000{video.video_url}"
        
        video_detail = {
            "id": video.id,
            "title": video.title,
            "description": video.description,
            "coverUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{video.cover_url}" or video.cover_url,
            "videoUrl": play_url,
            "duration": video.duration,
            "courseId": video.course_id,
            "courseName": course_name,
            "teacher": teacher_name,
            "uploadTime": video.upload_time.isoformat(),
            "viewCount": video.view_count,
            "commentCount": video.comment_count,
            "watchProgress": watch_progress,
            "lastWatchTime": last_watch_time,
            "resolutions": ["360p", "720p", "1080p"],  # 实际应用中应基于实际分辨率
            "hasSummary": has_summary,
            "chapters": chapters,            "ossUploaded": False,  # 不再使用OSS
            "hasLocalFile": video.is_local_file_exists()  # 本地文件存在状态
        }
        
        # 增加视频浏览量
        video.view_count += 1
        db.session.commit()
        
        return jsonify(Result.success(video_detail, "获取视频详情成功"))
        
    except Exception as e:
        current_app.logger.error(f"获取视频详情错误: {str(e)}")
        return jsonify(Result.error(400, f"获取视频详情失败: {str(e)}"))

@video_bp.route('/search', methods=['GET'])
@token_required
def search_videos():
    """
    搜索视频接口
    """
    try:
        # 获取查询参数
        keyword = request.args.get('keyword', '')
        course_id = request.args.get('courseId', type=str)  # 修改为str类型，因为UUID在URL中以字符串形式传递
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 10, type=int)
        
        if not keyword:
            return jsonify(Result.error(400, "请提供搜索知识点"))
        
        # 构建查询
        query = Video.query.filter_by(is_deleted=False)
        
        # 知识点搜索
        query = query.filter(
            or_(
                Video.title.contains(keyword),
                Video.description.contains(keyword)
            )
        )
        
        # 如果指定了课程ID，则筛选
        if course_id:
            try:
                # 转换为UUID对象进行过滤
                course_uuid = uuid.UUID(course_id)
                query = query.filter_by(course_id=course_uuid)
            except ValueError:
                # 如果UUID格式错误，返回错误信息
                return jsonify(Result.error(400, "课程ID格式不正确"))
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        videos = query.order_by(Video.upload_time.desc()) \
                      .offset((page - 1) * page_size) \
                      .limit(page_size) \
                      .all()
        
        # 构建响应数据
        video_list = []
        for video in videos:
            # 在实际应用中，这里应该使用NLP或搜索引擎技术提取知识点匹配的段落
            # 简化实现：生成两个匹配点
            middle_point = video.duration // 3
            three_quarter_point = video.duration * 3 // 4
            
            match_points = [
                {
                    "timePoint": middle_point,
                    "text": f"在讲解{keyword}的基本概念时...",
                    "confidence": 0.95
                },
                {
                    "timePoint": three_quarter_point,
                    "text": f"关于{keyword}的进阶应用包括...",
                    "confidence": 0.89
                }
            ]
            
            video_list.append({
                "id": video.id,
                "title": video.title,
                "description": video.description,
                "coverUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{video.cover_url}" or video.cover_url,
                "duration": video.duration,
                "uploadTime": video.upload_time.isoformat(),
                "viewCount": video.view_count,
                "commentCount": video.comment_count,
                "matchPoints": match_points
            })
        
        return jsonify(Result.success({
            "total": total,
            "page": page,
            "pageSize": page_size,
            "keyword": keyword,
            "list": video_list
        }, "搜索成功"))
        
    except Exception as e:
        current_app.logger.error(f"搜索视频错误: {str(e)}")
        return jsonify(Result.error(400, f"搜索失败: {str(e)}"))

@video_bp.route('/<video_id>/progress', methods=['POST'])
@token_required
def update_video_progress(video_id):
    """
    更新观看进度接口
    """
    try:
        # 获取当前用户ID (现在从JWT获取)
        user_id = request.user.get('user_id')
        if not user_id:
            return jsonify(Result.error(401, "未登录"))
            
        # 检查视频是否存在
        video = Video.query.get(video_id)
        if not video or video.is_deleted:
            return jsonify(Result.error(404, "视频不存在"))
        
        # 获取请求数据
        data = request.get_json()
        current_time = data.get('currentTime')
        duration = data.get('duration')
        completed = data.get('completed', False)
        
        if current_time is None or duration is None:
            return jsonify(Result.error(400, "缺少必要参数"))
        
        # 计算进度
        progress = min(1.0, max(0.0, current_time / duration)) if duration > 0 else 0
        
        # 更新或创建进度记录
        progress_record = UserVideoProgress.query.filter_by(
            user_id=user_id,
            video_id=video_id
        ).first()
        
        if progress_record:
            progress_record.progress = progress
            progress_record.last_position = current_time
            progress_record.completed = completed
            progress_record.update_time = datetime.now()
        else:
            progress_record = UserVideoProgress(
                user_id=user_id,
                video_id=video_id,
                progress=progress,
                last_position=current_time,
                completed=completed
            )
            db.session.add(progress_record)
        
        db.session.commit()
        
        return jsonify(Result.success({
            "videoId": video_id,
            "progress": progress,
            "lastWatchTime": current_time,
            "completed": completed
        }, "进度更新成功"))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新视频进度错误: {str(e)}")
        return jsonify(Result.error(400, f"更新进度失败: {str(e)}"))

@video_bp.route('/<video_id>/comments', methods=['GET'])
@token_required
def get_video_comments(video_id):
    """
    获取视频评论列表接口
    """
    try:
        # 获取当前用户ID (现在从JWT获取)
        user_id = request.user.get('user_id')
        user:Users= Users.query.get(user_id)
        print(user)
        # 检查视频是否存在
        video = Video.query.get(video_id)
        if not video or video.is_deleted:
            return jsonify(Result.error(404, "视频不存在"))
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 10, type=int)
        sort_by = request.args.get('sortBy', 'time')  # time或likes
        
        # 构建排序
        if sort_by == 'likes':
            order_clause = VideoComment.likes.desc()
        else:  # 默认按时间排序
            order_clause = VideoComment.create_time.desc()
        
        # 查询评论（只查询顶级评论，不包括回复）
        query = VideoComment.query.filter_by(
            video_id=video_id,
            is_deleted=False,
            parent_id=None  # 只查询顶级评论
        )
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        comments = query.order_by(order_clause) \
                       .offset((page - 1) * page_size) \
                       .limit(page_size) \
                       .all()
        
        # 获取用户点赞记录
        liked_comment_ids = set()
        if user_id:
            likes = CommentLike.query.filter_by(user_id=user_id).all()
            liked_comment_ids = {like.comment_id for like in likes}
        
        # 构建评论列表
        comment_list = []
        for comment in comments:
            # 使用ORM关系获取用户信息
            comment_username = comment.user.username if comment.user else "未知用户"
            
            # 使用ORM关系获取回复
            replies = comment.replies.filter_by(is_deleted=False).order_by(VideoComment.create_time).all()
            
            # 构建回复列表
            reply_list = []
            for reply in replies:
                # 使用ORM关系获取回复用户信息
                reply_username = reply.user.username if reply.user else "未知用户"
                
                reply_list.append({
                    "id": reply.id,
                    "content": reply.content,
                    "userId": reply.user_id,
                    "userName": reply_username,
                    "avatar": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{reply.user.avatar}" or reply.user.avatar,
                    "createTime": reply.create_time.isoformat(),
                    "likes": reply.likes,
                    "liked": reply.id in liked_comment_ids
                })
            
            # 构建评论对象
            comment_list.append({
                "id": comment.id,
                "content": comment.content,
                "videoId": comment.video_id,
                "userId": comment.user_id,
                "userName": comment_username,
                "avatar": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{comment.user.avatar}" or comment.user.avatar,
                "timePoint": comment.time_point,
                "createTime": comment.create_time.isoformat(),
                "likes": comment.likes,
                "liked": comment.id in liked_comment_ids,
                "replies": reply_list
            })
        
        return jsonify(Result.success({
            "total": total,
            "page": page,
            "pageSize": page_size,
            "list": comment_list
        }, "获取评论成功"))
        
    except Exception as e:
        current_app.logger.error(f"获取视频评论错误: {str(e)}")
        return jsonify(Result.error(400, f"获取评论失败: {str(e)}"))

@video_bp.route('/<video_id>/comments', methods=['POST'])
@token_required
def add_video_comment(video_id):
    """
    添加视频评论接口
    """
    try:
        # 获取当前用户ID (现在从JWT获取)
        user_id = request.user.get('user_id')
        if not user_id:
            return jsonify(Result.error(401, "未登录"))
        user:Users= Users.query.get(user_id)
        # 检查视频是否存在
        video = Video.query.get(video_id)
        if not video or video.is_deleted:
            return jsonify(Result.error(404, "视频不存在"))
        
        # 获取请求数据
        data = request.get_json()
        content = data.get('content')
        time_point = data.get('timePoint')
        parent_id = data.get('parentId')  # 如果是回复其他评论
        
        if not content:
            return jsonify(Result.error(400, "评论内容不能为空"))
        
        # 如果是回复，检查父评论是否存在
        if parent_id:
            parent_comment = VideoComment.query.get(parent_id)
            if not parent_comment or parent_comment.is_deleted:
                return jsonify(Result.error(404, "回复的评论不存在"))
        
        # 创建评论
        comment = VideoComment(
            content=content,
            video_id=video_id,
            user_id=user_id,
            parent_id=parent_id,
            time_point=time_point,
            create_time=datetime.now(),
            likes=0,
            is_deleted=False
        )
        
        # 保存到数据库
        db.session.add(comment)
        db.session.commit()
        
        # 如果是顶级评论，更新视频评论数
        if not parent_id:
            video.comment_count += 1
            db.session.commit()
        
        # 获取用户信息
        user = Users.query.get(user_id)
        username = user.username if user else "未知用户"
        
        # 返回创建的评论
        return jsonify(Result.success({
            "id": comment.id,
            "content": comment.content,
            "videoId": comment.video_id,
            "userId": comment.user_id,
            "userName": username,
            "avatar": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{user.avatar}" or user.avatar,
            "timePoint": comment.time_point,
            "parentId": comment.parent_id,
            "createTime": comment.create_time.isoformat(),
            "likes": 0
        }, "评论成功"))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"添加评论错误: {str(e)}")
        return jsonify(Result.error(400, f"评论失败: {str(e)}"))

@video_bp.route('/comments/<comment_id>', methods=['DELETE'])
@token_required
def delete_comment(comment_id):
    """
    删除评论接口
    """
    try:
        # 获取当前用户ID
        user_id = request.user.get('user_id')
        if not user_id:
            return jsonify(Result.error(401, "未登录"))
        
        # 查询评论
        comment = VideoComment.query.get(comment_id)
        if not comment or comment.is_deleted:
            return jsonify(Result.error(404, "评论不存在"))
        
        # 检查权限（只能删除自己的评论）
        if str(comment.user_id) != str(user_id):
            return jsonify(Result.error(403, "您没有权限删除此评论"))
        
        # 标记评论为已删除
        comment.is_deleted = True
        
        # 如果是顶级评论，更新视频评论数
        if not comment.parent_id:
            video = Video.query.get(comment.video_id)
            if video and video.comment_count > 0:
                video.comment_count -= 1
        
        db.session.commit()
        
        return jsonify(Result.success(None, "删除评论成功"))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除评论错误: {str(e)}")
        return jsonify(Result.error(400, f"删除评论失败: {str(e)}"))

@video_bp.route('/comments/<comment_id>/like', methods=['POST'])
@token_required
def like_comment(comment_id):
    """
    点赞/取消点赞评论接口
    """
    try:
        # 获取当前用户ID
        user_id = request.user.get('user_id')
        if not user_id:
            return jsonify(Result.error(401, "未登录"))
        
        # 查询评论
        comment = VideoComment.query.get(comment_id)
        if not comment or comment.is_deleted:
            return jsonify(Result.error(404, "评论不存在"))
        
        # 查询是否已经点赞
        like_record = CommentLike.query.filter_by(
            comment_id=comment_id,
            user_id=user_id
        ).first()
        
        if like_record:
            # 如果已经点赞，则取消点赞
            db.session.delete(like_record)
            comment.likes = max(0, comment.likes - 1)  # 确保点赞数不会小于0
            liked = False
        else:
            # 如果未点赞，则添加点赞
            like_record = CommentLike(
                comment_id=comment_id,
                user_id=user_id
            )
            db.session.add(like_record)
            comment.likes += 1
            liked = True
        
        db.session.commit()
        
        return jsonify(Result.success({
            "id": comment.id,
            "likes": comment.likes,
            "liked": liked
        }, "操作成功"))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"点赞评论错误: {str(e)}")
        return jsonify(Result.error(400, f"操作失败: {str(e)}"))

@video_bp.route('/<uuid:video_id>', methods=['DELETE'])
@token_required
def delete_video(video_id):
    """
    删除视频接口（硬删除 + 级联删除）
    """
    try:
        # 获取当前用户ID
        user_id = request.user.get('user_id')
        
        # 查找视频
        video = Video.query.get(video_id)
        if not video:
            return jsonify(Result.error(404, "视频不存在"))
            
        # 检查权限（只有拥有者或管理员可以删除）
        video_course = video.course
        if str(video_course.teacher_id) != str(user_id) and not Users.query.get(user_id).role == 'admin':
            return jsonify(Result.error(403, "您没有权限删除此视频"))
        
        deletion_log = []
        video_title = video.title
        
        # 1. 删除comment_likes（通过video_comments关联）
        comment_likes_count = db.session.query(func.count(CommentLike.id)).join(
            VideoComment, VideoComment.id == CommentLike.comment_id
        ).filter(VideoComment.video_id == str(video_id)).scalar()
        
        if comment_likes_count > 0:
            # 删除评论点赞
            db.session.execute(
                db.text("""
                    DELETE cl FROM comment_likes cl 
                    INNER JOIN video_comments vc ON cl.comment_id = vc.id 
                    WHERE vc.video_id = :video_id
                """),
                {"video_id": str(video_id)}
            )
            deletion_log.append(f"删除了comment_likes表中{comment_likes_count}条记录")
        
        # 2. 删除video_comments（包括子评论）
        video_comments_count = VideoComment.query.filter_by(video_id=str(video_id)).count()
        if video_comments_count > 0:
            VideoComment.query.filter_by(video_id=str(video_id)).delete()
            deletion_log.append(f"删除了video_comments表中{video_comments_count}条记录")
        
        # 3. 删除user_video_progress
        progress_count = UserVideoProgress.query.filter_by(video_id=str(video_id)).count()
        if progress_count > 0:
            UserVideoProgress.query.filter_by(video_id=str(video_id)).delete()
            deletion_log.append(f"删除了user_video_progress表中{progress_count}条记录")
        
        # 4. 删除video_keywords
        video_keywords_count = VideoKeyword.query.filter_by(video_id=str(video_id)).count()
        if video_keywords_count > 0:
            VideoKeyword.query.filter_by(video_id=str(video_id)).delete()
            deletion_log.append(f"删除了video_keywords表中{video_keywords_count}条记录")
        
        # 5. 删除video_vector_indices
        vector_indices_count = VideoVectorIndex.query.filter_by(video_id=str(video_id)).count()
        if vector_indices_count > 0:
            # 删除向量索引文件
            vector_indices = VideoVectorIndex.query.filter_by(video_id=str(video_id)).all()
            for vector_index in vector_indices:
                try:
                    if vector_index.index_path and os.path.exists(vector_index.index_path):
                        import shutil
                        if os.path.isdir(vector_index.index_path):
                            shutil.rmtree(vector_index.index_path)
                        else:
                            os.remove(vector_index.index_path)
                        deletion_log.append(f"删除了向量索引文件: {vector_index.index_path}")
                except Exception as e:
                    current_app.logger.warning(f"删除向量索引文件失败: {e}")
            
            VideoVectorIndex.query.filter_by(video_id=str(video_id)).delete()
            deletion_log.append(f"删除了video_vector_indices表中{vector_indices_count}条记录")
        
        # 6. 删除video_keyframes（包括关键帧图片文件）
        keyframes_count = VideoKeyframe.query.filter_by(video_id=str(video_id)).count()
        if keyframes_count > 0:
            # 删除关键帧图片文件
            keyframes = VideoKeyframe.query.filter_by(video_id=str(video_id)).all()
            for keyframe in keyframes:
                try:
                    if keyframe.file_name:
                        # 构建关键帧文件路径
                        keyframe_dir = os.path.join(os.getcwd(), 'temp_keyframes', f'video_{video_id}')
                        keyframe_path = os.path.join(keyframe_dir, keyframe.file_name)
                        if os.path.exists(keyframe_path):
                            os.remove(keyframe_path)
                        
                        # 如果关键帧目录为空，删除目录
                        if os.path.exists(keyframe_dir) and not os.listdir(keyframe_dir):
                            os.rmdir(keyframe_dir)
                            deletion_log.append(f"删除了关键帧目录: {keyframe_dir}")
                except Exception as e:
                    current_app.logger.warning(f"删除关键帧文件失败: {e}")
            
            VideoKeyframe.query.filter_by(video_id=str(video_id)).delete()
            deletion_log.append(f"删除了video_keyframes表中{keyframes_count}条记录")
        
        # 7. 删除video_summaries
        summary_count = VideoSummary.query.filter_by(video_id=str(video_id)).count()
        if summary_count > 0:
            VideoSummary.query.filter_by(video_id=str(video_id)).delete()
            deletion_log.append(f"删除了video_summaries表中{summary_count}条记录")
        
        # 8. 删除video_processing_tasks
        processing_tasks_count = VideoProcessingTask.query.filter_by(video_id=str(video_id)).count()
        if processing_tasks_count > 0:
            VideoProcessingTask.query.filter_by(video_id=str(video_id)).delete()
            deletion_log.append(f"删除了video_processing_tasks表中{processing_tasks_count}条记录")
        
        # 9. 删除视频文件和封面图
        try:
            # 删除视频文件
            if video.video_url:
                video_path = os.path.join(os.getcwd(), video.video_url.lstrip('/'))
                if os.path.exists(video_path):
                    os.remove(video_path)
                    deletion_log.append(f"删除了视频文件: {video_path}")
                else:
                    deletion_log.append(f"视频文件不存在: {video_path}")
            
            # 删除封面图
            if video.cover_url:
                cover_path = os.path.join(os.getcwd(), video.cover_url.lstrip('/'))
                if os.path.exists(cover_path):
                    os.remove(cover_path)
                    deletion_log.append(f"删除了封面文件: {cover_path}")
                else:
                    deletion_log.append(f"封面文件不存在: {cover_path}")
        except Exception as e:
            current_app.logger.warning(f"删除视频文件失败: {e}")
            deletion_log.append(f"删除视频文件失败: {e}")
        
        # 10. 最后删除videos主表记录
        db.session.delete(video)
        deletion_log.append(f"删除了videos表中的主记录: {video_title}")
        
        # 提交事务
        db.session.commit()
        
        # 输出删除日志
        print(f"\n🎬 视频删除完成 - 视频ID: {video_id}")
        print(f"🎬 视频标题: {video_title}")
        print("🎬 级联删除详情:")
        for log in deletion_log:
            print(f"   ✓ {log}")
        print("🎬 删除操作完成\n")
        
        return jsonify(Result.success({
            'deletionLog': deletion_log,
            'videoTitle': video_title
        }, "视频删除成功"))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除视频错误: {str(e)}")
        return jsonify(Result.error(500, f"删除视频失败: {str(e)}"))

@video_bp.route('/unlink', methods=['POST'])
@token_required
def unlink_video_from_course():
    """
    解除视频与课程的关联
    如果视频不再与任何课程关联，则会删除该视频
    """
    try:
        # 检查权限 (使用JWT中的用户ID)
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
            
        # 获取请求数据
        data = request.get_json()
        video_id = data.get('videoId')
        course_id = data.get('courseId')
        
        if not video_id or not course_id:
            return jsonify(Result.error(400, "请提供视频ID和课程ID"))
        
        # 查找视频
        video = Video.query.get(video_id)
        if not video:
            return jsonify(Result.error(404, "视频不存在"))
            
        # 查找课程
        course = Course.query.get(course_id)
        if not course:
            return jsonify(Result.error(404, "课程不存在"))
            
        # 检查视频是否属于该课程
        if str(video.course_id) != str(course_id):
            return jsonify(Result.error(400, "该视频不属于指定课程"))
            
        # 检查用户是否为课程所有者或管理员
        if str(course.teacher_id) != str(user_id) and not Users.query.get(user_id).role == 'admin':
            return jsonify(Result.error(403, "无权修改他人创建的课程视频"))
        
        # 获取视频属于的其他课程数量
        other_courses_count = db.session.query(func.count(Video.id)).filter(
            Video.id == video_id,
            Video.course_id != course_id,
            Video.is_deleted == False
        ).scalar()
        
        # 如果视频不再与任何课程关联，则删除视频
        if other_courses_count == 0:            # 标记视频为已删除
            video.is_deleted = True
            #删除对应的VideoKeyframe和VideoVectorIndex
            db.session.query(VideoKeyframe).filter_by(video_id=video_id).delete()
            db.session.query(VideoVectorIndex).filter_by(video_id=video_id).delete()
            # 删除视频文件
            try:
                video_path = os.path.join(os.getcwd(), video.video_url.lstrip('/'))
                if os.path.exists(video_path):
                    os.remove(video_path)
                    
                # 删除视频封面图
                if video.cover_url:
                    cover_path = os.path.join(os.getcwd(), video.cover_url.lstrip('/'))
                    if os.path.exists(cover_path):
                        os.remove(cover_path)
            except Exception as e:
                # 即使删除文件失败，仍继续删除数据库记录
                current_app.logger.error(f"删除视频文件失败: {str(e)}")
            
            db.session.commit()
            return jsonify(Result.success(None, "视频已解除关联并删除"))
        else:            # 只解除关联，保留视频记录
            video.course_id = None
            db.session.commit()
            return jsonify(Result.success(None, "视频已解除关联"))
            
    except Exception as e:
        # 如果有错误，回滚事务
        db.session.rollback()
        return jsonify(Result.error(500, f"解除视频关联失败: {str(e)}"))

@video_bp.route('/update/<video_id>', methods=['PUT'])
@token_required
def update_video(video_id):
    """
    更新视频信息
    """
    try:
        # 检查权限
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
            
        # 查找视频
        video = Video.query.get(video_id)
        if not video:
            return jsonify(Result.error(404, "视频不存在"))
            
        # 如果视频属于课程，确认是否有权限
        if video.course_id:
            course = Course.query.get(video.course_id)
            if course and str(course.teacher_id) != str(user_id) and not Users.query.get(user_id).role == 'admin':
                return jsonify(Result.error(403, "无权修改他人创建的课程视频"))
        
        # 获取请求数据
        data = request.get_json()
        
        # 更新视频信息
        if 'title' in data:
            video.title = data['title']
        if 'description' in data:
            video.description = data['description']
        if 'coverUrl' in data:
            video.cover_url = data['coverUrl']
        
        db.session.commit()
        
        return jsonify(Result.success({
            "id": video.id,
            "title": video.title,
            "description": video.description,
            "coverUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{video.cover_url}" or video.cover_url,
            "duration": video.duration,
            "uploadTime": video.upload_time.isoformat() if video.upload_time else None,
            "viewCount": video.view_count,
            "commentCount": video.comment_count
        }, "视频信息更新成功"))
        
    except Exception as e:
        # 如果有错误，回滚事务
        db.session.rollback()
        return jsonify(Result.error(500, f"更新视频信息失败: {str(e)}"))

@video_bp.route('/<video_id>/process', methods=['POST'])
@token_required
def process_video(video_id):
    """
    手动触发视频处理任务的接口，支持简化的处理选项
    支持参数：
    - process_mode: 处理模式 ("full_reprocess" | "process_remaining")
    """
    try:
        # 检查权限
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
            
        # 查找视频
        video = Video.query.get(video_id)
        if not video:
            return jsonify(Result.error(404, "视频不存在"))
            
        # 检查视频是否已删除
        if video.is_deleted:
            return jsonify(Result.error(400, "视频已被删除"))
            
        # 如果视频属于课程，确认是否有权限
        if video.course_id:
            course = Course.query.get(video.course_id)
            if course and str(course.teacher_id) != str(user_id) and not Users.query.get(user_id).role == 'admin':
                return jsonify(Result.error(403, "无权处理他人创建的课程视频"))
        # 获取请求参数
        data = request.get_json() or {}
        process_mode = data.get('process_mode', 'full_reprocess')  # 默认为完全重新处理
        
        # 根据处理模式确定要执行的步骤
        processing_steps = None
        if process_mode == 'full_reprocess':
            # 清空记录并重新处理 - 执行所有步骤
            from tasks.video_processor import get_all_processing_steps
            processing_steps = get_all_processing_steps()
        elif process_mode == 'process_remaining':
            # 处理还未处理的步骤
            from tasks.video_processor import get_uncompleted_processing_steps
            processing_steps = get_uncompleted_processing_steps(video_id)
            if not processing_steps:
                return jsonify(Result.success({
                    "message": "所有处理步骤都已完成，无需重新处理"
                }, "视频处理已完成"))
        else:
            return jsonify(Result.error(400, f"无效的处理模式: {process_mode}，有效模式: full_reprocess, process_remaining"))
          # 检查视频本地文件可用性
        video = Video.query.get(video_id)
        if not video or not video.is_local_file_exists():
            return jsonify(Result.error(400, f"视频文件不存在，无法处理"))

        existing_task = VideoProcessingTask.query.filter_by(
            video_id=video_id, 
            status='processing'
        ).first()
        
        if existing_task:
            # Delete the existing processing task instead of returning an error
            db.session.delete(existing_task)

        # 导入处理函数并在后台线程中运行
        from tasks.video_processor.main_processor import process_video_task
        import threading
        from models.models import TaskLog
        from utils.video_processing_pool import video_processing_pool
        
        # 创建视频处理任务（非预览模式）
        task_id = f"task-{uuid.uuid4().hex[:8]}"

        # 只支持两种处理模式：full_reprocess或process_remaining
        task = VideoProcessingTask(
            video_id=video.id,
            task_id=task_id,
            status="pending",
            processing_type="full_reprocess",  # 默认为full_reprocess
            progress=0.0,
            start_time=datetime.now()
        )
        db.session.add(task)
        db.session.commit()
        
        # 提交任务到线程池处理，不阻塞HTTP响应
        task_id, stop_flag = video_processing_pool.submit_task_with_params(
            current_app._get_current_object(), 
            video.id, 
            process_video_task,
            processing_steps=processing_steps
        )
        
        # 更新任务ID（如果线程池生成了新的ID）
        if task.task_id != task_id:
            task.task_id = task_id
            db.session.commit()
        
        result_data = {
            "taskId": task_id,
            "pendingTasks": video_processing_pool.get_pending_tasks_count(),
            "activeTasks": video_processing_pool.get_active_tasks_count()
        }
        
        if processing_steps:
            result_data["processingSteps"] = processing_steps
        
        message = "视频处理任务已启动"
        return jsonify(Result.success(result_data, message))
        
    except Exception as e:
        current_app.logger.error(f"启动视频处理任务失败: {str(e)}")
        return jsonify(Result.error(500, f"启动视频处理任务失败: {str(e)}"))

@video_bp.route('/<video_id>/processing-status', methods=['GET'])
@token_required
def get_video_processing_status(video_id):
    """
    获取视频处理步骤状态的接口
    """
    try:
        # 检查权限
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
            
        # 查找视频
        video = Video.query.get(video_id)
        if not video:
            return jsonify(Result.error(404, "视频不存在"))
            
        # 检查视频是否已删除
        if video.is_deleted:
            return jsonify(Result.error(400, "视频已被删除"))
            
        # 如果视频属于课程，确认是否有权限
        if video.course_id:
            course = Course.query.get(video.course_id)
            if course and str(course.teacher_id) != str(user_id) and not Users.query.get(user_id).role == 'admin':
                return jsonify(Result.error(403, "无权查看他人创建的课程视频状态"))
        
        # 获取处理状态
        from tasks.video_processor.db_handler import check_video_processing_steps_status
        status = check_video_processing_steps_status(video_id)
        
        return jsonify(Result.success(status, "获取视频处理状态成功"))
        
    except Exception as e:
        current_app.logger.error(f"获取视频处理状态失败: {str(e)}")
        return jsonify(Result.error(500, f"获取视频处理状态失败: {str(e)}"))

@video_bp.route('/batch/processing-status', methods=['POST'])
@token_required
def get_videos_processing_status():
    """
    批量获取视频处理状态
    """
    try:
        data = request.get_json()
        if not data or 'video_ids' not in data:
            return jsonify(Result.error(400, "缺少video_ids参数"))
        
        video_ids = data['video_ids']
        if not isinstance(video_ids, list):
            return jsonify(Result.error(400, "video_ids必须是数组"))
        
        # 导入处理函数
        from tasks.video_processor import get_all_processing_steps, get_uncompleted_processing_steps
        
        results = []
        for video_id in video_ids:
            try:
                video_uuid = uuid.UUID(video_id) if isinstance(video_id, str) else video_id
                video = Video.query.filter_by(id=video_uuid, is_deleted=False).first()
                
                if not video:
                    results.append({
                        'video_id': str(video_id),
                        'error': '视频不存在'
                    })
                    continue
                
                # 获取所有处理步骤和未完成的步骤
                all_steps = get_all_processing_steps()
                uncompleted_steps = get_uncompleted_processing_steps(video_uuid)
                
                # 计算完成状态
                total_steps = len(all_steps)
                completed_steps = total_steps - len(uncompleted_steps)
                is_fully_completed = len(uncompleted_steps) == 0
                
                results.append({
                    'video_id': str(video_id),
                    'title': video.title,
                    'all_steps': all_steps,
                    'uncompleted_steps': uncompleted_steps,
                    'total_steps': total_steps,
                    'completed_steps': completed_steps,
                    'is_fully_completed': is_fully_completed,
                    'completion_percentage': (completed_steps / total_steps * 100) if total_steps > 0 else 100
                })
                
            except Exception as e:
                current_app.logger.error(f"获取视频 {video_id} 处理状态失败: {str(e)}")
                results.append({
                    'video_id': str(video_id),
                    'error': f'获取状态失败: {str(e)}'
                })
        
        return jsonify(Result.success({
            'videos': results
        }))
        
    except Exception as e:
        current_app.logger.error(f"批量获取视频处理状态失败: {str(e)}")
        return jsonify(Result.error(500, f"批量获取视频处理状态失败: {str(e)}"))
