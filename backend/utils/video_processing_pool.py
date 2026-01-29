import threading
import queue
from flask import current_app
from datetime import datetime
import uuid

# 创建一个线程池来管理视频处理任务
class VideoProcessingPool:
    def __init__(self, max_workers=1):
        """
        初始化视频处理线程池
        
        Args:
            max_workers: 最大工作线程数，默认为2
        """
        self.max_workers = max_workers
        self.semaphore = threading.Semaphore(max_workers)
        self.task_queue = queue.Queue()
        self.current_tasks = {}
        self.running = True
        self.worker_threads = []
        
        # 启动工作线程
        for i in range(max_workers):
            thread = threading.Thread(target=self._worker_thread, daemon=True)
            thread.start()
            self.worker_threads.append(thread)
    def _worker_thread(self):
        """工作线程函数，不断从队列中获取任务并执行"""
        while self.running:
            try:
                # 尝试从队列获取任务，超时1秒
                task = self.task_queue.get(timeout=1)
                if task is None:  # 收到停止信号
                    break
                
                # 解析任务参数，支持新旧两种格式
                if len(task) == 5:
                    # 旧格式：兼容现有代码
                    app, video_id, task_id, stop_flag, process_func = task
                    processing_steps = None
                    preview_mode = False
                elif len(task) == 7:
                    # 新格式：支持新参数
                    app, video_id, task_id, stop_flag, process_func, processing_steps, preview_mode = task
                else:
                    current_app.logger.error(f"无效的任务参数格式: {task}")
                    continue
                
                # 添加到当前任务列表
                self.current_tasks[task_id] = {
                    'video_id': video_id,
                    'start_time': datetime.now(),
                    'stop_flag': stop_flag
                }
                
                try:
                    with app.app_context():
                        # 记录线程ID
                        thread_id = threading.get_ident()
                        
                        # 添加任务日志
                        from models.models import db, TaskLog
                        log = TaskLog(
                            task_id=task_id,
                            video_id=video_id,
                            log_level="info",
                            message=f"开始处理视频，线程ID: {thread_id}"
                        )
                        db.session.add(log)
                        db.session.commit()
                        
                        # 在全局字典中添加线程信息
                        if hasattr(app, 'PROCESSING_THREADS'):
                            app.PROCESSING_THREADS[task_id] = {
                                'thread_id': thread_id,
                                'video_id': video_id,
                                'stop_flag': stop_flag
                            }
                        
                        # 执行处理函数，传递新参数
                        process_func(video_id, stop_flag, processing_steps, preview_mode)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    with app.app_context():
                        current_app.logger.error(f"处理视频任务失败: {str(e)}")
                finally:
                    # 从当前任务列表移除
                    if task_id in self.current_tasks:
                        del self.current_tasks[task_id]
                    
                    # 从全局线程列表移除
                    if hasattr(app, 'PROCESSING_THREADS') and task_id in app.PROCESSING_THREADS:
                        del app.PROCESSING_THREADS[task_id]
                    
                    # 通知队列任务完成
                    self.task_queue.task_done()
                    
            except queue.Empty:
                # 队列为空，继续下一次循环
                continue
            except Exception as e:
                import traceback
                traceback.print_exc()
                with app.app_context():

                    current_app.logger.error(f"工作线程发生错误: {str(e)}")
                continue
    
    def submit_task(self, app, video_id, process_func):
        """
        提交视频处理任务
        
        Args:
            app: Flask应用实例
            video_id: 视频ID
            process_func: 处理函数
            
        Returns:
            task_id: 任务ID
        """
        # 生成任务ID
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        
        # 创建停止标志
        stop_flag = threading.Event()
        
        # 添加到队列
        self.task_queue.put((app, video_id, task_id, stop_flag, process_func))
        
        return task_id, stop_flag
    
    def submit_task_with_params(self, app, video_id, process_func, processing_steps=None, preview_mode=False):
        """
        提交视频处理任务（支持参数）
        
        Args:
            app: Flask应用实例
            video_id: 视频ID
            process_func: 处理函数
            processing_steps: 要执行的步骤列表
            preview_mode: 预览模式
            
        Returns:
            task_id: 任务ID
            stop_flag: 停止标志
        """
        # 生成任务ID
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        
        # 创建停止标志
        stop_flag = threading.Event()
        
        # 添加到队列，包含额外参数
        self.task_queue.put((app, video_id, task_id, stop_flag, process_func, processing_steps, preview_mode))
        
        return task_id, stop_flag

    def get_pending_tasks_count(self):
        """获取等待中的任务数量"""
        return self.task_queue.qsize()
    
    def get_active_tasks_count(self):
        """获取正在执行的任务数量"""
        return len(self.current_tasks)
    
    def stop_task(self, task_id):
        """停止指定任务"""
        if task_id in self.current_tasks:
            self.current_tasks[task_id]['stop_flag'].set()
            return True
        return False
    
    def shutdown(self, wait=True):
        """关闭线程池"""
        self.running = False
        
        # 清空队列并添加停止信号
        with self.task_queue.mutex:
            self.task_queue.queue.clear()
        
        # 对每个工作线程添加终止信号
        for _ in range(len(self.worker_threads)):
            self.task_queue.put(None)
        
        # 停止所有当前任务
        for task_id in list(self.current_tasks.keys()):
            self.stop_task(task_id)
        
        # 等待所有线程结束
        if wait:
            for thread in self.worker_threads:
                thread.join()

# 创建全局处理池实例
video_processing_pool = VideoProcessingPool(max_workers=1)
