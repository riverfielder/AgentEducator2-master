"""
统一的LLM服务模块 - 基于LangChain和统一配置管理
提供简洁一致的LLM调用接口
"""
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from typing import Dict, Any, Optional, List
from config.unified_llm_config import get_langchain_config


class UnifiedLLMService:
    """统一的LLM服务类 - 基于LangChain"""
    
    def __init__(self):
        self._llm_instances = {}  # 缓存LangChain LLM实例
        self._embeddings_instances = {}  # 缓存嵌入实例
    
    def get_llm(self, model_key: str, **override_params) -> ChatOpenAI:
        """获取LangChain ChatOpenAI实例"""
        # 创建缓存键
        cache_key = f"{model_key}_{hash(str(sorted(override_params.items())))}"
        
        if cache_key not in self._llm_instances:
            config = get_langchain_config(model_key, **override_params)
            self._llm_instances[cache_key] = ChatOpenAI(**config)
        
        return self._llm_instances[cache_key]
    
    def get_embeddings(self, model_key: str = "embedding", **override_params) -> OpenAIEmbeddings:
        """获取LangChain嵌入实例"""
        # 创建缓存键
        cache_key = f"{model_key}_{hash(str(sorted(override_params.items())))}"
        
        if cache_key not in self._embeddings_instances:
            config = get_langchain_config(model_key, **override_params)
            self._embeddings_instances[cache_key] = OpenAIEmbeddings(**config)
        
        return self._embeddings_instances[cache_key]
    
    def create_chat_llm(self, model_key: str, **override_params) -> ChatOpenAI:
        """创建新的LangChain ChatOpenAI实例（不缓存）"""
        config = get_langchain_config(model_key, **override_params)
        return ChatOpenAI(**config)
    
    def create_embeddings(self, model_key: str = "embedding", **override_params) -> OpenAIEmbeddings:
        """创建新的LangChain嵌入实例（不缓存）"""
        config = get_langchain_config(model_key, **override_params)
        return OpenAIEmbeddings(**config)
    
    def clear_cache(self):
        """清除所有缓存的实例"""
        self._llm_instances.clear()
        self._embeddings_instances.clear()


# 全局服务实例
unified_llm_service = UnifiedLLMService()


# 便捷函数
def get_llm(model_key: str, **override_params) -> ChatOpenAI:
    """获取LangChain ChatOpenAI实例的便捷函数"""
    return unified_llm_service.get_llm(model_key, **override_params)


def get_llm_instance(model_key: str, **override_params) -> ChatOpenAI:
    """获取LangChain ChatOpenAI实例的别名函数，与get_llm相同"""
    return unified_llm_service.get_llm(model_key, **override_params)


def get_embeddings(model_key: str = "embedding", **override_params) -> OpenAIEmbeddings:
    """获取LangChain嵌入实例的便捷函数"""
    return unified_llm_service.get_embeddings(model_key, **override_params)


def create_chat_llm(model_key: str, **override_params) -> ChatOpenAI:
    """创建LangChain ChatOpenAI实例的便捷函数"""
    return unified_llm_service.create_chat_llm(model_key, **override_params)


def create_embeddings(model_key: str = "embedding", **override_params) -> OpenAIEmbeddings:
    """创建LangChain嵌入实例的便捷函数"""
    return unified_llm_service.create_embeddings(model_key, **override_params)


# 向后兼容的别名
create_langchain_llm = create_chat_llm
create_langchain_embeddings = create_embeddings
