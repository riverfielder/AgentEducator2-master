"""嵌入模型服务模块 - 使用统一配置管理"""
from langchain_openai import OpenAIEmbeddings
from config.unified_llm_config import get_langchain_config


class EmbeddingsService:
    """嵌入模型服务（单例模式）"""
    
    _instance = None
    _embeddings = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_embeddings(self):
        """获取嵌入模型"""
        if self._embeddings is None:
            config = get_langchain_config("embedding")
            self._embeddings = OpenAIEmbeddings(**config)
        return self._embeddings


# 全局实例
embeddings_service = EmbeddingsService()
