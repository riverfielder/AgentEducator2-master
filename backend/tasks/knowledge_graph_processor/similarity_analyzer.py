"""知识图谱处理器相似度聚类分析器"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import AgglomerativeClustering
from flask import current_app
from .data_access import KnowledgeGraphDataAccess
from .llm_service import LLMService
from .config import KnowledgeGraphConfig

class SimilarityAnalyzer:
    """相似度聚类分析器"""
    
    def __init__(self, llm_service=None):
        """初始化相似度分析器"""
        self.llm_service = llm_service or LLMService()
        self.data_access = KnowledgeGraphDataAccess()
        self.config = KnowledgeGraphConfig()
    
    def perform_similarity_clustering(self, course_id, task_id=None):
        """执行相似度聚类分析"""
        current_app.logger.info(f"开始对课程 {course_id} 执行相似度聚类分析")
        
        # 收集关键词信息
        keyword_info = self._collect_keyword_info(course_id)
        
        if len(keyword_info) < self.config.MIN_CLUSTER_SIZE:
            current_app.logger.warning(f"关键词数量不足，跳过聚类分析")
            return []
        
        # 执行聚类
        clusters = self._cluster_keywords_by_similarity(keyword_info)
        
        if not clusters:
            current_app.logger.info("没有找到有效的聚类")
            return []
        
        current_app.logger.info(f"找到 {len(clusters)} 个聚类")
        
        # 分析聚类关系
        course_info = self.data_access.get_course_info(course_id)
        cluster_relations = self._analyze_cluster_relations(
            clusters, course_info, task_id
        )
        
        current_app.logger.info(f"聚类分析完成，生成了 {len(cluster_relations)} 个关系")
        return cluster_relations
    
    def _collect_keyword_info(self, course_id):
        """收集关键词信息"""
        all_keywords = self.data_access.get_all_course_keywords(course_id)
        
        keyword_info = []
        for keyword in all_keywords:
            # 构建关键词的文本表示（可以包含更多上下文信息）
            text_representation = keyword.name
            
            # 如果有分类信息，加入文本表示
            if keyword.category:
                text_representation += f" {self.config.get_category_description(keyword.category)}"
            
            keyword_info.append({
                'id': keyword.id,
                'name': keyword.name,
                'text': text_representation,
                'category': keyword.category
            })
        
        return keyword_info
    
    def _cluster_keywords_by_similarity(self, keyword_info):
        """基于相似度聚类关键词"""
        if len(keyword_info) < self.config.MIN_CLUSTER_SIZE:
            return []
        
        # 提取文本
        texts = [info['text'] for info in keyword_info]
        
        # TF-IDF向量化
        try:
            vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words=None,  # 中文没有内置停用词
                ngram_range=(1, 2)
            )
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # 计算余弦相似度
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # 转换为距离矩阵
            distance_matrix = 1 - similarity_matrix
            
            # 动态确定聚类数量
            n_keywords = len(keyword_info)
            max_clusters = max(2, int(n_keywords * self.config.MAX_CLUSTERS_RATIO))
            min_clusters = 2
            
            best_clusters = None
            best_score = -1
            
            # 尝试不同的聚类数量
            for n_clusters in range(min_clusters, min(max_clusters + 1, n_keywords)):
                try:
                    clustering = AgglomerativeClustering(
                        n_clusters=n_clusters,
                        metric='precomputed',
                        linkage='average'
                    )
                    cluster_labels = clustering.fit_predict(distance_matrix)
                    
                    # 评估聚类质量（简单的轮廓系数近似）
                    score = self._evaluate_clustering(similarity_matrix, cluster_labels)
                    
                    if score > best_score:
                        best_score = score
                        best_clusters = cluster_labels
                
                except Exception as e:
                    current_app.logger.warning(f"聚类失败 (n_clusters={n_clusters}): {str(e)}")
                    continue
            
            if best_clusters is None:
                current_app.logger.warning("所有聚类尝试都失败了")
                return []
            
            # 组织聚类结果
            clusters = self._organize_clusters(keyword_info, best_clusters, similarity_matrix)
            
            # 过滤小聚类
            filtered_clusters = [
                cluster for cluster in clusters 
                if len(cluster['keywords']) >= self.config.MIN_CLUSTER_SIZE
            ]
            
            # 按聚类大小和相似度排序
            filtered_clusters.sort(
                key=lambda x: (len(x['keywords']), x['avg_similarity']), 
                reverse=True
            )
            
            return filtered_clusters
            
        except Exception as e:
            current_app.logger.error(f"聚类过程出错: {str(e)}")
            return []
    
    def _evaluate_clustering(self, similarity_matrix, cluster_labels):
        """评估聚类质量"""
        try:
            n_samples = len(cluster_labels)
            if n_samples == 0:
                return -1
            
            # 计算聚类内平均相似度
            intra_cluster_similarities = []
            
            for cluster_id in set(cluster_labels):
                cluster_indices = [i for i, label in enumerate(cluster_labels) if label == cluster_id]
                
                if len(cluster_indices) < 2:
                    continue
                
                # 计算聚类内相似度
                cluster_similarities = []
                for i in range(len(cluster_indices)):
                    for j in range(i + 1, len(cluster_indices)):
                        idx1, idx2 = cluster_indices[i], cluster_indices[j]
                        cluster_similarities.append(similarity_matrix[idx1][idx2])
                
                if cluster_similarities:
                    intra_cluster_similarities.extend(cluster_similarities)
            
            if not intra_cluster_similarities:
                return -1
            
            return np.mean(intra_cluster_similarities)
            
        except Exception as e:
            current_app.logger.warning(f"聚类评估出错: {str(e)}")
            return -1
    
    def _organize_clusters(self, keyword_info, cluster_labels, similarity_matrix):
        """组织聚类结果"""
        clusters = {}
        
        for i, (info, label) in enumerate(zip(keyword_info, cluster_labels)):
            if label not in clusters:
                clusters[label] = {
                    'keywords': [],
                    'indices': []
                }
            
            clusters[label]['keywords'].append(info['name'])
            clusters[label]['indices'].append(i)
        
        # 计算每个聚类的平均相似度
        result_clusters = []
        for cluster_id, cluster_data in clusters.items():
            indices = cluster_data['indices']
            
            # 计算聚类内平均相似度
            if len(indices) >= 2:
                similarities = []
                for i in range(len(indices)):
                    for j in range(i + 1, len(indices)):
                        idx1, idx2 = indices[i], indices[j]
                        similarities.append(similarity_matrix[idx1][idx2])
                
                avg_similarity = np.mean(similarities) if similarities else 0
            else:
                avg_similarity = 0
            
            result_clusters.append({
                'id': cluster_id,
                'keywords': cluster_data['keywords'],
                'avg_similarity': avg_similarity,
                'size': len(cluster_data['keywords'])
            })
        
        return result_clusters
    
    def _analyze_cluster_relations(self, clusters, course_info, task_id=None):
        """分析聚类关系"""
        all_relations = []
        print(all_relations)
        print(clusters)
        # 过滤出有效聚类（大小>=2且相似度>=阈值）
        valid_clusters = [
            cluster for cluster in clusters
            if cluster['size'] >= self.config.MIN_CLUSTER_SIZE 
            and cluster['avg_similarity'] >= self.config.SIMILARITY_THRESHOLD
        ]
        
        if not valid_clusters:
            current_app.logger.info("没有找到有效的聚类进行关系分析")
            return []
        
        current_app.logger.info(f"开始分析 {len(valid_clusters)} 个有效聚类的关系")
        
        # 分批处理聚类
        batches = self.llm_service.create_batches(valid_clusters, self.config.CLUSTER_BATCH_SIZE)
        
        for i, batch in enumerate(batches):
            current_app.logger.info(f"正在分析第 {i+1}/{len(batches)} 批聚类关系")
            
            for cluster in batch:
                try:
                    cluster_relations = self.llm_service.analyze_cluster_relations(
                        cluster['keywords'], course_info, cluster['avg_similarity']
                    )
                    
                    # 验证关系
                    valid_relations = self._validate_cluster_relations(
                        cluster_relations, cluster['keywords']
                    )
                    
                    all_relations.extend(valid_relations)
                    
                except Exception as e:
                    current_app.logger.error(f"分析聚类 {cluster['id']} 关系时出错: {str(e)}")
                    continue
            
            # 更新进度
            if task_id:
                progress = 70 + int((i + 1) / len(batches) * 20)  # 聚类分析占70-90%
                self.data_access.update_task_progress(task_id, progress)
        
        current_app.logger.info(f"聚类关系分析完成，生成了 {len(all_relations)} 个关系")
        return all_relations
    
    def _validate_cluster_relations(self, relations, cluster_keywords):
        """验证聚类关系"""
        valid_relations = []
        cluster_keyword_set = set(cluster_keywords)
        
        for relation in relations:
            if not isinstance(relation, dict):
                continue
            
            source = relation.get('source')
            target = relation.get('target')
            relation_type = relation.get('relation_type')
            
            if not all([source, target, relation_type]):
                continue
            
            # 确保源和目标都在聚类中
            if source not in cluster_keyword_set or target not in cluster_keyword_set:
                continue
            
            # 确保源和目标不同
            if source == target:
                continue
            
            # 检查关系类型是否有效
            valid_types = self.config.get_all_relation_types() + ['similar']
            if relation_type not in valid_types:
                continue
            
            valid_relations.append(relation)
        
        return valid_relations