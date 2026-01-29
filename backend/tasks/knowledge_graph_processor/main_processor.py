"""知识图谱处理器主处理器"""

from datetime import datetime
from flask import current_app
import threading
import queue
import concurrent.futures
from .data_access import KnowledgeGraphDataAccess
from .keyword_manager import KeywordManager
from .relation_manager import RelationManager
from .similarity_analyzer import SimilarityAnalyzer
from .llm_service import LLMService
from .config import KnowledgeGraphConfig

class BatchLLMProcessor:
    """批量LLM处理器 - 使用16个线程并行处理LLM调用"""
    
    def __init__(self, max_workers=16):
        """初始化批量LLM处理器"""
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
    
    def process_batches_parallel(self, batches, process_func, task_id=None, 
                                progress_start=0, progress_end=100):
        """并行处理批次"""
        if not batches:
            return []
        
        current_app.logger.info(f"使用 {self.max_workers} 个线程并行处理 {len(batches)} 个批次")
        
        # 提交所有批次任务
        future_to_batch = {
            self.executor.submit(process_func, batch): (i, batch) 
            for i, batch in enumerate(batches)
        }
        
        results = []
        completed = 0
        
        # 等待任务完成并收集结果
        for future in concurrent.futures.as_completed(future_to_batch):
            batch_idx, batch = future_to_batch[future]
            try:
                result = future.result()
                results.append((batch_idx, result))
                completed += 1
                
                # 更新进度
                if task_id:
                    progress = progress_start + int((completed / len(batches)) * (progress_end - progress_start))
                    # 这里需要通过某种方式更新进度，比如使用回调函数
                    current_app.logger.info(f"批次处理进度: {completed}/{len(batches)} ({progress}%)")
                
            except Exception as e:
                current_app.logger.error(f"批次 {batch_idx} 处理失败: {str(e)}")
                # 可以选择继续处理其他批次或者抛出异常
                raise e
        
        # 按原始顺序排序结果
        results.sort(key=lambda x: x[0])
        return [result for _, result in results]
    
    def shutdown(self):
        """关闭线程池"""
        self.executor.shutdown(wait=True)

class KnowledgeGraphMainProcessor:
    """知识图谱主处理器"""
    
    def __init__(self, api_key=None, base_url=None):
        """初始化主处理器"""
        # 初始化LLM服务
        self.llm_service = LLMService(api_key, base_url)
        
        # 初始化批量LLM处理器
        self.batch_processor = BatchLLMProcessor(max_workers=16)
        
        # 初始化各个组件，传入批量处理器
        self.data_access = KnowledgeGraphDataAccess()
        self.keyword_manager = KeywordManager(self.llm_service, self.batch_processor)
        self.relation_manager = RelationManager(self.llm_service, self.batch_processor)
        self.similarity_analyzer = SimilarityAnalyzer(self.llm_service)
        
        # 配置
        self.config = KnowledgeGraphConfig()
    
    def __del__(self):
        """析构函数，确保线程池正确关闭"""
        if hasattr(self, 'batch_processor'):
            self.batch_processor.shutdown()
    
    def check_content_processed_status(self, course_id):
        """检查内容处理状态"""
        return self.data_access.get_content_processed_status(course_id)
    
    def process_course_knowledge_graph(self, course_id, force_regenerate=False, enable_incremental=True):
        """处理课程知识图谱"""
        current_app.logger.info(f"开始处理课程 {course_id} 的知识图谱")
        
        try:
            if force_regenerate:
                current_app.logger.info("强制重新生成知识图谱")
                return self._process_course_knowledge_graph_full(course_id)
            elif enable_incremental:
                current_app.logger.info("使用增量处理模式")
                return self.process_course_knowledge_graph_incremental(course_id)
            else:
                current_app.logger.info("使用完整处理模式")
                return self._process_course_knowledge_graph_full(course_id)
                
        except Exception as e:
            current_app.logger.error(f"处理课程知识图谱时出错: {str(e)}")
            raise e
    
    def process_course_knowledge_graph_incremental(self, course_id):
        """增量处理课程知识图谱"""
        current_app.logger.info(f"开始增量处理课程 {course_id} 的知识图谱")
        
        # 检查是否有未处理的内容
        status = self.data_access.get_content_processed_status(course_id)
        unprocessed_videos = status['videos']['unprocessed']
        unprocessed_documents = status['documents']['unprocessed']
        
        if not unprocessed_videos and not unprocessed_documents:
            current_app.logger.info("没有未处理的内容，跳过增量处理")
            return {
                'success': True,
                'message': '没有未处理的内容',
                'task_id': None
            }
        
        current_app.logger.info(
            f"发现未处理内容: {len(unprocessed_videos)} 个视频, {len(unprocessed_documents)} 个文档"
        )
        
        # 创建任务记录
        task = self.data_access.create_processing_task(course_id, 'incremental')
        
        try:
            # 1. 增量提取和分类知识点 (0-30%)
            current_app.logger.info("步骤1: 增量提取和分类知识点")
            self.data_access.update_task_progress(task.id, 0, 'running')
            
            self.keyword_manager.extract_and_categorize_keywords_incremental(
                course_id, task.id
            )
            
            # 2. 增量建立知识点关系 (30-70%)
            current_app.logger.info("步骤2: 增量建立知识点关系")
            self.data_access.update_task_progress(task.id, 30)
            
            self.relation_manager.build_keyword_relations_incremental(
                course_id, task.id
            )
            
            # 3. 执行相似度聚类分析 (70-90%)
            current_app.logger.info("步骤3: 执行相似度聚类分析")
            self.data_access.update_task_progress(task.id, 70)
            
            cluster_relations = self.similarity_analyzer.perform_similarity_clustering(
                course_id, task.id
            )
            
            # 保存聚类关系到数据库
            if cluster_relations:
                saved_cluster_count = self.data_access.save_relations(cluster_relations)
                current_app.logger.info(f"聚类分析发现并保存了 {saved_cluster_count} 个关系")
            
            # 4. 处理孤立知识点 (90-100%)
            current_app.logger.info("步骤4: 处理孤立知识点")
            self.data_access.update_task_progress(task.id, 90)
            
            self.keyword_manager.handle_orphaned_keywords(course_id, task.id)
            
            # 5. 更新课程级别知识点统计
            current_app.logger.info("步骤5: 更新课程统计")
            self.data_access.update_course_keyword_stats(course_id)
            
            # 完成任务
            self.data_access.update_task_progress(task.id, 100, 'completed')
            
            current_app.logger.info(f"增量知识图谱处理完成，任务ID: {task.id}")
            
            return {
                'success': True,
                'message': '增量知识图谱处理完成',
                'task_id': task.id
            }
            
        except Exception as e:
            error_msg = f"增量处理失败: {str(e)}"
            current_app.logger.error(error_msg)
            self.data_access.update_task_progress(task.id, None, 'failed', error_msg)
            raise e
    
    def _process_course_knowledge_graph_full(self, course_id):
        """完整处理课程知识图谱"""
        current_app.logger.info(f"开始完整处理课程 {course_id} 的知识图谱")
        
        # 创建任务记录
        task = self.data_access.create_processing_task(course_id, 'full')
        
        try:
            # 1. 提取和分类知识点 (0-50%)
            current_app.logger.info("步骤1: 提取和分类知识点")
            self.data_access.update_task_progress(task.id, 0, 'running')
            
            self.keyword_manager.extract_and_categorize_keywords(course_id, task.id)
            
            # 2. 执行相似度聚类分析 (50-70%)
            current_app.logger.info("步骤2: 执行相似度聚类分析")
            self.data_access.update_task_progress(task.id, 50)
            
            cluster_relations = self.similarity_analyzer.perform_similarity_clustering(
                course_id, task.id
            )
            
            # 保存聚类关系到数据库
            if cluster_relations:
                saved_cluster_count = self.data_access.save_relations(cluster_relations)
                current_app.logger.info(f"聚类分析发现并保存了 {saved_cluster_count} 个关系")
            
            # 3. 建立知识点关系 (70-90%)
            current_app.logger.info("步骤3: 建立知识点关系")
            self.data_access.update_task_progress(task.id, 70)
            
            self.relation_manager.build_keyword_relations(course_id, task.id)
            
            # 4. 处理孤立知识点 (90-100%)
            current_app.logger.info("步骤4: 处理孤立知识点")
            self.data_access.update_task_progress(task.id, 90)
            
            self.keyword_manager.handle_orphaned_keywords(course_id, task.id)
            
            # 5. 更新课程级别知识点统计
            current_app.logger.info("步骤5: 更新课程统计")
            self.data_access.update_course_keyword_stats(course_id)
            
            # 完成任务
            self.data_access.update_task_progress(task.id, 100, 'completed')
            
            current_app.logger.info(f"完整知识图谱处理完成，任务ID: {task.id}")
            
            return {
                'success': True,
                'message': '知识图谱处理完成',
                'task_id': task.id
            }
            
        except Exception as e:
            error_msg = f"完整处理失败: {str(e)}"
            current_app.logger.error(error_msg)
            self.data_access.update_task_progress(task.id, None, 'failed', error_msg)
            raise e
    
    def check_videos_processed_status(self, course_id):
        """检查视频处理状态（兼容性方法）"""
        status = self.check_content_processed_status(course_id)
        
        # 转换为旧格式
        return {
            'processed_videos': status['videos']['processed'],
            'unprocessed_videos': status['videos']['unprocessed'],
            'total_videos': status['videos']['total']
        }

# 保持向后兼容的入口函数
def process_knowledge_graph_task(course_id, force_regenerate=False, enable_incremental=True):
    """处理知识图谱任务（入口函数）"""
    processor = KnowledgeGraphMainProcessor()
    return processor.process_course_knowledge_graph(
        course_id, force_regenerate, enable_incremental
    )

def trigger_knowledge_graph_generation(course_id):
    """触发知识图谱生成（入口函数）"""
    processor = KnowledgeGraphMainProcessor()
    return processor.process_course_knowledge_graph(course_id, force_regenerate=True)