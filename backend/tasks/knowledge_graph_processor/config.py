"""知识图谱处理器配置类"""

class KnowledgeGraphConfig:
    """知识图谱处理配置"""
    
    # LLM配置
    DEFAULT_MODEL = "gpt-4o-mini"
    MAX_TOKENS = 4000
    TEMPERATURE = 0.1
    CHAT_MODEL = "THUDM/GLM-4-32B-0414"
    # 批处理配置
    KEYWORD_BATCH_SIZE = 50
    RELATION_BATCH_SIZE = 50
    CLUSTER_BATCH_SIZE = 10
    
    # 聚类配置
    MIN_CLUSTER_SIZE = 2
    MAX_CLUSTERS_RATIO = 0.3
    SIMILARITY_THRESHOLD = 0.3
    
    # 知识点分类
    KEYWORD_CATEGORIES = {
        'core_concept': '核心概念',
        'main_module': '主要模块', 
        'specific_point': '具体知识点'
    }
    
    # 关系类型
    RELATION_TYPES = {
        'prerequisite': '前置关系',
        'related': '相关关系',
        'contains': '包含关系',
        'similar': '相似关系'
    }
    
    # 进度更新间隔
    PROGRESS_UPDATE_INTERVAL = 10
    
    # 重试配置
    MAX_RETRIES = 3
    RETRY_DELAY = 1
    
    @classmethod
    def get_category_description(cls, category):
        """获取分类描述"""
        return cls.KEYWORD_CATEGORIES.get(category, category)
    
    @classmethod
    def get_relation_description(cls, relation_type):
        """获取关系类型描述"""
        return cls.RELATION_TYPES.get(relation_type, relation_type)
    
    @classmethod
    def get_all_categories(cls):
        """获取所有分类"""
        return list(cls.KEYWORD_CATEGORIES.keys())
    
    @classmethod
    def get_all_relation_types(cls):
        """获取所有关系类型"""
        return list(cls.RELATION_TYPES.keys())