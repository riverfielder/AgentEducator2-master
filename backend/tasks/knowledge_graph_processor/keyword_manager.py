"""知识图谱处理器关键词管理器"""

from collections import Counter, defaultdict
from flask import current_app
from .data_access import KnowledgeGraphDataAccess
from .llm_service import LLMService
from .config import KnowledgeGraphConfig

class KeywordManager:
    """关键词管理器"""
    
    def __init__(self, llm_service=None, batch_processor=None):
        """初始化关键词管理器"""
        self.llm_service = llm_service or LLMService()
        self.batch_processor = batch_processor
        self.data_access = KnowledgeGraphDataAccess()
        self.config = KnowledgeGraphConfig()
    
    def extract_and_categorize_keywords(self, course_id, task_id=None):
        """提取和分类关键词"""
        current_app.logger.info(f"开始提取和分类课程 {course_id} 的关键词")
        
        # 收集所有关键词
        all_keywords = self._collect_course_keywords(course_id)
        
        if not all_keywords:
            current_app.logger.warning(f"课程 {course_id} 没有找到关键词")
            return
        
        current_app.logger.info(f"收集到 {len(all_keywords)} 个关键词")
        
        # 分批分类关键词
        keyword_names = list(set([kw.name for kw in all_keywords]))  # 确保去重
        current_app.logger.info(f"去重后关键词数量: {len(keyword_names)}")
        batches = self.llm_service.create_batches(keyword_names, self.config.KEYWORD_BATCH_SIZE)
        
        all_classifications = []
        
        if self.batch_processor:
            # 使用批量处理器并行处理
            current_app.logger.info(f"使用16线程并行处理 {len(batches)} 个关键词分类批次")
            
            def classify_batch(batch):
                return self.llm_service.classify_keywords(batch)
            
            batch_results = self.batch_processor.process_batches_parallel(
                batches, classify_batch, task_id, 0, 50
            )
            
            # 合并所有结果
            for result in batch_results:
                if result:
                    all_classifications.extend(result)
        else:
            # 传统串行处理
            for i, batch in enumerate(batches):
                current_app.logger.info(f"正在分类第 {i+1}/{len(batches)} 批关键词")
                
                classifications = self.llm_service.classify_keywords(batch)
                all_classifications.extend(classifications)
                
                # 更新进度
                if task_id:
                    progress = int((i + 1) / len(batches) * 50)  # 分类占50%进度
                    self.data_access.update_task_progress(task_id, progress)
        
        # 验证分类完整性
        classified_keywords = {c['keyword'] for c in all_classifications}
        missing_keywords = set(keyword_names) - classified_keywords
        
        # 为缺失的关键词设置默认分类
        for keyword in missing_keywords:
            all_classifications.append({
                'keyword': keyword,
                'category': 'specific_point',
                'reason': '默认分类'
            })
        
        # 保存分类结果
        self.data_access.save_keywords(all_classifications)
        
        current_app.logger.info(f"完成关键词分类，共分类 {len(all_classifications)} 个关键词")
        return all_classifications
    
    def extract_and_categorize_keywords_incremental(self, course_id, task_id=None):
        """增量提取和分类关键词"""
        current_app.logger.info(f"开始增量提取和分类课程 {course_id} 的关键词")
        
        # 获取未处理的内容
        status = self.data_access.get_content_processed_status(course_id)
        unprocessed_videos = status['videos']['unprocessed']
        unprocessed_documents = status['documents']['unprocessed']
        
        if not unprocessed_videos and not unprocessed_documents:
            current_app.logger.info("没有未处理的内容")
            return []
        
        # 收集新关键词
        new_keywords = self._collect_new_keywords(unprocessed_videos, unprocessed_documents)
        
        if not new_keywords:
            current_app.logger.info("没有找到新关键词")
            return []
        
        current_app.logger.info(f"收集到 {len(new_keywords)} 个新关键词")
        
        # 分类新关键词
        keyword_names = list(set(new_keywords.keys()))  # 确保去重
        current_app.logger.info(f"去重后新关键词数量: {len(keyword_names)}")
        batches = self.llm_service.create_batches(keyword_names, self.config.KEYWORD_BATCH_SIZE)
        
        all_classifications = []
        
        if self.batch_processor:
            # 使用批量处理器并行处理
            current_app.logger.info(f"使用16线程并行处理 {len(batches)} 个新关键词分类批次")
            
            def classify_batch(batch):
                return self.llm_service.classify_keywords(batch)
            
            batch_results = self.batch_processor.process_batches_parallel(
                batches, classify_batch, task_id, 0, 30
            )
            
            # 合并所有结果
            for result in batch_results:
                if result:
                    all_classifications.extend(result)
        else:
            # 传统串行处理
            for i, batch in enumerate(batches):
                current_app.logger.info(f"正在分类第 {i+1}/{len(batches)} 批新关键词")
                
                classifications = self.llm_service.classify_keywords(batch)
                all_classifications.extend(classifications)
                
                # 更新进度
                if task_id:
                    progress = int((i + 1) / len(batches) * 30)  # 增量分类占30%进度
                    self.data_access.update_task_progress(task_id, progress)
        
        # 保存分类结果
        self.data_access.save_keywords(all_classifications)
        
        current_app.logger.info(f"完成增量关键词分类，共分类 {len(all_classifications)} 个关键词")
        return all_classifications
    
    def get_categorized_keywords(self, course_id):
        """获取分类后的关键词"""
        return self.data_access.get_course_keywords_by_category(course_id)
    
    def get_all_keywords(self, course_id):
        """获取所有关键词"""
        return self.data_access.get_all_course_keywords(course_id)
    
    def handle_orphaned_keywords(self, course_id, task_id=None):
        """处理孤立关键词"""
        current_app.logger.info(f"开始处理课程 {course_id} 的孤立关键词")
        
        # 获取孤立关键词
        orphaned_keywords = self.data_access.get_orphaned_keywords(course_id)
        
        if not orphaned_keywords:
            current_app.logger.info("没有找到孤立关键词")
            return 0
        
        current_app.logger.info(f"找到 {len(orphaned_keywords)} 个孤立关键词")
        
        # 获取已连接的关键词
        all_keywords = self.data_access.get_all_course_keywords(course_id)
        connected_keywords = [kw for kw in all_keywords if kw not in orphaned_keywords]
        
        if not connected_keywords:
            current_app.logger.warning("没有已连接的关键词可供连接")
            return 0
        
        # 分批处理孤立关键词
        orphaned_names = [kw.name for kw in orphaned_keywords]
        connected_names = [kw.name for kw in connected_keywords[:50]]  # 限制连接关键词数量
        
        batches = self.llm_service.create_batches(orphaned_names, 10)  # 小批次处理
        
        total_relations = 0
        for i, batch in enumerate(batches):
            current_app.logger.info(f"正在处理第 {i+1}/{len(batches)} 批孤立关键词")
            
            relations = self.llm_service.connect_orphaned_keywords(batch, connected_names)
            
            # 验证和保存关系
            valid_relations = self._validate_orphaned_relations(relations, orphaned_names, connected_names)
            saved_count = self.data_access.save_relations(valid_relations)
            total_relations += saved_count
            
            # 更新进度
            if task_id:
                progress = 90 + int((i + 1) / len(batches) * 10)  # 孤立关键词处理占最后10%
                self.data_access.update_task_progress(task_id, progress)
        
        current_app.logger.info(f"完成孤立关键词处理，建立了 {total_relations} 个关系")
        return total_relations
    
    def _collect_course_keywords(self, course_id):
        """收集课程关键词"""
        # 直接使用数据访问层的方法，它已经处理了去重
        return self.data_access.get_all_course_keywords(course_id)
    
    def _collect_new_keywords(self, unprocessed_videos, unprocessed_documents):
        """收集新关键词"""
        new_keywords = defaultdict(int)
        
        # 收集未处理视频的关键词
        for video_id in unprocessed_videos:
            keywords = self.data_access.get_video_keywords(video_id)
            for keyword in keywords:
                new_keywords[keyword.name] += 1
        
        # 收集未处理文档的关键词
        for document_id in unprocessed_documents:
            keywords = self.data_access.get_document_keywords(document_id)
            for keyword in keywords:
                new_keywords[keyword.name] += 1
        
        return dict(new_keywords)
    
    def _validate_orphaned_relations(self, relations, orphaned_names, connected_names):
        """验证孤立关键词关系"""
        valid_relations = []
        
        for relation in relations:
            # 检查源和目标是否有效
            source = relation.get('source')
            target = relation.get('target')
            
            if not source or not target:
                continue
            
            # 确保至少有一个是孤立关键词
            if source not in orphaned_names and target not in orphaned_names:
                continue
            
            # 确保另一个是已连接关键词
            if source in orphaned_names and target not in connected_names:
                continue
            if target in orphaned_names and source not in connected_names:
                continue
            
            valid_relations.append(relation)
        
        return valid_relations