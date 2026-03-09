"""QA系统配置模块"""
from .config import Config


class LLMConfig:
    """QA系统配置类"""
    
    # API配置
    SILICON_API_BASE = "https://api.siliconflow.cn/v1"
    API_KEY_DEFAULT = "sk-gplnfadmdaipjskyauqadvqcgbbatvmcrguzcdbnmffsjrzt"
    
    QA_API_BASE = "https://ark.cn-beijing.volces.com/api/v3"
    QA_API_KEY = "373f1f5b-095e-469d-aa93-9319407b8e0f"
    QA_MODEL = "doubao-seed-1-8-251228"
    
    @classmethod
    def get_api_key(cls) -> str:
        """获取API Key"""
        return Config.get_openai_api_key() or cls.API_KEY_DEFAULT
    
    @classmethod
    def get_silicon_api_base(cls) -> str:
        """获取Silicon API Base URL"""
        return Config.get_silicon_api_base()
    
    # 模型配置
    EMBEDDING_MODEL = 'Pro/BAAI/bge-m3'
    CHAT_MODEL = "Pro/deepseek-ai/DeepSeek-V3-1226"
    #CHAT_MODEL='THUDM/GLM-4-32B-0414'
    general_MODEL = "Qwen/Qwen3-8B"
    
    # 向量索引配置
    VECTOR_INDEX_DIR = "vector_indices"
    
    # 检索配置
    BM25_K = 6
    SEMANTIC_K = 4
    SEMANTIC_SCORE_THRESHOLD = 0.3
    SEMANTIC_FETCH_K = 10
    ENSEMBLE_WEIGHTS = [0.6, 0.4]  # BM25权重0.4，语义检索权重0.6
    ENSEMBLE_K = 10
    
    # LLM配置
    TEMPERATURE = 1
    REQUEST_TIMEOUT = 60
    THINKING_TYPE = "disabled"  # 默认禁用深度思考能力，可选值: "disabled", "enabled", "auto"
    
    # 历史消息配置
    MAX_HISTORY_LENGTH = 10
    RECENT_HISTORY_LENGTH = 8
    
    # 缓存配置
    LRU_CACHE_SIZE = 100
    
    # 限流配置
    TPM_LIMIT = 9500  # 每分钟token限制（降低以便测试）
    RPM_LIMIT = 1000     # 每分钟请求限制（降低以便测试）
