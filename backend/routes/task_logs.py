from flask import Blueprint, request, jsonify, current_app
from models.models import VideoProcessingTask, DocumentProcessingTask, TaskLog, Video, Document, db, Course
from utils.result import Result
from utils.auth import token_required
import traceback
import os
import signal
import psutil
import threading
from datetime import datetime

# 导入视频处理线程池
from utils.video_processing_pool import video_processing_pool

task_logs_bp = Blueprint('task_logs', __name__)

@task_logs_bp.route('/list', methods=['GET'])
@token_required
def list_tasks():
    """获取任务列表（支持视频和文档处理任务）"""
    try:
        # 获取当前用户ID
        current_user_id = request.user.get('user_id')
        
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
        status = request.args.get('status', None)
        task_type = request.args.get('task_type', 'all')  # all, video, document
        search = request.args.get('search', None)  # 搜索关键词
        
        tasks_list = []
        total = 0
        
        # 获取视频处理任务（过滤：只显示当前用户作为教师的课程中的视频任务）
        if task_type in ['all', 'video']:
            video_tasks_query = db.session.query(
                VideoProcessingTask.id,
                VideoProcessingTask.task_id,
                VideoProcessingTask.video_id,
                VideoProcessingTask.status,
                VideoProcessingTask.progress,
                VideoProcessingTask.start_time,
                VideoProcessingTask.end_time,
                VideoProcessingTask.error_message,
                VideoProcessingTask.processing_type,
                Video.title.label('resource_title'),
                Video.cover_url.label('resource_cover'),
                Course.teacher_id  # 添加教师ID用于过滤
            ).join(
                Video, VideoProcessingTask.video_id == Video.id
            ).join(
                Course, Video.course_id == Course.id
            ).filter(
                Course.teacher_id == current_user_id  # 只显示当前用户作为教师的课程
            )
            
            # 应用状态过滤
            if status:
                video_tasks_query = video_tasks_query.filter(VideoProcessingTask.status == status)
            
            # 应用搜索过滤
            if search:
                video_tasks_query = video_tasks_query.filter(Video.title.contains(search))
            
            video_tasks_with_info = video_tasks_query.order_by(VideoProcessingTask.start_time.desc())
            
            # 格式化视频任务结果
            for task in video_tasks_with_info.all():
                task_dict = {
                    'id': task.id,
                    'task_id': task.task_id,
                    'resource_id': task.video_id,
                    'resource_type': 'video',
                    'status': task.status,
                    'progress': task.progress or 0.0,
                    'start_time': task.start_time.isoformat() if task.start_time else None,
                    'end_time': task.end_time.isoformat() if task.end_time else None,
                    'error_message': task.error_message,
                    'processing_type': task.processing_type,
                    'resource_title': task.resource_title,
                    'resource_cover': task.resource_cover
                }
                tasks_list.append(task_dict)
        
        # 获取文档处理任务（过滤：只显示当前用户作为教师的课程中的文档任务）
        if task_type in ['all', 'document']:
            doc_tasks_query = db.session.query(
                DocumentProcessingTask.id,
                DocumentProcessingTask.task_id,
                DocumentProcessingTask.document_id,
                DocumentProcessingTask.status,
                DocumentProcessingTask.progress,
                DocumentProcessingTask.start_time,
                DocumentProcessingTask.end_time,
                DocumentProcessingTask.error_message,
                DocumentProcessingTask.processing_type,
                Document.title.label('resource_title'),
                Document.file_type,
                Course.teacher_id  # 添加教师ID用于过滤
            ).join(
                Document, DocumentProcessingTask.document_id == Document.id
            ).join(
                Course, Document.course_id == Course.id
            ).filter(
                Course.teacher_id == current_user_id  # 只显示当前用户作为教师的课程
            )
            
            # 应用状态过滤
            if status:
                doc_tasks_query = doc_tasks_query.filter(DocumentProcessingTask.status == status)
            
            # 应用搜索过滤
            if search:
                doc_tasks_query = doc_tasks_query.filter(Document.title.contains(search))
            
            doc_tasks_with_info = doc_tasks_query.order_by(DocumentProcessingTask.start_time.desc())
            
            # 格式化文档任务结果
            for task in doc_tasks_with_info.all():
                # 根据文件类型生成图标
                file_type_icon = _get_file_type_icon(task.file_type)
                
                task_dict = {
                    'id': task.id,
                    'task_id': task.task_id,
                    'resource_id': task.document_id,
                    'resource_type': 'document',
                    'status': task.status,
                    'progress': task.progress or 0.0,
                    'start_time': task.start_time.isoformat() if task.start_time else None,
                    'end_time': task.end_time.isoformat() if task.end_time else None,
                    'error_message': task.error_message,
                    'processing_type': task.processing_type,
                    'resource_title': task.resource_title,
                    'resource_cover': file_type_icon,  # 使用文件类型图标作为"封面"
                    'file_type': task.file_type
                }
                tasks_list.append(task_dict)
        
        # 按开始时间倒序排序所有任务
        tasks_list.sort(key=lambda x: x['start_time'] or '1970-01-01T00:00:00', reverse=True)
        
        # 手动分页
        total = len(tasks_list)
        start_index = (page - 1) * size
        end_index = start_index + size
        paginated_tasks = tasks_list[start_index:end_index]
        
        # 获取线程池状态信息
        pool_status = {
            'active_tasks': video_processing_pool.get_active_tasks_count(),
            'pending_tasks': video_processing_pool.get_pending_tasks_count(),
            'max_workers': video_processing_pool.max_workers
        }
        
        return jsonify(Result.success({
            'list': paginated_tasks,
            'total': total,
            'page': page,
            'size': size,
            'pool_status': pool_status
        }))
        
    except Exception as e:
        current_app.logger.error(f"获取任务列表失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(500, f"获取任务列表失败: {str(e)}"))

def _get_file_type_icon(file_type):
    """根据文件类型获取图标路径"""
    file_type_icons = {
        'pdf': '/static/icons/pdf-icon.png',
        'doc': '/static/icons/doc-icon.png',
        'docx': '/static/icons/doc-icon.png',
        'ppt': '/static/icons/ppt-icon.png',
        'pptx': '/static/icons/ppt-icon.png',
        'xls': '/static/icons/excel-icon.png',
        'xlsx': '/static/icons/excel-icon.png',
        'txt': '/static/icons/txt-icon.png',
        'md': '/static/icons/markdown-icon.png',
    }
    return file_type_icons.get(file_type.lower(), '/static/icons/document-icon.png')

@task_logs_bp.route('/logs/<task_id>', methods=['GET'])
@token_required
def get_task_logs(task_id):
    """获取任务日志"""
    try:
        # 获取当前用户ID
        current_user_id = request.user.get('user_id')
        
        # 查找任务，同时验证权限
        video_task = db.session.query(VideoProcessingTask).join(
            Video, VideoProcessingTask.video_id == Video.id
        ).join(
            Course, Video.course_id == Course.id
        ).filter(
            VideoProcessingTask.task_id == task_id,
            Course.teacher_id == current_user_id  # 确保是当前用户的课程
        ).first()
        
        doc_task = None
        if not video_task:
            doc_task = db.session.query(DocumentProcessingTask).join(
                Document, DocumentProcessingTask.document_id == Document.id
            ).join(
                Course, Document.course_id == Course.id
            ).filter(
                DocumentProcessingTask.task_id == task_id,
                Course.teacher_id == current_user_id  # 确保是当前用户的课程
            ).first()
        
        if not video_task and not doc_task:
            return jsonify(Result.error(404, "找不到指定的任务或无权限访问"))
        
        # 获取日志记录
        logs = TaskLog.query.filter_by(task_id=task_id).order_by(TaskLog.timestamp.asc()).all()
        
        logs_list = []
        for log in logs:
            logs_list.append({
                'id': log.id,
                'log_level': log.log_level,
                'message': log.message,
                'timestamp': log.timestamp.isoformat() if log.timestamp else None
            })
        
        # 获取任务信息
        if video_task:
            video = Video.query.get(video_task.video_id)
            task_info = {
                'id': video_task.id,
                'task_id': video_task.task_id,
                'resource_id': video_task.video_id,
                'resource_type': 'video',
                'status': video_task.status,
                'progress': video_task.progress or 0.0,
                'start_time': video_task.start_time.isoformat() if video_task.start_time else None,
                'end_time': video_task.end_time.isoformat() if video_task.end_time else None,
                'error_message': video_task.error_message,
                'processing_type': video_task.processing_type,
                'resource_title': video.title if video else "未知视频",
                'resource_cover': video.cover_url if video else None
            }
        else:  # doc_task
            document = Document.query.get(doc_task.document_id)
            task_info = {
                'id': doc_task.id,
                'task_id': doc_task.task_id,
                'resource_id': doc_task.document_id,
                'resource_type': 'document',
                'status': doc_task.status,
                'progress': doc_task.progress or 0.0,
                'start_time': doc_task.start_time.isoformat() if doc_task.start_time else None,
                'end_time': doc_task.end_time.isoformat() if doc_task.end_time else None,
                'error_message': doc_task.error_message,
                'processing_type': doc_task.processing_type,
                'resource_title': document.title if document else "未知文档",
                'resource_cover': _get_file_type_icon(document.file_type) if document else None,
                'file_type': document.file_type if document else None
            }
        
        return jsonify(Result.success({
            'task': task_info,
            'logs': logs_list
        }))
        
    except Exception as e:
        current_app.logger.error(f"获取任务日志失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(500, f"获取任务日志失败: {str(e)}"))

@task_logs_bp.route('/task/<task_id>', methods=['GET'])
@token_required
def get_task_info(task_id):
    """获取任务信息"""
    try:
        # 获取当前用户ID
        current_user_id = request.user.get('user_id')
        
        # 查找视频任务，同时验证权限
        video_task = db.session.query(VideoProcessingTask).join(
            Video, VideoProcessingTask.video_id == Video.id
        ).join(
            Course, Video.course_id == Course.id
        ).filter(
            VideoProcessingTask.task_id == task_id,
            Course.teacher_id == current_user_id  # 确保是当前用户的课程
        ).first()
        
        if video_task:
            video = Video.query.get(video_task.video_id)
            task_info = {
                'id': video_task.id,
                'task_id': video_task.task_id,
                'resource_id': video_task.video_id,
                'resource_type': 'video',
                'status': video_task.status,
                'progress': video_task.progress or 0.0,
                'start_time': video_task.start_time.isoformat() if video_task.start_time else None,
                'end_time': video_task.end_time.isoformat() if video_task.end_time else None,
                'error_message': video_task.error_message,
                'processing_type': video_task.processing_type,
                'resource_title': video.title if video else "未知视频",
                'resource_cover': video.cover_url if video else None
            }
            return jsonify(Result.success(task_info))
        
        # 查找文档任务，同时验证权限
        doc_task = db.session.query(DocumentProcessingTask).join(
            Document, DocumentProcessingTask.document_id == Document.id
        ).join(
            Course, Document.course_id == Course.id
        ).filter(
            DocumentProcessingTask.task_id == task_id,
            Course.teacher_id == current_user_id  # 确保是当前用户的课程
        ).first()
        
        if doc_task:
            document = Document.query.get(doc_task.document_id)
            task_info = {
                'id': doc_task.id,
                'task_id': doc_task.task_id,
                'resource_id': doc_task.document_id,
                'resource_type': 'document',
                'status': doc_task.status,
                'progress': doc_task.progress or 0.0,
                'start_time': doc_task.start_time.isoformat() if doc_task.start_time else None,
                'end_time': doc_task.end_time.isoformat() if doc_task.end_time else None,
                'error_message': doc_task.error_message,
                'processing_type': doc_task.processing_type,
                'resource_title': document.title if document else "未知文档",
                'resource_cover': _get_file_type_icon(document.file_type) if document else None,
                'file_type': document.file_type if document else None
            }
            return jsonify(Result.success(task_info))
        
        return jsonify(Result.error(404, "找不到指定的任务或无权限访问"))
        
    except Exception as e:
        current_app.logger.error(f"获取任务信息失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(500, f"获取任务信息失败: {str(e)}"))

@task_logs_bp.route('/task/<task_id>', methods=['DELETE'])
@token_required
def delete_task(task_id):
    """硬删除指定任务及其所有日志（支持视频和文档任务）"""
    try:
        # 获取当前用户ID
        current_user_id = request.user.get('user_id')
        
        # 查找视频处理任务，同时验证权限
        video_task = db.session.query(VideoProcessingTask).join(
            Video, VideoProcessingTask.video_id == Video.id
        ).join(
            Course, Video.course_id == Course.id
        ).filter(
            VideoProcessingTask.task_id == task_id,
            Course.teacher_id == current_user_id  # 确保是当前用户的课程
        ).first()
        
        # 查找文档处理任务，同时验证权限
        doc_task = None
        if not video_task:
            doc_task = db.session.query(DocumentProcessingTask).join(
                Document, DocumentProcessingTask.document_id == Document.id
            ).join(
                Course, Document.course_id == Course.id
            ).filter(
                DocumentProcessingTask.task_id == task_id,
                Course.teacher_id == current_user_id  # 确保是当前用户的课程
            ).first()
        
        if not video_task and not doc_task:
            return jsonify(Result.error(404, "找不到指定的任务或无权限访问"))
        
        deletion_log = []
        task_title = ""
        resource_type = ""
        
        # 处理视频任务的删除
        if video_task:
            task = video_task
            resource_type = "视频处理任务"
            
            # 获取任务标题用于日志
            video = Video.query.get(task.video_id)
            if video:
                task_title = f"{video.title} (任务ID: {task_id})"
            else:
                task_title = f"未知视频 (任务ID: {task_id})"
            
            # 如果任务正在处理中，尝试终止对应的线程
            if task.status in ['processing', 'running']:
                try:
                    # 尝试通过线程池停止任务
                    stopped = video_processing_pool.stop_task(task_id)
                    
                    if stopped:
                        current_app.logger.info(f"已通过线程池停止视频任务 {task_id}")
                        deletion_log.append("成功终止正在运行的视频处理线程")
                    else:
                        # 如果在线程池中找不到，检查应用的线程字典
                        if hasattr(current_app, 'PROCESSING_THREADS') and task_id in current_app.PROCESSING_THREADS:
                            thread_info = current_app.PROCESSING_THREADS[task_id]
                            
                            # 设置停止标志
                            if 'stop_flag' in thread_info:
                                thread_info['stop_flag'].set()
                                current_app.logger.info(f"已设置视频任务 {task_id} 的停止标志")
                                deletion_log.append("设置任务停止标志，通知处理线程停止")
                            
                            # 清理线程字典
                            del current_app.PROCESSING_THREADS[task_id]
                        else:
                            current_app.logger.warning(f"视频任务 {task_id} 状态为处理中，但在活动线程中未找到")
                            deletion_log.append("任务状态为处理中，但未找到对应的处理线程")
                except Exception as e:
                    current_app.logger.error(f"尝试终止视频任务线程时出错: {str(e)}")
                    deletion_log.append(f"终止处理线程时出错: {str(e)}")
            
            # 1. 删除task_logs表中的所有相关日志
            log_count = TaskLog.query.filter_by(task_id=task_id).count()
            if log_count > 0:
                TaskLog.query.filter_by(task_id=task_id).delete()
                deletion_log.append(f"删除了task_logs表中{log_count}条日志记录")
            
            # 2. 删除video_processing_tasks表中的主记录
            db.session.delete(task)
            deletion_log.append(f"删除了video_processing_tasks表中的主记录")
        
        # 处理文档任务的删除
        elif doc_task:
            task = doc_task
            resource_type = "文档处理任务"
            
            # 获取任务标题用于日志
            document = Document.query.get(task.document_id)
            if document:
                task_title = f"{document.title} (任务ID: {task_id})"
            else:
                task_title = f"未知文档 (任务ID: {task_id})"
            
            # 文档处理任务目前没有复杂的线程池管理，直接删除
            if task.status in ['pending', 'running']:
                deletion_log.append("终止了正在运行的文档处理任务")
            
            # 1. 删除task_logs表中的所有相关日志
            log_count = TaskLog.query.filter_by(task_id=task_id).count()
            if log_count > 0:
                TaskLog.query.filter_by(task_id=task_id).delete()
                deletion_log.append(f"删除了task_logs表中{log_count}条日志记录")
            
            # 2. 删除document_processing_tasks表中的主记录
            db.session.delete(task)
            deletion_log.append(f"删除了document_processing_tasks表中的主记录")
        
        # 提交事务
        db.session.commit()
        
        # 输出删除日志
        print(f"\n🗑️ {resource_type}删除完成")
        print(f"🗑️ 任务标题: {task_title}")
        print("🗑️ 硬删除详情:")
        for log in deletion_log:
            print(f"   ✓ {log}")
        print("🗑️ 删除操作完成\n")
        
        return jsonify(Result.success({
            'deletionLog': deletion_log,
            'taskTitle': task_title,
            'resourceType': resource_type
        }, f"{resource_type}已彻底删除"))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除任务失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(500, f"删除任务失败: {str(e)}"))

@task_logs_bp.route('/pool-status', methods=['GET'])
@token_required
def get_pool_status():
    """获取视频处理线程池的状态"""
    try:
        status = {
            'active_tasks': video_processing_pool.get_active_tasks_count(),
            'pending_tasks': video_processing_pool.get_pending_tasks_count(),
            'max_workers': video_processing_pool.max_workers,
            'is_full': video_processing_pool.get_active_tasks_count() >= video_processing_pool.max_workers
        }
        
        # 获取正在处理的任务信息
        active_tasks = []
        for task_id, task_info in video_processing_pool.current_tasks.items():
            # 查找任务记录
            task = VideoProcessingTask.query.filter_by(task_id=task_id).first()
            if task:
                # 获取视频信息
                video = Video.query.get(task.video_id)
                active_tasks.append({
                    'task_id': task_id,
                    'video_id': str(task.video_id),
                    'video_title': video.title if video else "未知视频",
                    'start_time': task_info['start_time'].isoformat(),
                    'duration': (datetime.now() - task_info['start_time']).total_seconds(),
                    'progress': task.progress
                })
        
        status['active_task_details'] = active_tasks
        
        return jsonify(Result.success(status))
    except Exception as e:
        current_app.logger.error(f"获取线程池状态失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(500, f"获取线程池状态失败: {str(e)}"))
