from flask import Blueprint, request, jsonify, current_app, session
from utils.result import Result
from utils.file_util import allowed_file, save_file, allowed_video_file, allowed_document_file
from datetime import datetime
from models.models import db, Document, Video, Users
import pandas as pd
import io
import re
from werkzeug.security import generate_password_hash
import os
import subprocess
import json
import uuid
import threading
from threading import Thread
import dotenv
dotenv.load_dotenv()
# 创建一个全局字典来存储线程信息和停止标志
PROCESSING_THREADS = {}

# 导入视频处理任务
from tasks.video_processor.main_processor import process_video_task
from models.models import VideoProcessingTask
from utils.auth import get_current_user_id as jwt_get_user_id
from utils.auth import token_required
from utils.video_processing_pool import video_processing_pool

upload_bp = Blueprint('uploads', __name__)

def get_current_user_id():
    """获取当前登录用户ID"""
    # 尝试从JWT中获取用户ID
    user_id = jwt_get_user_id()
    if user_id:
        return user_id
        
    # 如果JWT认证失败，尝试从session获取
    user_id = session.get('user_id')
    return user_id

def is_teacher_or_admin(user_id):
    """检查用户是否为教师或管理员"""
    if not user_id:
        return False
    
    user = Users.query.get(user_id)
    if not user:
        return False
        
    return user.role in ['teacher', 'admin']

@upload_bp.route('/image', methods=['POST'])
def upload_image():
    """
    上传图片接口，需要教师或管理员权限
    """
    try:
        # 检查权限
        user_id = get_current_user_id()
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
        
        # 检查是否有文件部分
        if 'file' not in request.files:
            return jsonify(Result.error(400, "未找到上传文件"))
        
        file = request.files['file']
        
        # 如果用户没有选择文件，浏览器可能会发送一个没有文件名的空文件部分
        if file.filename == '':
            return jsonify(Result.error(400, "未选择文件"))
        
        # 检查文件类型是否允许
        if not allowed_file(file.filename):
            return jsonify(Result.error(400, "不支持的文件格式，请上传图片文件"))
        
        # 保存文件并获取保存路径
        file_path = save_file(file, file_type='image')
        
        # 返回文件信息
        return jsonify(Result.success({
            "imageUrl": file_path
        }, "图片上传成功"))
        
    except Exception as e:
        current_app.logger.error(f"图片上传错误: {str(e)}")
        return jsonify(Result.error(500, f"服务器错误: {str(e)}"))

@upload_bp.route('/document', methods=['POST'])
def upload_document():
    """
    上传课件文档接口，需要教师或管理员权限
    支持智能文档处理功能
    """
    try:
        # 检查权限
        user_id = get_current_user_id()
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
        
        # 检查是否有文件部分
        if 'file' not in request.files:
            return jsonify(Result.error(400, "未找到上传文件"))
        
        # 获取课程ID
        course_id = request.form.get('courseId')
        if not course_id:
            return jsonify(Result.error(400, "未提供课程ID"))
        
        # 上传场景：自动全处理
        # 不再需要处理步骤参数，所有上传都自动全处理
        processing_steps = ['markitdown', 'segment', 'vector', 'summary']
        
        file = request.files['file']
        
        # 如果用户没有选择文件，浏览器可能会发送一个没有文件名的空文件部分
        if file.filename == '':
            return jsonify(Result.error(400, "未选择文件"))
        
        # 检查文件类型是否允许
        if not allowed_document_file(file.filename):
            return jsonify(Result.error(400, "不支持的文档格式"))
        
        # 保存文件并获取保存路径
        file_path = save_file(file, file_type='document')
        
        # 获取文件大小和类型
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # 重置文件指针
        file_type = file.filename.split('.')[-1].lower()
        
        # 创建文档记录并保存到数据库
        document = Document(
            title=file.filename,
            file_url=file_path,
            file_type=file_type,
            file_size=file_size,
            course_id=course_id,
            upload_time=datetime.now(),
            is_deleted=False
        )
        
        db.session.add(document)
        db.session.commit()
        
        # 自动启动文档处理任务（上传场景总是处理）
        processing_result = None
        current_app.logger.info(f"自动启动文档处理: 文档ID={document.id}, 步骤={processing_steps}")
        
        try:
            # 导入文档处理模块
            from tasks.document_processor.main_processor import process_document_async
            
            # 执行文档处理
            processing_result = process_document_async(
                document.id, 
                processing_steps
            )
            
            # 安全处理处理结果的日志输出，避免Unicode编码问题
            try:
                result_summary = f"代码={processing_result.get('code', 'N/A')}, 消息={processing_result.get('message', 'N/A')}"
                current_app.logger.info(f"文档处理完成: 文档ID={document.id}, 步骤={processing_steps}, 结果={result_summary}")
            except Exception as log_error:
                current_app.logger.info(f"文档处理完成: 文档ID={document.id}, 步骤={processing_steps}, 结果=<日志编码错误>")
            
        except Exception as process_error:
            current_app.logger.error(f"文档处理失败: {str(process_error)}")
            import traceback
            current_app.logger.error(f"错误详情: {traceback.format_exc()}")
            # 处理失败不影响文档上传成功，只记录错误
            processing_result = {"code": 500, "message": f"文档处理失败: {str(process_error)}", "data": None}
        
        # 构建返回结果
        response_data = {
            "documentId": document.id,
            "documentUrl": document.file_url,
            "documentName": document.title,
            "documentType": document.file_type,
            "size": document.file_size,
            "processing": {
                "enabled": True,  # 上传场景总是启用处理
                "steps": processing_steps,
                "result": processing_result['data'] if processing_result and processing_result.get('code') == 200 else None,
                "error": processing_result['message'] if processing_result and processing_result.get('code') != 200 else None
            }
        }
        
        # 返回文件信息和处理结果
        return jsonify(Result.success(response_data, "课件上传成功"))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"文档上传错误: {str(e)}")
        return jsonify(Result.error(500, f"服务器错误: {str(e)}"))

@upload_bp.route('/student_list', methods=['POST'])
def upload_student_list():
    """
    上传学生名单接口
    """
    try:
        # 检查是否有文件部分
        if 'file' not in request.files:
            return jsonify(Result.error(400, "未找到上传文件"))
        
        file = request.files['file']
        
        # 如果用户没有选择文件，浏览器可能会发送一个没有文件名的空文件部分
        if file.filename == '':
            return jsonify(Result.error(400, "未选择文件"))
        
        # 检查文件类型是否为Excel或CSV
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            return jsonify(Result.error(400, "请上传Excel或CSV格式的文件"))
        
        # 解析Excel/CSV文件
        invalid_records = []
        preview_data = []
        
        # 读取文件内容
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
            
        # 验证必要列是否存在
        required_columns = ['studentId', 'name', 'email']
        for col in required_columns:
            if col not in df.columns:
                return jsonify(Result.error(400, f"文件缺少必要列: {col}"))
        
        # 验证每行数据
        valid_students = []
        for index, row in df.iterrows():
            student = {
                'studentId': str(row['studentId']),
                'name': str(row['name']),
                'email': str(row['email'])
            }
            
            # 检查邮箱格式
            if not re.match(r"[^@]+@[^@]+\.[^@]+", student['email']):
                invalid_records.append({
                    "row": index + 2,  # +2因为Excel从1开始，且有表头
                    "reason": "邮箱格式错误"
                })
                continue
                
            # 检查学号是否已存在
            existing_user = Users.query.filter_by(
                username=student['studentId'], 
                is_deleted=False
            ).first()
            
            if existing_user:
                invalid_records.append({
                    "row": index + 2,
                    "reason": "学号已存在"
                })
                continue
                
            # 检查邮箱是否已存在
            existing_email = Users.query.filter_by(
                email=student['email'], 
                is_deleted=False
            ).first()
            
            if existing_email:
                invalid_records.append({
                    "row": index + 2,
                    "reason": "邮箱已被使用"
                })
                continue
            
            valid_students.append(student)
            
            # 添加到预览数据（最多显示5条）
            if len(preview_data) < 5:
                preview_data.append(student)
        
        # 返回解析结果
        return jsonify(Result.success({
            "totalCount": len(df),
            "validCount": len(valid_students),
            "invalidRecords": invalid_records,
            "previewData": preview_data,
            "validStudents": valid_students  # 传递有效学生列表供后续导入使用
        }, "学生名单解析成功"))
        
    except Exception as e:
        current_app.logger.error(f"学生名单上传错误: {str(e)}")
        return jsonify(Result.error(500, f"服务器错误: {str(e)}"))

@upload_bp.route('/course_video', methods=['POST'])
def upload_course_video():
    """
    上传教学视频资源接口
    """
    try:
        # 检查是否有文件部分
        if 'file' not in request.files:
            return jsonify(Result.error(400, "未找到上传文件"))
          # 获取附加参数
        course_id = request.form.get('courseId')
        title = request.form.get('title')
        description = request.form.get('description', '')
        
        # 上传场景：自动全处理
        # 不再需要处理步骤参数，所有上传都自动全处理
        processing_steps = ['keyframes', 'ocr', 'asr', 'vector', 'summary']
        
        json_sub = None
        
        if not all([course_id, title]):
            return jsonify(Result.error(400, "缺少必要参数"))
        
        file = request.files['file']
        if 'json_sub' in request.files:
            json_sub = request.files['json_sub']
        # 如果用户没有选择文件，浏览器可能会发送一个没有文件名的空文件部分
        if file.filename == '':
            return jsonify(Result.error(400, "未选择文件"))
        
        # 检查文件类型是否允许
        if not allowed_video_file(file.filename):
            return jsonify(Result.error(400, "不支持的视频格式"))
        
        # 保存文件并获取保存路径
        file_path = save_file(file, file_type='video')
        
        # 如果有字幕文件，保存同名json文件
        if json_sub:
            # 获取视频文件名（不含扩展名）
            video_filename = os.path.splitext(os.path.basename(file_path))[0]
            # 构造json文件路径
            json_dir = os.path.dirname(file_path)
            json_path = os.path.join(json_dir, f"{video_filename}.json")
            
            # 保存json文件
            actual_json_path = os.path.join(os.getcwd(), json_path.lstrip('/'))
            print(actual_json_path)
            json_sub.save(actual_json_path)
        
        # 实际路径计算
        actual_file_path = os.path.join(os.getcwd(), file_path.lstrip('/'))
        
        # 使用ffmpeg获取视频时长
        try:
            cmd = [
                'ffprobe', 
                '-v', 'error', 
                '-show_entries', 'format=duration', 
                '-of', 'json', 
                actual_file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            data = json.loads(result.stdout)
            duration = int(float(data['format']['duration']))
        except (subprocess.SubprocessError, json.JSONDecodeError, KeyError) as e:
            current_app.logger.error(f"获取视频时长失败: {str(e)}")
            # 如果ffmpeg命令失败，使用默认时长
            duration = 1800  # 默认30分钟
          # 生成视频封面图
        try:
            # 使用环境变量配置的图片文件夹
            from utils.file_util import get_upload_folder
            thumb_dir = get_upload_folder('image')
            if not os.path.exists(thumb_dir):
                os.makedirs(thumb_dir, exist_ok=True)
                
            thumbnail_filename = f"{uuid.uuid4().hex}_thumb.jpg"
            thumbnail_path = os.path.join(thumb_dir, thumbnail_filename)
            
            # 使用ffmpeg抓取视频第5秒的帧作为封面
            cmd = [
                'ffmpeg',
                '-i', actual_file_path,
                '-ss', '00:00:05',
                '-vframes', '1',
                '-vf', 'scale=320:-1',
                thumbnail_path
            ]
            subprocess.run(cmd, capture_output=True)            
            # 获取相对于基础路径的URL
            from config.config import Config
            folder_name = Config.get_upload_folder('image')
            cover_url = f"/{folder_name}/{thumbnail_filename}"
        except subprocess.SubprocessError as e:
            current_app.logger.error(f"生成视频封面失败: {str(e)}")
            # 如果生成封面失败，使用默认封面
            from config.config import Config
            folder_name = Config.get_upload_folder('image')
            cover_url = f"/{folder_name}/default_video_cover.jpg"
        
        # 创建视频记录并保存到数据库
        video = Video(
            title=title,
            description=description,
            cover_url=cover_url,            video_url=file_path,
            duration=duration,
            course_id=(course_id),
            view_count=0,
            comment_count=0,
            upload_time=datetime.now(),
            is_deleted=False
        )
        
        db.session.add(video)
        db.session.commit()
        
        # 自动触发视频处理任务
        task_id = None
        try:
            # 创建视频处理任务
            task_id = f"task-{uuid.uuid4().hex[:8]}"
            
            # 只支持全处理（full_reprocess）
            task = VideoProcessingTask(
                video_id=video.id,
                task_id=task_id,
                status="pending",
                processing_type="full_reprocess",
                progress=0.0,
                start_time=datetime.now()
            )
            db.session.add(task)
            db.session.commit()
            
            # 提交任务到线程池处理
            actual_task_id, stop_flag = video_processing_pool.submit_task_with_params(
                current_app._get_current_object(), 
                video.id, 
                process_video_task,
                processing_steps=processing_steps
            )
            
            # 更新任务ID（如果线程池生成了新的ID）
            if task.task_id != actual_task_id:
                task.task_id = actual_task_id
                task_id = actual_task_id
                db.session.commit()
                
            current_app.logger.info(f"视频 {video.id} 处理任务已启动，task_id: {task_id}")
            
        except Exception as e:
            current_app.logger.error(f"启动视频处理任务失败: {str(e)}")
            # 即使处理任务启动失败，也不影响视频上传的成功
            task_id = None
        
        # 返回视频信息
        return jsonify(Result.success({
            "videoId": video.id,
            "videoUrl": video.video_url,
            "title": video.title,
            "description": video.description,
            "duration": video.duration,
            "courseId": video.course_id,
            "processingStatus": "pending",
            "processingSteps": processing_steps,
            "uploadTime": video.upload_time.isoformat(),
            "coverUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{video.cover_url}" or video.cover_url,
            "taskId": task_id
        }, "教学视频上传成功"))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"视频上传错误: {str(e)}")
        return jsonify(Result.error(500, f"服务器错误: {str(e)}"))

@upload_bp.route('/avatar', methods=['POST'])
@token_required
def upload_avatar():
    """
    上传用户头像接口
    """
    try:
        # 获取当前用户ID
        user_id = request.user.get('user_id')
        if not user_id:
            return jsonify(Result.error(401, "未登录"))
        
        # 检查是否有文件部分
        if 'file' not in request.files:
            return jsonify(Result.error(400, "未找到上传文件"))
        
        file = request.files['file']
        
        # 如果用户没有选择文件，浏览器可能会发送一个没有文件名的空文件部分
        if file.filename == '':
            return jsonify(Result.error(400, "未选择文件"))
        
        # 检查文件类型是否允许
        if not allowed_file(file.filename):
            return jsonify(Result.error(400, "不支持的文件格式，请上传图片文件"))
        
        # 保存文件并获取保存路径
        file_path = save_file(file, file_type='avatar')
        
        # 更新用户的头像URL
        user = Users.query.get(user_id)
        if not user:
            return jsonify(Result.error(404, "用户不存在"))
            
        user.avatar = file_path
        db.session.commit()
        
        # 返回文件信息
        return jsonify(Result.success({
            "avatar": file_path
        }, "头像上传成功"))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"头像上传错误: {str(e)}")
        return jsonify(Result.error(500, f"服务器错误: {str(e)}"))