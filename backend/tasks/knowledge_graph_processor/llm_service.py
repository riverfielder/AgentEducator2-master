"""知识图谱处理器LLM服务 - 使用统一配置管理"""

import json
import re
import time
from flask import current_app
from .config import KnowledgeGraphConfig
from .prompt_manager import PromptManager
from services.unified_llm_service import get_llm_instance

class LLMService:
    """LLM服务类"""
    
    def __init__(self, api_key=None, base_url=None, model=None):
        """初始化LLM服务"""
        # 使用统一的LLM服务
        self.llm = get_llm_instance("knowledge_graph_build")
        self.config = KnowledgeGraphConfig()
    
    def classify_keywords(self, keywords):
        """分类关键词"""
        prompt = PromptManager.get_keyword_classification_prompt()
        keywords_text = '\n'.join([f"- {kw}" for kw in keywords])
        
        response = self._call_llm(
            prompt.format(keywords=keywords_text)
        )
        
        return self._parse_classification_response(response)
    
    def analyze_relations(self, keywords, course_info=None):
        """分析关键词关系"""
        # 去重关键词列表
        original_count = len(keywords) if keywords else 0
        keywords = list(set(keywords)) if keywords else []
        
        if not keywords:
            return []
        
        # 记录去重效果
        if original_count != len(keywords):
            current_app.logger.info(f"关键词去重: {original_count}→{len(keywords)}")
        
        prompt = PromptManager.get_relation_analysis_prompt()
        keywords_text = '\n'.join([f"- {kw}" for kw in keywords])
        course_text = f"课程：{course_info.name}" if course_info else "课程信息未提供"
        
        response = self._call_llm(
            prompt.format(keywords=keywords_text, course_info=course_text)
        )
        
        return self._parse_relation_response(response)
    
    def analyze_cross_level_relations(self, level1_keywords, level2_keywords, 
                                    level1_name, level2_name):
        """分析跨级别关系"""
        # 去重输入关键词列表，防止重复分析
        original_l1_count = len(level1_keywords) if level1_keywords else 0
        original_l2_count = len(level2_keywords) if level2_keywords else 0
        
        level1_keywords = list(set(level1_keywords)) if level1_keywords else []
        level2_keywords = list(set(level2_keywords)) if level2_keywords else []
        
        if not level1_keywords or not level2_keywords:
            return []
        
        # 记录去重效果
        if original_l1_count != len(level1_keywords) or original_l2_count != len(level2_keywords):
            current_app.logger.info(f"关键词去重: {level1_name} {original_l1_count}→{len(level1_keywords)}, {level2_name} {original_l2_count}→{len(level2_keywords)}")
        
        prompt = PromptManager.get_cross_level_relation_prompt()
        level1_text = '\n'.join([f"- {kw}" for kw in level1_keywords])
        level2_text = '\n'.join([f"- {kw}" for kw in level2_keywords])
        
        response = self._call_llm(
            prompt.format(
                level1_name=level1_name,
                level2_name=level2_name,
                level1_keywords=level1_text,
                level2_keywords=level2_text
            )
        )
        
        return self._parse_relation_response(response)
    
    def analyze_cluster_relations(self, keywords, course_info, similarity):
        """分析聚类关系"""
        prompt = PromptManager.get_cluster_relation_prompt()
        keywords_text = '\n'.join([f"- {kw}" for kw in keywords])
        course_text = f"课程：{course_info.name}" if course_info else "课程信息未提供"
        
        response = self._call_llm(
            prompt.format(
                keywords=keywords_text,
                course_info=course_text,
                similarity=similarity
            )
        )
        
        return self._parse_relation_response(response)
    
    def connect_orphaned_keywords(self, orphaned_keywords, connected_keywords):
        """连接孤立关键词"""
        prompt = PromptManager.get_orphaned_keywords_prompt()
        orphaned_text = '\n'.join([f"- {kw}" for kw in orphaned_keywords])
        connected_text = '\n'.join([f"- {kw}" for kw in connected_keywords])
        
        response = self._call_llm(
            prompt.format(
                orphaned_keywords=orphaned_text,
                connected_keywords=connected_text
            )
        )
        
        return self._parse_relation_response(response)
    
    def analyze_incremental_relations(self, new_keywords, existing_keywords):
        """分析增量关系"""
        # 去重关键词列表
        original_new_count = len(new_keywords) if new_keywords else 0
        original_existing_count = len(existing_keywords) if existing_keywords else 0
        
        new_keywords = list(set(new_keywords)) if new_keywords else []
        existing_keywords = list(set(existing_keywords)) if existing_keywords else []
        
        if not new_keywords or not existing_keywords:
            return []
        
        # 记录去重效果
        if original_new_count != len(new_keywords) or original_existing_count != len(existing_keywords):
            current_app.logger.info(f"增量关系关键词去重: 新关键词 {original_new_count}→{len(new_keywords)}, 现有关键词 {original_existing_count}→{len(existing_keywords)}")
        
        prompt = PromptManager.get_incremental_relation_prompt()
        new_text = '\n'.join([f"- {kw}" for kw in new_keywords])
        existing_text = '\n'.join([f"- {kw}" for kw in existing_keywords])
        
        response = self._call_llm(
            prompt.format(
                new_keywords=new_text,
                existing_keywords=existing_text
            )
        )
        
        return self._parse_relation_response(response)
    
    def _call_llm(self, prompt, max_retries=None):
        """调用LLM"""
        max_retries = max_retries or self.config.MAX_RETRIES
        
        for attempt in range(max_retries):
            try:
                messages = [
                    {"role": "system", "content": "你是一个专业的知识图谱分析师。"},
                    {"role": "user", "content": prompt}
                ]
                
                response = self.llm.invoke(messages)
                return response.content.strip()
                
            except Exception as e:
                current_app.logger.error(f"LLM调用失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(self.config.RETRY_DELAY)
                else:
                    raise e
    
    def _parse_classification_response(self, response):
        """解析分类响应"""
        try:
            # 尝试直接解析JSON
            data = json.loads(response)
            if 'classifications' in data:
                return data['classifications']
        except json.JSONDecodeError:
            pass
        
        # 尝试提取JSON部分
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                if 'classifications' in data:
                    return data['classifications']
            except json.JSONDecodeError:
                pass
        
        current_app.logger.error(f"无法解析分类响应: {response}")
        return []
    
    def _parse_relation_response(self, response):
        """解析关系响应"""
        try:
            # 尝试直接解析JSON
            data = json.loads(response)
            if 'relations' in data:
                return self._validate_relations(data['relations'])
        except json.JSONDecodeError:
            pass
        
        # 尝试提取JSON部分
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                if 'relations' in data:
                    return self._validate_relations(data['relations'])
            except json.JSONDecodeError:
                pass
        
        # 尝试模式匹配
        relations = self._extract_relations_by_pattern(response)
        if relations:
            return relations
        
        current_app.logger.error(f"无法解析关系响应: {response}")
        return []
    
    def _validate_relations(self, relations):
        """验证关系数据"""
        valid_relations = []
        valid_types = self.config.get_all_relation_types()
        
        for relation in relations:
            if not isinstance(relation, dict):
                continue
            
            # 检查必需字段
            if not all(key in relation for key in ['source', 'target', 'relation_type']):
                continue
            
            # 检查关系类型
            if relation['relation_type'] not in valid_types:
                continue
            
            # 检查源和目标不能相同
            if relation['source'] == relation['target']:
                continue
            
            # 设置默认置信度
            if 'confidence' not in relation:
                relation['confidence'] = 0.8
            
            valid_relations.append(relation)
        
        return valid_relations
    
    def _extract_relations_by_pattern(self, response):
        """通过模式匹配提取关系"""
        relations = []
        valid_types = self.config.get_all_relation_types()
        
        # 匹配关系模式
        patterns = [
            r'(\w+)\s*->\s*(\w+)\s*\[(\w+)\]',
            r'(\w+)\s*-\s*(\w+)\s*:\s*(\w+)',
            r'(\w+)\s*关系\s*(\w+)\s*:\s*(\w+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response)
            for match in matches:
                if len(match) == 3:
                    source, target, rel_type = match
                    if rel_type in valid_types and source != target:
                        relations.append({
                            'source': source,
                            'target': target,
                            'relation_type': rel_type,
                            'confidence': 0.7,
                            'reason': '模式匹配提取'
                        })
        
        return relations
    
    def create_batches(self, items, batch_size=None):
        """创建批次"""
        batch_size = batch_size or self.config.KEYWORD_BATCH_SIZE
        batches = []
        for i in range(0, len(items), batch_size):
            batches.append(items[i:i + batch_size])
        return batches