"""
任务日志模块
负责记录视频处理任务的日志
"""

from flask import current_app
from models.models import db, TaskLog

def add_task_log(task_id, video_id, level, message):
    """
    添加任务日志
    
    参数:
        task_id: 任务ID
        video_id: 视频ID
        level: 日志级别（'debug', 'info', 'warning', 'error'等）
        message: 日志消息
        
    返回:
        无
    """
    try:
        log = TaskLog(
            task_id=task_id,
            video_id=video_id,
            log_level=level,
            message=message
        )
        db.session.add(log)
        db.session.commit()
        
        # 同时输出到应用日志
        if level == 'info':
            current_app.logger.info(f"[Task {task_id}] {message}")
        elif level == 'warning':
            current_app.logger.warning(f"[Task {task_id}] {message}")
        elif level == 'error':
            current_app.logger.error(f"[Task {task_id}] {message}")
        elif level == 'debug':
            current_app.logger.debug(f"[Task {task_id}] {message}")
    except Exception as e:
        current_app.logger.error(f"记录任务日志失败: {str(e)}")
