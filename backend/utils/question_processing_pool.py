import threading
import queue
from flask import current_app
from datetime import datetime
import uuid

class QuestionProcessingPool:
    def __init__(self, max_workers=2):
        self.max_workers = max_workers
        self.semaphore = threading.Semaphore(max_workers)
        self.task_queue = queue.Queue()
        self.current_tasks = {}
        self.running = True
        self.worker_threads = []
        for i in range(max_workers):
            thread = threading.Thread(target=self._worker_thread, daemon=True)
            thread.start()
            self.worker_threads.append(thread)

    def _worker_thread(self):
        while self.running:
            try:
                task = self.task_queue.get(timeout=1)
                if task is None:
                    break
                app, question_id, process_func = task
                task_id = f"question-task-{question_id}"
                self.current_tasks[task_id] = {
                    'question_id': question_id,
                    'start_time': datetime.now()
                }
                try:
                    with app.app_context():
                        thread_id = threading.get_ident()
                        current_app.logger.info(f"开始处理题目关键词，线程ID: {thread_id}, 题目ID: {question_id}")
                        process_func(app, question_id)
                except Exception as e:
                    current_app.logger.error(f"处理题目关键词任务失败: {str(e)}")
                finally:
                    if task_id in self.current_tasks:
                        del self.current_tasks[task_id]
                    self.task_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                current_app.logger.error(f"工作线程发生错误: {str(e)}")
                continue

    def submit_task(self, app, question_id, process_func):
        self.task_queue.put((app, question_id, process_func))

# 创建全局处理池实例
question_processing_pool = QuestionProcessingPool(max_workers=2) 