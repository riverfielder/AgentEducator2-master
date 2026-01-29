"""知识图谱处理器关系管理器"""

from flask import current_app
from .data_access import KnowledgeGraphDataAccess
from .llm_service import LLMService
from .config import KnowledgeGraphConfig

class RelationManager:
    """关系管理器"""
    
    def __init__(self, llm_service=None, batch_processor=None):
        """初始化关系管理器"""
        self.llm_service = llm_service or LLMService()
        self.batch_processor = batch_processor
        self.data_access = KnowledgeGraphDataAccess()
        self.config = KnowledgeGraphConfig()
    
    def build_keyword_relations(self, course_id, task_id=None):
        """建立关键词关系"""
        current_app.logger.info(f"开始建立课程 {course_id} 的关键词关系")
        
        # 获取分类后的关键词
        categorized_keywords = self.data_access.get_course_keywords_by_category(course_id)
        course_info = self.data_access.get_course_info(course_id)
        
        # 分析关系
        all_relations = self._analyze_keyword_relations_with_llm(
            categorized_keywords, course_info, task_id
        )
        
        # 保存关系
        saved_count = self.data_access.save_relations(all_relations)
        
        current_app.logger.info(f"完成关系建立，保存了 {saved_count} 个关系")
        return saved_count
    
    def build_keyword_relations_incremental(self, course_id, task_id=None):
        """增量建立关键词关系"""
        current_app.logger.info(f"开始增量建立课程 {course_id} 的关键词关系")
        
        # 获取所有关键词（包括新旧）
        all_keywords = self.data_access.get_all_course_keywords(course_id)
        
        # 获取未处理内容的关键词作为新关键词
        status = self.data_access.get_content_processed_status(course_id)
        unprocessed_videos = status['videos']['unprocessed']
        unprocessed_documents = status['documents']['unprocessed']
        
        new_keyword_names = set()
        
        # 收集新关键词名称
        for video_id in unprocessed_videos:
            keywords = self.data_access.get_video_keywords(video_id)
            new_keyword_names.update(kw.name for kw in keywords)
        
        for document_id in unprocessed_documents:
            keywords = self.data_access.get_document_keywords(document_id)
            new_keyword_names.update(kw.name for kw in keywords)
        
        if not new_keyword_names:
            current_app.logger.info("没有新关键词需要建立关系")
            return 0
        
        # 分离新旧关键词并去重
        new_keywords = list(set([kw.name for kw in all_keywords if kw.name in new_keyword_names]))
        existing_keywords = list(set([kw.name for kw in all_keywords if kw.name not in new_keyword_names]))
        
        current_app.logger.info(f"去重后 - 新关键词: {len(new_keywords)}, 现有关键词: {len(existing_keywords)}")
        
        # 分析增量关系
        relations = self._analyze_keyword_relations_with_llm_incremental(
            new_keywords, existing_keywords, task_id
        )
        
        # 保存关系
        saved_count = self.data_access.save_relations(relations)
        
        current_app.logger.info(f"完成增量关系建立，保存了 {saved_count} 个关系")
        return saved_count
    
    def _analyze_keyword_relations_with_llm(self, categorized_keywords, course_info, task_id=None):
        """使用LLM分析关键词关系"""
        all_relations = []
        
        # 提取关键词名称并去重，避免重复调用LLM
        core_concepts = list(set([kw.name for kw in categorized_keywords['core_concept']]))
        main_modules = list(set([kw.name for kw in categorized_keywords['main_module']]))
        specific_points = list(set([kw.name for kw in categorized_keywords['specific_point']]))
        
        current_app.logger.info(f"去重后关键词统计 - 核心概念: {len(core_concepts)}, 主要模块: {len(main_modules)}, 具体知识点: {len(specific_points)}")
        
        total_steps = 0
        # 跨级别关系步骤（基于去重后的关键词计算）
        if core_concepts and main_modules:
            total_steps += len(self.llm_service.create_batches(
                [(c, m) for c in core_concepts for m in main_modules], 
                self.config.RELATION_BATCH_SIZE
            ))
        if core_concepts and specific_points:
            total_steps += len(self.llm_service.create_batches(
                [(c, s) for c in core_concepts for s in specific_points],
                self.config.RELATION_BATCH_SIZE
            ))
        if main_modules and specific_points:
            total_steps += len(self.llm_service.create_batches(
                [(m, s) for m in main_modules for s in specific_points],
                self.config.RELATION_BATCH_SIZE
            ))
        
        # 同级别关系步骤
        if len(core_concepts) > 1:
            total_steps += len(self.llm_service.create_batches(
                core_concepts, self.config.RELATION_BATCH_SIZE
            ))
        if len(main_modules) > 1:
            total_steps += len(self.llm_service.create_batches(
                main_modules, self.config.RELATION_BATCH_SIZE
            ))
        if len(specific_points) > 1:
            # 使用滑动窗口
            total_steps += max(1, len(specific_points) // 20)
        
        current_step = 0
        
        # 分析跨级别关系（传递去重后的关键词）
        cross_level_relations = self._analyze_cross_level_relations(
            {'core_concept': core_concepts, 'main_module': main_modules, 'specific_point': specific_points}, 
            course_info, task_id, current_step, total_steps
        )
        all_relations.extend(cross_level_relations)
        current_step += len(cross_level_relations)
        
        # 分析同级别关系（传递去重后的关键词）
        same_level_relations = self._analyze_same_level_relations(
            {'core_concept': core_concepts, 'main_module': main_modules, 'specific_point': specific_points}, 
            course_info, task_id, current_step, total_steps
        )
        all_relations.extend(same_level_relations)
        
        return all_relations
    
    def _analyze_keyword_relations_with_llm_incremental(self, new_keywords, existing_keywords, task_id=None):
        """增量分析关键词关系"""
        all_relations = []
        
        # 分批处理
        new_batches = self.llm_service.create_batches(new_keywords, self.config.RELATION_BATCH_SIZE)
        existing_sample = existing_keywords[:100]  # 限制现有关键词数量
        
        if self.batch_processor:
            # 使用批量处理器并行处理
            current_app.logger.info(f"使用16线程并行处理 {len(new_batches)} 个增量关系批次")
            
            def analyze_incremental_batch(batch):
                return self.llm_service.analyze_incremental_relations(
                    batch, existing_sample
                )
            
            batch_results = self.batch_processor.process_batches_parallel(
                new_batches, analyze_incremental_batch, task_id, 30, 70
            )
            
            # 合并和验证所有结果
            for result in batch_results:
                if result:
                    valid_relations = self._validate_and_deduplicate_relations(result)
                    all_relations.extend(valid_relations)
        else:
            # 传统串行处理
            for i, new_batch in enumerate(new_batches):
                current_app.logger.info(f"正在分析第 {i+1}/{len(new_batches)} 批增量关系")
                
                relations = self.llm_service.analyze_incremental_relations(
                    new_batch, existing_sample
                )
                
                # 验证和去重
                valid_relations = self._validate_and_deduplicate_relations(relations)
                all_relations.extend(valid_relations)
                
                # 更新进度
                if task_id:
                    progress = 30 + int((i + 1) / len(new_batches) * 40)  # 增量关系占30-70%
                    self.data_access.update_task_progress(task_id, progress)
        
        return all_relations
    
    def _analyze_cross_level_relations(self, clean_categorized_keywords, course_info, task_id, current_step, total_steps):
        """分析跨级别关系（接收已去重的关键词列表）"""
        relations = []
        
        # 直接使用已去重的关键词列表
        core_concepts = clean_categorized_keywords['core_concept']
        main_modules = clean_categorized_keywords['main_module']  
        specific_points = clean_categorized_keywords['specific_point']
        
        # 核心概念 vs 主要模块
        if core_concepts and main_modules:
            relations.extend(self._analyze_cross_level_batch(
                core_concepts, main_modules, "核心概念", "主要模块",
                task_id, current_step, total_steps
            ))
        
        # 核心概念 vs 具体知识点
        if core_concepts and specific_points:
            relations.extend(self._analyze_cross_level_batch(
                core_concepts, specific_points, "核心概念", "具体知识点",
                task_id, current_step, total_steps
            ))
        
        # 主要模块 vs 具体知识点
        if main_modules and specific_points:
            relations.extend(self._analyze_cross_level_batch(
                main_modules, specific_points, "主要模块", "具体知识点",
                task_id, current_step, total_steps
            ))
        
        return relations
    
    def _analyze_cross_level_batch(self, level1_keywords, level2_keywords, level1_name, level2_name, task_id, current_step, total_steps):
        """分批分析跨级别关系（接收已去重的关键词列表）"""
        relations = []
        
        # 关键词列表已经在上层去重，这里不需要再次去重
        current_app.logger.info(f"分析{level1_name}-{level2_name}关系: {len(level1_keywords)} x {len(level2_keywords)} = {len(level1_keywords) * len(level2_keywords)}个关键词对")
        
        # 创建关键词对
        keyword_pairs = [(l1, l2) for l1 in level1_keywords for l2 in level2_keywords]
        batches = self.llm_service.create_batches(keyword_pairs, self.config.RELATION_BATCH_SIZE)
        
        if self.batch_processor:
            # 使用批量处理器并行处理
            current_app.logger.info(f"使用16线程并行处理 {len(batches)} 个{level1_name}-{level2_name}关系批次")
            
            def analyze_relation_batch(batch):
                # 分离关键词对为两个列表并去重
                l1_list = list(set([pair[0] for pair in batch]))
                l2_list = list(set([pair[1] for pair in batch]))
                return self.llm_service.analyze_cross_level_relations(
                    l1_list, l2_list, level1_name, level2_name
                )
            
            batch_results = self.batch_processor.process_batches_parallel(
                batches, analyze_relation_batch, task_id, 
                current_step, current_step + len(batches)
            )
            
            # 合并所有结果
            for result in batch_results:
                if result:
                    relations.extend(result)
        else:
            # 传统串行处理
            for i, batch in enumerate(batches):
                current_app.logger.info(f"正在分析第 {i+1}/{len(batches)} 批{level1_name}-{level2_name}关系")
                
                # 分离关键词对为两个列表并去重
                l1_list = list(set([pair[0] for pair in batch]))
                l2_list = list(set([pair[1] for pair in batch]))
                
                batch_relations = self.llm_service.analyze_cross_level_relations(
                    l1_list, l2_list, level1_name, level2_name
                )
                
                if batch_relations:
                    relations.extend(batch_relations)
                
                # 更新进度
                if task_id and total_steps > 0:
                    progress = int((current_step + i + 1) / total_steps * 40) + 30  # 关系分析占30-70%
                    self.data_access.update_task_progress(task_id, progress)
        
        return relations
    
    def _analyze_same_level_relations(self, clean_categorized_keywords, course_info, task_id, current_step, total_steps):
        """分析同级别关系（接收已去重的关键词列表）"""
        relations = []
        
        # 直接使用已去重的关键词列表
        core_concepts = clean_categorized_keywords['core_concept']
        main_modules = clean_categorized_keywords['main_module']
        specific_points = clean_categorized_keywords['specific_point']
        
        # 分析核心概念内部关系
        if len(core_concepts) > 1:
            relations.extend(self._analyze_same_level_batch(
                core_concepts, "核心概念", task_id, current_step, total_steps
            ))
        
        # 分析主要模块内部关系
        if len(main_modules) > 1:
            relations.extend(self._analyze_same_level_batch(
                main_modules, "主要模块", task_id, current_step, total_steps
            ))
        
        # 分析具体知识点内部关系（使用滑动窗口）
        if len(specific_points) > 1:
            relations.extend(self._analyze_specific_points_relations(
                specific_points, task_id, current_step, total_steps
            ))
        
        return relations
    
    def _analyze_same_level_batch(self, keywords, level_name, task_id, current_step, total_steps):
        """分批分析同级别关系"""
        relations = []
        batches = self.llm_service.create_batches(keywords, self.config.RELATION_BATCH_SIZE)
        
        for i, batch in enumerate(batches):
            batch_relations = self.llm_service.analyze_relations(batch)
            
            # 验证和去重
            valid_relations = self._validate_and_deduplicate_relations(batch_relations)
            relations.extend(valid_relations)
            
            # 更新进度
            if task_id:
                progress = 80 + int((current_step + i + 1) / total_steps * 10)
                self.data_access.update_task_progress(task_id, progress)
        
        return relations
    
    def _analyze_specific_points_relations(self, specific_points, task_id, current_step, total_steps):
        """使用滑动窗口分析具体知识点关系"""
        relations = []
        window_size = 20
        step_size = 10
        
        for i in range(0, len(specific_points), step_size):
            window = specific_points[i:i + window_size]
            if len(window) > 1:
                window_relations = self.llm_service.analyze_relations(window)
                
                # 验证和去重
                valid_relations = self._validate_and_deduplicate_relations(window_relations)
                relations.extend(valid_relations)
            
            # 更新进度
            if task_id:
                progress = 90 + int((i + 1) / len(specific_points) * 10)
                self.data_access.update_task_progress(task_id, progress)
        
        return relations
    
    def _validate_and_deduplicate_relations(self, relations):
        """验证和去重关系"""
        valid_relations = []
        seen_relations = set()
        
        for relation in relations:
            # 基本验证
            if not isinstance(relation, dict):
                continue
            
            source = relation.get('source')
            target = relation.get('target')
            relation_type = relation.get('relation_type')
            
            if not all([source, target, relation_type]):
                continue
            
            if source == target:
                continue
            
            # 去重
            relation_key = (source, target, relation_type)
            reverse_key = (target, source, relation_type)
            
            if relation_key in seen_relations or reverse_key in seen_relations:
                continue
            
            # 检查数据库中是否已存在
            if self.data_access.check_relation_exists(source, target, relation_type):
                continue
            
            seen_relations.add(relation_key)
            valid_relations.append(relation)
        
        return valid_relations