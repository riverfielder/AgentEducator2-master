"""
文档处理任务日志记录器
负责记录文档处理过程中的日志信息
"""

import traceback
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from models.models import DocumentProcessingTask, TaskLog, db


class DocumentTaskLogger:
    """文档处理任务日志记录器"""

    def __init__(self, document_id: int, task_id: Optional[str] = None):
        """
        初始化日志记录器
        
        Args:
            document_id: 文档ID
            task_id: 任务ID（字符串类型，可选）
        """
        self.document_id = document_id
        self.task_id = task_id

    def log_info(self, step: str, message: str, details: Optional[str] = None):
        """记录信息日志"""
        self._add_log('INFO', step, message, details)

    def log_warning(self, step: str, message: str, details: Optional[str] = None):
        """记录警告日志"""
        self._add_log('WARNING', step, message, details)

    def log_error(self, step: str, message: str, details: Optional[str] = None):
        """记录错误日志"""
        self._add_log('ERROR', step, message, details)

    def log_success(self, step: str, message: str, details: Optional[str] = None):
        """记录成功日志"""
        self._add_log('SUCCESS', step, message, details)

    def log_exception(self, step: str, message: str, exception: Exception):
        """记录异常日志"""
        error_details = f"异常类型: {type(exception).__name__}\n"
        error_details += f"异常信息: {str(exception)}\n"
        error_details += f"堆栈跟踪:\n{traceback.format_exc()}"
        self._add_log('ERROR', step, message, error_details)

    def _add_log(self, log_level: str, step: str, message: str, details: Optional[str] = None):
        """
        添加日志到数据库
        
        Args:
            log_level: 日志级别
            step: 处理步骤
            message: 日志消息
            details: 详细信息
        """
        try:
            log_entry = TaskLog(
                task_id=self.task_id,
                document_id=self.document_id,
                log_level=log_level,
                message=f"[{step}] {message}",
                timestamp=datetime.now()
            )
            
            db.session.add(log_entry)
            db.session.commit()
            
            # 同时打印到控制台（安全处理Unicode字符）
            timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            try:
                console_msg = f"[{timestamp_str}] [{log_level}] 文档ID:{self.document_id} - {step}: {message}"
                if details:
                    console_msg += f"\n详细信息: {details}"
                print(console_msg, flush=True)
            except UnicodeEncodeError:
                # 如果包含无法编码的字符，使用安全的方式输出
                safe_message = message.encode('utf-8', 'ignore').decode('utf-8', 'ignore')
                safe_details = details.encode('utf-8', 'ignore').decode('utf-8', 'ignore') if details else None
                console_msg = f"[{timestamp_str}] [{log_level}] 文档ID:{self.document_id} - {step}: {safe_message}"
                if safe_details:
                    console_msg += f"\n详细信息: {safe_details}"
                print(console_msg, flush=True)
            
        except Exception as e:
            # 如果数据库记录失败，至少要打印到控制台
            try:
                error_msg = f"记录日志失败: {str(e)}"
                print(f"[ERROR] {error_msg}", flush=True)
                print(f"[ORIGINAL LOG] [{log_level}] 文档ID:{self.document_id} - {step}: {message}", flush=True)
                if details:
                    print(f"[ORIGINAL DETAILS] {details}", flush=True)
            except UnicodeEncodeError:
                # 最后的安全备份
                print(f"[ERROR] 记录日志失败，且包含无法编码的字符", flush=True)

    def update_task_status(self, status: str, error_message: Optional[str] = None):
        """
        更新文档处理任务状态
        
        Args:
            status: 任务状态
            error_message: 错误信息（可选）
        """
        if not self.task_id:
            return
        
        try:
            task = db.session.query(DocumentProcessingTask).filter_by(id=self.task_id).first()
            if task:
                task.status = status
                task.updated_at = datetime.now()
                if error_message:
                    task.error_message = error_message
                db.session.commit()
                
                self.log_info('task_status', f'任务状态更新为: {status}', error_message)
            else:
                self.log_warning('task_status', f'未找到任务ID: {self.task_id}')
                
        except Exception as e:
            self.log_exception('task_status', '更新任务状态失败', e)

    def start_step(self, step: str, description: str):
        """开始处理步骤"""
        self.log_info(step, f'开始{description}')

    def complete_step(self, step: str, description: str, result_data: Optional[dict] = None):
        """完成处理步骤"""
        details = None
        if result_data:
            details = f"处理结果: {str(result_data)}"
        self.log_success(step, f'完成{description}', details)

    def fail_step(self, step: str, description: str, error: str):
        """步骤失败"""
        self.log_error(step, f'{description}失败: {error}')


def create_document_task_logger(document_id: int, task_id: Optional[str] = None) -> DocumentTaskLogger:
    """
    创建文档处理任务日志记录器
    
    Args:
        document_id: 文档ID
        task_id: 任务ID（字符串类型，可选）
        
    Returns:
        DocumentTaskLogger: 日志记录器实例
    """
    return DocumentTaskLogger(document_id, task_id)


def add_task_log(task_id: str, video_id, level: str, message: str, document_id=None):
    """
    添加任务日志（兼容视频处理器接口）
    
    Args:
        task_id: 任务ID
        video_id: 视频ID（对于文档处理，这个参数会被忽略）
        level: 日志级别
        message: 日志消息
        document_id: 文档ID（关键字参数）
    """
    try:
        # 如果提供了document_id，使用文档ID；否则使用video_id作为通用ID
        actual_document_id = document_id if document_id is not None else video_id
        
        log_entry = TaskLog(
            task_id=task_id,
            video_id=video_id if video_id and not document_id else None,
            document_id=actual_document_id if document_id else None,
            log_level=level.upper(),
            message=message,
            timestamp=datetime.now()
        )
        
        db.session.add(log_entry)
        db.session.commit()
        
        # 同时打印到控制台（安全处理Unicode字符）
        timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            if document_id:
                console_msg = f"[{timestamp_str}] [{level.upper()}] 文档ID:{document_id} - {message}"
            else:
                console_msg = f"[{timestamp_str}] [{level.upper()}] 任务:{task_id} - {message}"
            print(console_msg, flush=True)
        except UnicodeEncodeError:
            # 如果包含无法编码的字符，使用安全的方式输出
            safe_message = message.encode('utf-8', 'ignore').decode('utf-8', 'ignore')
            if document_id:
                console_msg = f"[{timestamp_str}] [{level.upper()}] 文档ID:{document_id} - {safe_message}"
            else:
                console_msg = f"[{timestamp_str}] [{level.upper()}] 任务:{task_id} - {safe_message}"
            print(console_msg, flush=True)
        
    except Exception as e:
        # 如果数据库记录失败，至少要打印到控制台
        try:
            error_msg = f"记录日志失败: {str(e)}"
            print(f"[ERROR] {error_msg}", flush=True)
            print(f"[ORIGINAL LOG] [{level.upper()}] 任务:{task_id} - {message}", flush=True)
        except UnicodeEncodeError:
            # 最后的安全备份
            print(f"[ERROR] 记录日志失败，且包含无法编码的字符", flush=True) 