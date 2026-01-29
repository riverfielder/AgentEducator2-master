import os
from flask import Blueprint, request, jsonify, session, current_app
from models.models import Course, db, Users, Video, Document, CourseChapter, StudentCourseEnrollment, CourseKeyword, Assignment, ChatSession, ChatMessage, DailyStats, TaskLog, DocumentProcessingTask, DocumentKeyword, DocumentVectorIndex, DocumentSegment, DocumentSummary, Question, StudentAnswer
from schemas.course_dto import CourseCreateDTO, CourseEditDTO
from schemas.course_vo import CourseVO, CourseDetailVO, TeacherInfoVO
from utils.result import Result
from datetime import datetime
from sqlalchemy import func
from utils.auth import token_required, get_current_user_id as jwt_get_user_id
import json

course_bp = Blueprint('course', __name__)

def get_course_category(course):
    try:
        desc = json.loads(course.description) if course.description else {}
        return desc.get('category', [])
    except Exception:
        return []

def get_current_user_id():
    """获取当前登录用户ID"""
    return jwt_get_user_id()

def is_teacher_or_admin(user_id):
    """检查用户是否为教师或管理员"""
    if not user_id:
        return False
    
    user = Users.query.filter_by(id=user_id, is_deleted=False).first()
    if not user:
        return False
        
    return user.role in ['teacher', 'admin']

@course_bp.route('/add', methods=['POST'])
@token_required
def add_course():
    """
    添加课程接口，需要教师或管理员权限
    """
    try:
        # 检查权限 (使用JWT中的用户ID)
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
            
        # 获取请求 JSON 数据
        data = request.get_json()
        
        # 处理公开课程字段
        if 'isPublic' in data:
            data['is_public'] = data['isPublic']
        
        # 处理描述，description直接存储文本
        desc = data.get('description', '')
        data['description'] = desc
        # 保持category字段单独传递
        
        dto = CourseCreateDTO(**data)
        
        # 从时间戳转换为时间戳整数值 (不再需要转换为日期对象)
        from datetime import datetime
        
        # 前端传来的时间戳是毫秒级的，直接存储即可
        start_date = dto.startDate if dto.startDate else None
        end_date = dto.endDate if dto.endDate else None
        
        # 创建课程对象
        course = Course(
            name=dto.name,
            code=dto.code,
            description=dto.description,
            image_url=dto.imageUrl,
            start_date=start_date,  # 直接存储时间戳
            end_date=end_date,      # 直接存储时间戳
            hours=dto.hours,
            status=dto.status,     # 现在是整数
            is_public=dto.is_public,  # 添加是否为公开课
            semester=dto.semester,
            teacher_id=user_id,  # 设置当前用户为课程教师
            create_time=datetime.now(),
            update_time=datetime.now(),
        )
        
        # 保存到数据库
        db.session.add(course)
        db.session.commit()

        
        
        # 刷新获取最新数据
        db.session.refresh(course)
        
        # 手动构建VO对象，处理整数时间戳
        course_vo = {
            "id": course.id,
            "name": course.name,
            "code": course.code,
            "description": course.description or "",
            "imageUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{course.image_url}" or course.image_url or "",
            "startDate": course.start_date if course.start_date else 0,
            "endDate": course.end_date if course.end_date else 0,
            "hours": course.hours,
            "studentCount": course.student_count,
            "status": course.status,  # 已经是整数
            "isPublic": course.is_public,  # 添加是否为公开课
            "semester": course.semester,
            "createTime": course.create_time,
            "updateTime": course.update_time,
        }
        
        return jsonify(Result.success(course_vo, "课程添加成功"))
        
    except Exception as e:
        # 如果有错误，回滚事务
        db.session.rollback()
        return jsonify(Result.error(400, f"添加失败: {str(e)}"))

@course_bp.route('/edit/<course_id>', methods=['PUT'])
@token_required
def edit_course(course_id):
    """
    编辑课程接口，需要教师或管理员权限
    """
    try:
        # 检查权限 (使用JWT中的用户ID)
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
            
        # 查找课程
        course = Course.query.get(course_id)
        
        # 检查课程是否存在
        if not course:
            return jsonify(Result.error(404, "课程不存在"))
        
        # 检查课程是否已删除
        if course.is_deleted:
            return jsonify(Result.error(400, "课程已被删除"))
        
        # 检查是否为课程所有者或管理员
        admin_user = Users.query.filter_by(id=user_id, is_deleted=False).first()
        if str(course.teacher_id) != str(user_id) and not (admin_user and admin_user.role == 'admin'):
            print(f"课程教师ID: {course.teacher_id}, 当前用户ID: {user_id}, 类型: {type(course.teacher_id)}, {type(user_id)}")
            return jsonify(Result.error(403, "无权修改他人创建的课程"))
        
        # 获取请求 JSON 数据
        data = request.get_json()
        # 处理公开课程字段
        if 'isPublic' in data:
            data['is_public'] = data['isPublic']
        
        # 处理分类和描述，description直接存储文本
        desc = data.get('description', '')
        data['description'] = desc
        # 保持category字段单独传递
        
        # 输出接收到的数据用于调试
        print(f"接收到的数据: {data}")
        
        try:
            # 使用 DTO 验证和处理数据
            dto = CourseEditDTO(**data)
            
            # 更新课程信息
            course.name = dto.name
            course.description = dto.description
            course.image_url = dto.imageUrl
            
            # 直接使用时间戳，不再转换为日期对象
            course.start_date = dto.startDate if dto.startDate else None
            course.end_date = dto.endDate if dto.endDate else None
            
            course.hours = dto.hours
            course.status = dto.status  # 现在是整数类型
            course.is_public = dto.is_public  # 更新是否为公开课
            course.semester = dto.semester
            course.update_time = datetime.now()
            
            # 提交更改
            db.session.commit()
            
            # 刷新获取最新数据
            db.session.refresh(course)
            
        except Exception as validation_error:
            print(f"验证错误: {validation_error}")
            return jsonify(Result.error(400, f"数据验证失败: {str(validation_error)}"))
        
        # 手动构建VO对象，将日期对象转换为时间戳
        course_vo = {
            "id": course.id,
            "name": course.name,
            "code": course.code,
            "description": course.description or "",
            "imageUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{course.image_url}" or course.image_url or "",
            "startDate": course.start_date if course.start_date else 0,  # 已经是时间戳，直接使用
            "endDate": course.end_date if course.end_date else 0,  # 已经是时间戳，直接使用
            "hours": course.hours,
            "studentCount": course.student_count,
            "status": course.status,
            "isPublic": course.is_public,
            "semester": course.semester,
            "createTime": course.create_time,
            "updateTime": course.update_time,
        }
        
        return jsonify(Result.success(course_vo, "课程更新成功"))
        
    except Exception as e:
        # 如果有错误，回滚事务
        db.session.rollback()
        print(f"更新失败: {str(e)}")
        return jsonify(Result.error(400, f"更新失败: {str(e)}"))

@course_bp.route('/delete/<course_id>', methods=['DELETE'])
@token_required
def delete_course(course_id):
    """
    删除课程接口（硬删除 + 级联删除）
    复用视频和文档的删除接口，实现完整的级联删除
    """
    try:
        # 检查权限 (使用JWT中的用户ID)
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
            
        # 查找课程
        course = Course.query.get(course_id)
        
        # 检查课程是否存在
        if not course:
            return jsonify(Result.error(404, "课程不存在"))
        
        # 检查是否为课程所有者或管理员
        admin_user = Users.query.filter_by(id=user_id, is_deleted=False).first()
        if str(course.teacher_id) != str(user_id) and not (admin_user and admin_user.role == 'admin'):
            print(f"删除操作 - 课程教师ID: {course.teacher_id}, 当前用户ID: {user_id}, 类型: {type(course.teacher_id)}, {type(user_id)}")
            return jsonify(Result.error(403, "无权删除他人创建的课程"))
        
        deletion_log = []
        course_name = course.name
        
        print(f"\n🗑️ 开始删除课程 - 课程ID: {course_id}")
        print(f"🗑️ 课程名称: {course_name}")
        print("🗑️ 开始级联删除操作...\n")
        
        # 第一步：删除课程下的所有视频（复用视频删除逻辑）
        # 注意：这里要获取所有视频，包括已经标记为删除的，确保完全清理
        videos = Video.query.filter_by(course_id=course_id).all()
        deleted_videos_count = 0
        
        for video in videos:
            try:
                # 导入视频删除相关的模型和函数
                from models.models import (VideoComment, CommentLike, UserVideoProgress, 
                                         VideoKeyword, VideoVectorIndex, VideoSummary, 
                                         VideoSegment, VideoKeyframe, VideoProcessingTask)
                from sqlalchemy import func
                
                video_id = str(video.id)
                video_title = video.title
                
                # 删除comment_likes（通过video_comments关联）
                comment_likes_count = db.session.query(func.count(CommentLike.id)).join(
                    VideoComment, VideoComment.id == CommentLike.comment_id
                ).filter(VideoComment.video_id == video_id).scalar()
                
                if comment_likes_count > 0:
                    db.session.execute(
                        db.text("""
                            DELETE cl FROM comment_likes cl 
                            INNER JOIN video_comments vc ON cl.comment_id = vc.id 
                            WHERE vc.video_id = :video_id
                        """),
                        {"video_id": video_id}
                    )
                
                # 删除video_comments（包括子评论）
                video_comments_count = VideoComment.query.filter_by(video_id=video_id).count()
                if video_comments_count > 0:
                    VideoComment.query.filter_by(video_id=video_id).delete(synchronize_session=False)
                
                # 删除user_video_progress
                progress_count = UserVideoProgress.query.filter_by(video_id=video_id).count()
                if progress_count > 0:
                    UserVideoProgress.query.filter_by(video_id=video_id).delete(synchronize_session=False)
                
                # 删除video_keywords
                video_keywords_count = VideoKeyword.query.filter_by(video_id=video_id).count()
                if video_keywords_count > 0:
                    VideoKeyword.query.filter_by(video_id=video_id).delete(synchronize_session=False)
                
                # 删除video_vector_indices及文件
                video_vector_count = VideoVectorIndex.query.filter_by(video_id=video_id).count()
                if video_vector_count > 0:
                    vector_indices = VideoVectorIndex.query.filter_by(video_id=video_id).all()
                    for vector_index in vector_indices:
                        try:
                            if vector_index.index_path and os.path.exists(vector_index.index_path):
                                import shutil
                                if os.path.isdir(vector_index.index_path):
                                    shutil.rmtree(vector_index.index_path)
                                else:
                                    os.remove(vector_index.index_path)
                        except Exception as e:
                            current_app.logger.warning(f"删除视频向量索引文件失败: {e}")
                    VideoVectorIndex.query.filter_by(video_id=video_id).delete(synchronize_session=False)
                
                # 删除video_summaries
                video_summaries_count = VideoSummary.query.filter_by(video_id=video_id).count()
                if video_summaries_count > 0:
                    VideoSummary.query.filter_by(video_id=video_id).delete(synchronize_session=False)
                
                # 删除video_segments
                video_segments_count = VideoSegment.query.filter_by(video_id=video_id).count()
                if video_segments_count > 0:
                    VideoSegment.query.filter_by(video_id=video_id).delete(synchronize_session=False)
                
                # 删除video_keyframes及文件
                keyframes_count = VideoKeyframe.query.filter_by(video_id=video_id).count()
                if keyframes_count > 0:
                    keyframes = VideoKeyframe.query.filter_by(video_id=video_id).all()
                    for keyframe in keyframes:
                        try:
                            if keyframe.image_path and os.path.exists(keyframe.image_path):
                                os.remove(keyframe.image_path)
                        except Exception as e:
                            current_app.logger.warning(f"删除关键帧文件失败: {e}")
                    VideoKeyframe.query.filter_by(video_id=video_id).delete(synchronize_session=False)
                
                # 删除video_processing_tasks
                video_tasks_count = VideoProcessingTask.query.filter_by(video_id=video_id).count()
                if video_tasks_count > 0:
                    VideoProcessingTask.query.filter_by(video_id=video_id).delete(synchronize_session=False)
                
                # 删除视频文件
                try:
                    from utils.file_util import get_upload_base_path
                    base_path = get_upload_base_path()
                    
                    # 删除视频文件
                    if video.video_url:
                        video_file_path = video.video_url.lstrip('/')
                        if base_path == '.':
                            full_video_path = video_file_path
                        else:
                            full_video_path = os.path.join(base_path, video_file_path)
                        
                        if os.path.exists(full_video_path):
                            os.remove(full_video_path)
                    
                    # 删除封面文件
                    if video.cover_url:
                        cover_file_path = video.cover_url.lstrip('/')
                        if base_path == '.':
                            full_cover_path = cover_file_path
                        else:
                            full_cover_path = os.path.join(base_path, cover_file_path)
                        
                        if os.path.exists(full_cover_path):
                            os.remove(full_cover_path)
                            
                except Exception as e:
                    current_app.logger.warning(f"删除视频文件失败: {e}")
                
                # 删除videos主表记录
                db.session.delete(video)
                deleted_videos_count += 1
                
            except Exception as e:
                current_app.logger.error(f"删除视频 {video.title} 失败: {e}")
                continue
        
        if deleted_videos_count > 0:
            deletion_log.append(f"删除了{deleted_videos_count}个视频及其相关数据")
        
        # 第二步：删除课程下的所有文档（复用文档删除逻辑）
        # 注意：这里要获取所有文档，包括已经标记为删除的，确保完全清理
        documents = Document.query.filter_by(course_id=course_id).all()
        deleted_documents_count = 0
        
        for document in documents:
            try:
                document_id = str(document.id)
                document_title = document.title
                
                # 删除document_keywords
                doc_keywords_count = DocumentKeyword.query.filter_by(document_id=document_id).count()
                if doc_keywords_count > 0:
                    DocumentKeyword.query.filter_by(document_id=document_id).delete(synchronize_session=False)
                
                # 删除document_vector_indices及文件
                doc_vector_count = DocumentVectorIndex.query.filter_by(document_id=document_id).count()
                if doc_vector_count > 0:
                    vector_indices = DocumentVectorIndex.query.filter_by(document_id=document_id).all()
                    for vector_index in vector_indices:
                        try:
                            if vector_index.index_path and os.path.exists(vector_index.index_path):
                                import shutil
                                if os.path.isdir(vector_index.index_path):
                                    shutil.rmtree(vector_index.index_path)
                                else:
                                    os.remove(vector_index.index_path)
                        except Exception as e:
                            current_app.logger.warning(f"删除文档向量索引文件失败: {e}")
                    DocumentVectorIndex.query.filter_by(document_id=document_id).delete(synchronize_session=False)
                
                # 删除document_segments
                doc_segments_count = DocumentSegment.query.filter_by(document_id=document_id).count()
                if doc_segments_count > 0:
                    DocumentSegment.query.filter_by(document_id=document_id).delete(synchronize_session=False)
                
                # 删除document_summaries
                doc_summaries_count = DocumentSummary.query.filter_by(document_id=document_id).count()
                if doc_summaries_count > 0:
                    DocumentSummary.query.filter_by(document_id=document_id).delete(synchronize_session=False)
                
                # 删除document_processing_tasks及其相关task_logs
                doc_tasks_count = DocumentProcessingTask.query.filter_by(document_id=document_id).count()
                if doc_tasks_count > 0:
                    # 先获取所有相关的task_id
                    doc_tasks = DocumentProcessingTask.query.filter_by(document_id=document_id).all()
                    task_ids = [task.task_id for task in doc_tasks]
                    
                    # 删除task_logs表中的相关日志记录
                    for task_id in task_ids:
                        TaskLog.query.filter_by(task_id=task_id).delete(synchronize_session=False)
                    
                    # 删除document_processing_tasks表记录
                    DocumentProcessingTask.query.filter_by(document_id=document_id).delete(synchronize_session=False)
                
                # 删除文档文件
                try:
                    from utils.file_util import get_upload_base_path
                    base_path = get_upload_base_path()
                    file_path = document.file_url.lstrip('/')
                    
                    if base_path == '.':
                        full_path = file_path
                    else:
                        full_path = os.path.join(base_path, file_path)
                    
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        
                except Exception as e:
                    current_app.logger.warning(f"删除文档文件失败: {e}")
                
                # 删除documents主表记录
                db.session.delete(document)
                deleted_documents_count += 1
                
            except Exception as e:
                current_app.logger.error(f"删除文档 {document.title} 失败: {e}")
                continue
        
        if deleted_documents_count > 0:
            deletion_log.append(f"删除了{deleted_documents_count}个文档及其相关数据")
        
        # 第三步：删除课程章节（包括已标记删除的）
        chapters_count = CourseChapter.query.filter_by(course_id=course_id).count()
        if chapters_count > 0:
            CourseChapter.query.filter_by(course_id=course_id).delete(synchronize_session=False)
            deletion_log.append(f"删除了course_chapters表中{chapters_count}条记录")
        
        # 第四步：删除学生选课记录
        enrollments_count = StudentCourseEnrollment.query.filter_by(course_id=course_id).count()
        if enrollments_count > 0:
            StudentCourseEnrollment.query.filter_by(course_id=course_id).delete(synchronize_session=False)
            deletion_log.append(f"删除了student_course_enrollments表中{enrollments_count}条记录")
        
        # 第五步：删除课程关键词
        course_keywords_count = CourseKeyword.query.filter_by(course_id=course_id).count()
        if course_keywords_count > 0:
            CourseKeyword.query.filter_by(course_id=course_id).delete(synchronize_session=False)
            deletion_log.append(f"删除了course_keywords表中{course_keywords_count}条记录")
          # 第六步：删除作业（如果有Assignment模型）
        try:
            assignments = Assignment.query.filter_by(course_id=course_id).all()
            assignments_count = len(assignments)
            
            if assignments_count > 0:
                # 手动删除每个作业的相关数据
                for assignment in assignments:
                    assignment_id = str(assignment.id)
                      # 删除学生答题记录
                    try:
                        student_answers_count = StudentAnswer.query.filter_by(assignment_id=assignment_id).count()
                        if student_answers_count > 0:
                            StudentAnswer.query.filter_by(assignment_id=assignment_id).delete(synchronize_session=False)
                            print(f"删除了作业 {assignment.title} 的 {student_answers_count} 条学生答题记录")
                    except Exception as e:
                        print(f"删除学生答题记录时出错: {e}")
                      # 删除作业题目及其关联数据
                    try:
                        questions = Question.query.filter_by(assignment_id=assignment_id).all()
                        questions_count = len(questions)
                        if questions_count > 0:
                            # 删除题目关联的知识点
                            for question in questions:
                                try:
                                    from models.models import QuestionKeyword
                                    QuestionKeyword.query.filter_by(question_id=question.id).delete(synchronize_session=False)
                                except Exception as e:
                                    print(f"删除题目知识点关联时出错: {e}")
                            
                            # 删除题目记录
                            Question.query.filter_by(assignment_id=assignment_id).delete(synchronize_session=False)
                            print(f"删除了作业 {assignment.title} 的 {questions_count} 道题目及其关联数据")
                    except Exception as e:
                        print(f"删除作业题目时出错: {e}")
                
                # 最后删除作业主表记录
                Assignment.query.filter_by(course_id=course_id).delete(synchronize_session=False)
                deletion_log.append(f"删除了{assignments_count}个作业及其相关数据")
        except Exception as e:
            print(f"删除作业时出错: {e}")
            # 如果Assignment表不存在，忽略错误
            pass
        
        # 第七步：删除聊天会话
        try:
            chat_sessions = ChatSession.query.filter_by(course_id=course_id).all()
            chat_sessions_count = len(chat_sessions)
            
            if chat_sessions_count > 0:
                # 删除聊天消息
                for session in chat_sessions:
                    ChatMessage.query.filter_by(session_id=session.id).delete(synchronize_session=False)
                
                # 删除聊天会话
                ChatSession.query.filter_by(course_id=course_id).delete(synchronize_session=False)
                deletion_log.append(f"删除了{chat_sessions_count}个聊天会话及相关消息")
        except Exception as e:
            # 如果ChatSession表不存在，忽略错误
            pass
        
        # 第八步：删除统计数据
        try:
            daily_stats_count = DailyStats.query.filter_by(course_id=course_id).count()
            if daily_stats_count > 0:
                DailyStats.query.filter_by(course_id=course_id).delete(synchronize_session=False)
                deletion_log.append(f"删除了daily_stats表中{daily_stats_count}条记录")
        except Exception as e:
            # 如果DailyStats表不存在，忽略错误
            pass
        
        # 第九步：删除课程封面图片文件
        try:
            if course.image_url:
                from utils.file_util import get_upload_base_path
                base_path = get_upload_base_path()
                image_path = course.image_url.lstrip('/')
                
                if base_path == '.':
                    full_image_path = image_path
                else:
                    full_image_path = os.path.join(base_path, image_path)
                
                if os.path.exists(full_image_path):
                    os.remove(full_image_path)
                    deletion_log.append(f"删除了课程封面图片文件: {full_image_path}")
        except Exception as e:
            current_app.logger.warning(f"删除课程封面图片失败: {e}")
        
        # 刷新会话，确保所有之前的删除操作都已执行
        db.session.flush()
        
        # 最后：删除courses主表记录
        db.session.delete(course)
        deletion_log.append(f"删除了courses表中的主记录: {course_name}")
        
        # 提交事务
        db.session.commit()
        
        # 输出删除日志
        print(f"\n🗑️ 课程删除完成 - 课程ID: {course_id}")
        print(f"🗑️ 课程名称: {course_name}")
        print("🗑️ 级联删除详情:")
        for log in deletion_log:
            print(f"   ✓ {log}")
        print("🗑️ 删除操作完成\n")
        
        return jsonify(Result.success({
            'deletionLog': deletion_log,
            'courseName': course_name
        }, "课程删除成功"))
        
    except Exception as e:
        # 如果有错误，回滚事务
        db.session.rollback()
        print(f"删除课程错误: {e}")
        return jsonify(Result.error(500, f"删除失败: {str(e)}"))

@course_bp.route('/list', methods=['GET'])
@token_required
def list_courses():
    """
    获取课程列表接口
    - 教师/管理员：返回自己创建的课程
    - 学生：返回公开课程和已选课程
    """
    try:
        # 获取当前用户信息
        user_id = request.user.get('user_id')
        user = Users.query.filter_by(id=user_id, is_deleted=False).first()
        
        if not user:
            return jsonify(Result.error(401, "用户不存在"))
            
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)
        
        # 根据用户角色决定查询逻辑
        if user.role in ['teacher', 'admin']:
            # 教师和管理员：返回自己创建的未删除课程
            query = Course.query.filter_by(is_deleted=False, teacher_id=user_id)
        else:
            # 学生：返回公开课程和已选课程
            # 获取学生已选课程的ID列表
            enrolled_course_ids = db.session.query(StudentCourseEnrollment.course_id)\
                .filter_by(student_id=user_id).all()
            enrolled_ids = [enrollment.course_id for enrollment in enrolled_course_ids]
            
            # 查询公开课程或已选课程
            if enrolled_ids:
                query = Course.query.filter(
                    Course.is_deleted == False,
                    db.or_(
                        Course.is_public == True,  # 公开课程
                        Course.id.in_(enrolled_ids)  # 已选课程
                    )
                )
            else:
                # 如果没有已选课程，只查询公开课程
                query = Course.query.filter(
                    Course.is_deleted == False,
                    Course.is_public == True
                )
        
        # 计算总数
        total = query.count()
        
        # 分页查询
        courses = query.order_by(Course.create_time.desc()).offset((page - 1) * size).limit(size).all()
        
        # 手动构建VO列表
        course_list = []
        for course in courses:
            # 对于学生，检查是否已选课
            is_enrolled = False
            if user.role == 'student':
                enrollment = StudentCourseEnrollment.query.filter_by(
                    student_id=user_id, 
                    course_id=course.id, 
                ).first()
                is_enrolled = enrollment is not None
            
            course_data = {
                "id": course.id,
                "name": course.name,
                "code": course.code,
                "description": course.description or "",
                "imageUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{course.image_url}" or course.image_url or "",
                "startDate": course.start_date if course.start_date else 0,
                "endDate": course.end_date if course.end_date else 0,
                "hours": course.hours,
                "studentCount": course.student_count,
                "status": course.status,  # 已经是整数类型
                "isPublic": course.is_public,  # 添加是否为公开课
                "semester": course.semester,
                "createTime": course.create_time,
                "updateTime": course.update_time,
                "teacher_id": str(course.teacher_id) if course.teacher_id else None  # 新增字段
            }
            
            # 如果是学生，添加选课状态
            if user.role == 'student':
                course_data["isEnrolled"] = is_enrolled
            
            course_list.append(course_data)
        
        return jsonify(Result.success({
            "total": total,
            "list": course_list,
            "page": page,
            "size": size,
            "userRole": user.role  # 返回用户角色，便于前端处理
        }, "获取课程列表成功"))
        
    except Exception as e:
        return jsonify(Result.error(400, f"获取课程列表失败: {str(e)}"))

@course_bp.route('/all', methods=['GET'])
@token_required
def list_all_courses():
    """
    获取全平台课程列表接口，用于题库等功能的课程筛选
    """
    try:
        # 检查权限 (使用JWT中的用户ID)
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
            
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 1000, type=int)  # 默认返回较多数据
        
        # 返回所有未删除课程
        query = Course.query.filter_by(is_deleted=False)
        
        # 计算总数
        total = query.count()
        
        # 分页查询
        courses = query.order_by(Course.create_time.desc()).offset((page - 1) * size).limit(size).all()
        
        # 手动构建VO列表
        course_list = []
        for course in courses:
            # 获取教师信息
            teacher_name = "未知教师"
            if course.teacher:
                teacher_name = course.teacher.username
                
            course_list.append({
                "id": course.id,
                "name": course.name,
                "code": course.code,
                "description": course.description or "",
                "imageUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{course.image_url}" or course.image_url or "",
                "startDate": course.start_date if course.start_date else 0,
                "endDate": course.end_date if course.end_date else 0,
                "hours": course.hours,
                "studentCount": course.student_count,
                "status": course.status,  # 已经是整数类型
                "isPublic": course.is_public,  # 添加是否为公开课
                "semester": course.semester,
                "createTime": course.create_time,
                "updateTime": course.update_time,
                "teacher_id": str(course.teacher_id) if course.teacher_id else None,
                "teacher_name": teacher_name  # 添加教师名称
            })
        
        return jsonify(Result.success({
            "total": total,
            "list": course_list,
            "page": page,
            "size": size
        }, "获取全平台课程列表成功"))
        
    except Exception as e:
        return jsonify(Result.error(400, f"获取全平台课程列表失败: {str(e)}"))

@course_bp.route('/detail/<course_id>', methods=['GET'])
def get_course_detail(course_id):
    """
    获取课程详情接口
    """
    try:
        # 查找课程
        course = Course.query.get(course_id)
        
        # 检查课程是否存在
        if not course:
            return jsonify(Result.error(404, "课程不存在"))
        
        # 检查课程是否已删除
        if course.is_deleted:
            return jsonify(Result.error(400, "课程已被删除"))
        
        # 使用ORM关系获取教师信息
        teacher_info = {"id": 0, "name": "未分配"}
        if course.teacher:
            teacher_info = {"id": course.teacher.id, "name": course.teacher.username,"avatar":course.teacher.avatar}
        
        # 使用ORM关系获取视频数量
        video_count = Video.query.filter_by(course_id=course.id, is_deleted=False).count()
          # 使用ORM关系获取课件数量
        material_count = Document.query.filter_by(course_id=course.id, is_deleted=False).count()
        
        # 获取该课程下的所有未删除视频，按视频标题字典序排序
        videos = Video.query.filter_by(course_id=course.id, is_deleted=False).order_by(Video.title.asc()).all()
        
        # 构建视频列表
        video_list = []
        for video in videos:
            video_list.append({
                "id": video.id,
                "title": video.title,
                "description": video.description or "",
                "coverUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{video.cover_url}" or video.cover_url,
                "duration": video.duration,
                "uploadTime": video.upload_time.isoformat(),
                "viewCount": video.view_count,
                "commentCount": video.comment_count
            })
            
        # 获取该课程下的所有未删除文档，按文档标题字典序排序
        documents = Document.query.filter_by(course_id=course.id, is_deleted=False).order_by(Document.title.asc()).all()
        
        # 构建文档列表
        document_list = []
        for document in documents:
            document_list.append({
                "id": document.id,
                "title": document.title,
                "description": document.description or "",
                "fileUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{document.file_url}" or document.file_url,
                "uploadTime": document.upload_time.isoformat() if document.upload_time else None,
                "fileSize": document.file_size,
                "fileType": document.file_type
            })
        
        # 手动构建详细VO对象
        course_detail = {
            "id": course.id,
            "name": course.name,
            "code": course.code,
            "description": course.description or "",
            "imageUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{course.image_url}" or course.image_url or "",
            "startDate": course.start_date if course.start_date else 0,
            "endDate": course.end_date if course.end_date else 0,
            "hours": course.hours,
            "studentCount": course.student_count,
            "status": course.status,  # 已经是整数类型
            "isPublic": course.is_public,  # 添加是否为公开课
            "semester": course.semester,
            "createTime": course.create_time,
            "updateTime": course.update_time,
            "teacherInfo": teacher_info,
            "videoCount": video_count,
            "materialCount": material_count,
            "videos": video_list,  # 添加视频列表到返回数据中
            "documents": document_list  # 添加文档列表到返回数据中
        }
        
        return jsonify(Result.success(course_detail, "获取课程详情成功"))
        
    except Exception as e:
        return jsonify(Result.error(400, f"获取课程详情失败: {str(e)}"))

@course_bp.route('/detail-with-chapters/<course_id>', methods=['GET'])
def get_course_detail_with_chapters(course_id):
    """
    获取包含章节结构的课程详情接口
    """
    try:
        from models.models import CourseChapter, Document
        
        # 查找课程
        course = Course.query.get(course_id)
        
        # 检查课程是否存在
        if not course:
            return jsonify(Result.error(404, "课程不存在"))
        
        # 检查课程是否已删除
        if course.is_deleted:
            return jsonify(Result.error(400, "课程已被删除"))
        
        # 获取教师信息
        teacher_info = {"id": "0", "name": "未分配"}
        if course.teacher:
            teacher_info = {
                "id": str(course.teacher.id), 
                "name": course.teacher.username,
                "avatar": course.teacher.avatar
            }
        
        # 获取课程章节（按order_index排序）
        chapters = CourseChapter.query.filter_by(
            course_id=course.id, 
            is_deleted=False
        ).order_by(CourseChapter.order_index.asc()).all()
        
        # 获取课程下所有视频和文档
        videos = Video.query.filter_by(course_id=course.id, is_deleted=False).all()
        documents = Document.query.filter_by(course_id=course.id, is_deleted=False).all()
        
        # 构建章节列表，包含每章节的资源
        chapters_list = []
        unassigned_resources = {"documents": [], "videos": []}
        
        for chapter in chapters:
            # 获取该章节的文档
            chapter_documents = [doc for doc in documents if str(doc.chapter_id) == str(chapter.id)]
            # 获取该章节的视频  
            chapter_videos = [video for video in videos if str(video.chapter_id) == str(chapter.id)]
            
            # 构建文档列表
            docs_list = []
            for doc in chapter_documents:
                docs_list.append({
                    "id": str(doc.id),
                    "title": doc.title,
                    "description": doc.description or "",
                    "fileUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{doc.file_url}" or doc.file_url,
                    "fileType": doc.file_type,
                    "fileSize": doc.file_size,
                    "downloadCount": doc.download_count or 0,
                    "uploadTime": doc.upload_time.isoformat() if doc.upload_time else None,
                    "type": "document"
                })
            
            # 构建视频列表
            videos_list = []
            for video in chapter_videos:
                videos_list.append({
                    "id": str(video.id),
                    "title": video.title,
                    "description": video.description or "",
                    "coverUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{video.cover_url}" or video.cover_url,
                    "duration": video.duration,
                    "viewCount": video.view_count or 0,
                    "commentCount": video.comment_count or 0,
                    "uploadTime": video.upload_time.isoformat() if video.upload_time else None,
                    "type": "video"
                })
            
            chapters_list.append({
                "id": str(chapter.id),
                "title": chapter.title,
                "description": chapter.description or "",
                "chapterNumber": chapter.chapter_number,
                "orderIndex": chapter.order_index,
                "documents": docs_list,  # 文档在前
                "videos": videos_list,   # 视频在后
                "totalResources": len(docs_list) + len(videos_list)
            })
        
        # 处理未分配到章节的资源
        unassigned_docs = [doc for doc in documents if not doc.chapter_id]
        unassigned_videos = [video for video in videos if not video.chapter_id]
        
        for doc in unassigned_docs:
            unassigned_resources["documents"].append({
                "id": str(doc.id),
                "title": doc.title,
                "description": doc.description or "",
                "fileUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{doc.file_url}" or doc.file_url,
                "fileType": doc.file_type,
                "fileSize": doc.file_size,
                "downloadCount": doc.download_count or 0,
                "uploadTime": doc.upload_time.isoformat() if doc.upload_time else None,
                "type": "document"
            })
            
        for video in unassigned_videos:
            unassigned_resources["videos"].append({
                "id": str(video.id),
                "title": video.title,
                "description": video.description or "",
                "coverUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{video.cover_url}" or video.cover_url,
                "duration": video.duration,
                "viewCount": video.view_count or 0,
                "commentCount": video.comment_count or 0,
                "uploadTime": video.upload_time.isoformat() if video.upload_time else None,
                "type": "video"
            })
        
        # 统计信息
        total_videos = len(videos)
        total_documents = len(documents)
        
        # 构建课程详情
        course_detail = {
            "id": str(course.id),
            "name": course.name,
            "code": course.code,
            "description": course.description or "",
            "imageUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{course.image_url}" or course.image_url or "",
            "startDate": course.start_date if course.start_date else 0,
            "endDate": course.end_date if course.end_date else 0,
            "hours": course.hours,
            "studentCount": course.student_count,
            "status": course.status,
            "isPublic": course.is_public,
            "semester": course.semester,
            "createTime": course.create_time.isoformat() if course.create_time else None,
            "updateTime": course.update_time.isoformat() if course.update_time else None,
            "teacherInfo": teacher_info,
            "videoCount": total_videos,
            "documentCount": total_documents,
            "chapterCount": len(chapters),
            "chapters": chapters_list,
            "unassignedResources": unassigned_resources,
        }
        
        return jsonify(Result.success(course_detail, "获取课程详情成功"))
        
    except Exception as e:
        print(f"获取课程详情失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify(Result.error(400, f"获取课程详情失败: {str(e)}"))