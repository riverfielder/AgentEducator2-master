"""
统一的LLM配置管理器
用于集中管理所有LLM相关的API端点、密钥、模型名称和参数
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class LLMProvider(Enum):
    """LLM服务提供商枚举"""
    SILICONFLOW = "siliconflow"
    VOLCENGINE = "volcengine"
    OPENAI = "openai"
    AZURE = "azure"


@dataclass
class LLMEndpointConfig:
    """LLM端点配置"""
    provider: LLMProvider
    base_url: str
    api_key: str
    description: str = ""


@dataclass 
class LLMModelConfig:
    """LLM模型配置"""
    model_name: str
    provider: LLMProvider
    endpoint_key: str
    default_params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


class UnifiedLLMConfig:
    """统一LLM配置管理器"""
    
    def __init__(self):
        self._endpoints = {}
        self._models = {}
        self._load_default_config()
    
    def _load_default_config(self):
        """加载默认配置"""
        
        # =============================================================================
        # API端点配置
        # =============================================================================
        
        # 硅基流动端点
        self._endpoints["siliconflow_main"] = LLMEndpointConfig(
            provider=LLMProvider.SILICONFLOW,
            base_url=os.getenv("SILICONFLOW_API_BASE", "https://api.siliconflow.cn/v1"),
            api_key=os.getenv("SILICONFLOW_API_KEY", "sk-gplnfadmdaipjskyauqadvqcgbbatvmcrguzcdbnmffsjrzt"),
            description="硅基流动主要API端点"
        )
        
        # 火山引擎端点
        self._endpoints["volcengine_doubao"] = LLMEndpointConfig(
            provider=LLMProvider.VOLCENGINE,
            base_url=os.getenv("VOLCENGINE_API_BASE", "https://ark.cn-beijing.volces.com/api/v3"),
            api_key=os.getenv("VOLCENGINE_API_KEY", "373f1f5b-095e-469d-aa93-9319407b8e0f"),
            description="火山引擎豆包API端点"
        )
        
        # OpenAI端点（备用）
        self._endpoints["openai_official"] = LLMEndpointConfig(
            provider=LLMProvider.OPENAI,
            base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
            api_key=os.getenv("OPENAI_API_KEY", ""),
            description="OpenAI官方API端点"
        )
        
        # =============================================================================
        # 模型配置
        # =============================================================================
        
        # 知识图谱相关模型
        self._models["knowledge_graph_analysis"] = LLMModelConfig(
            model_name="doubao-seed-1-6-flash-250615",
            provider=LLMProvider.VOLCENGINE,
            endpoint_key="volcengine_doubao",
            default_params={
                "temperature": 1.0,
                "timeout": 36000,
                "thinking": {"type": "disabled"}
            },
            description="知识图谱关系分析和分类"
        )
        
        
        self._models["knowledge_graph_build"] = LLMModelConfig(
            model_name="doubao-seed-1-6-250615",
            provider=LLMProvider.VOLCENGINE,
            endpoint_key="volcengine_doubao",
            default_params={
                "temperature": 1.0,
                "timeout": 36000,
                "thinking": {"type": "disabled"}
            },
            description="知识图谱聊天模型"
        )
        
        # 文档和视频处理模型
        self._models["document_processor"] = LLMModelConfig(
            model_name="doubao-seed-1-6-flash-250615",
            provider=LLMProvider.VOLCENGINE,
            endpoint_key="volcengine_doubao",
            default_params={
                "temperature": 1.0,
                "timeout": 36000,
                "thinking": {"type": "disabled"}
            },
            description="文档摘要和关键词提取"
        )
        
        self._models["video_processor"] = LLMModelConfig(
            model_name="doubao-seed-1-6-flash-250615",
            provider=LLMProvider.VOLCENGINE,
            endpoint_key="volcengine_doubao",
            default_params={
                "temperature": 1.0,
                "timeout": 36000,
                "thinking": {"type": "disabled"}
            },
            description="视频摘要生成"
        )
        
        # QA和聊天模型
        self._models["qa_main"] = LLMModelConfig(
            model_name="doubao-seed-1-6-250615",
            provider=LLMProvider.VOLCENGINE,
            endpoint_key="volcengine_doubao",
            default_params={
                "temperature": 1.0,
                "timeout": 36000,
                "thinking": {"type": "disabled"}
            },
            description="主要QA问答模型"
        )
        
        self._models["question_import"] = LLMModelConfig(
            model_name="doubao-seed-1-6-flash-250615",
            provider=LLMProvider.VOLCENGINE,
            endpoint_key="volcengine_doubao",
            default_params={
                "temperature": 1.0,
                "timeout": 36000,
                "thinking": {"type": "disabled"}
            },
            description="快速题库处理模型"
        )
        
        self._models["general"] = LLMModelConfig(
            model_name="doubao-seed-1-6-250615",
            provider=LLMProvider.VOLCENGINE,
            endpoint_key="volcengine_doubao",
            default_params={
                "temperature": 1.0,
                "timeout": 36000,
                "thinking": {"type": "disabled"}
            },
            description="通用模型"
        )
        
        self._models["general_lite"] = LLMModelConfig(
            model_name="doubao-seed-1-6-flash-250615",
            provider=LLMProvider.VOLCENGINE,
            endpoint_key="volcengine_doubao",
            default_params={
                "temperature": 1.0,
                "timeout": 36000,
                "thinking": {"type": "disabled"}
            },
            description="通用轻型模型"
        )
        self._models["general_lite_20"] = LLMModelConfig(
            model_name="doubao-seed-1-6-flash-250615",
            provider=LLMProvider.VOLCENGINE,
            endpoint_key="volcengine_doubao",
            default_params={
                "temperature": 1.0,
                "timeout": 10,
                "thinking": {"type": "disabled"}
            },
            description="短超时轻型模型"
        )
        # 嵌入模型
        self._models["embedding"] = LLMModelConfig(
            model_name="Pro/BAAI/bge-m3",
            provider=LLMProvider.SILICONFLOW,
            endpoint_key="siliconflow_main",
            default_params={
                "timeout": 60
            },
            description="文本嵌入模型"
        )
        
        # 演示和测试模型
        self._models["demo_chat"] = LLMModelConfig(
            model_name="deepseek-ai/DeepSeek-V3",
            provider=LLMProvider.SILICONFLOW,
            endpoint_key="siliconflow_main",
            default_params={
                "temperature": 0.7,
                "timeout": 60
            },
            description="演示系统聊天模型"
        )
    
    # =============================================================================
    # 公共接口方法
    # =============================================================================
    
    def get_endpoint_config(self, endpoint_key: str) -> Optional[LLMEndpointConfig]:
        """获取端点配置"""
        return self._endpoints.get(endpoint_key)
    
    def get_model_config(self, model_key: str) -> Optional[LLMModelConfig]:
        """获取模型配置"""
        return self._models.get(model_key)
    
    def get_langchain_config(self, model_key: str, **override_params) -> Dict[str, Any]:
        """获取LangChain兼容的配置"""
        model_config = self.get_model_config(model_key)
        if not model_config:
            raise ValueError(f"Model config not found: {model_key}")
        
        endpoint_config = self.get_endpoint_config(model_config.endpoint_key)
        if not endpoint_config:
            raise ValueError(f"Endpoint config not found: {model_config.endpoint_key}")
        
        # 合并配置
        merged_params = {
            **model_config.default_params,
            **override_params  # 覆盖参数
        }
        
        # 转换为LangChain格式
        langchain_config = {
            "openai_api_key": endpoint_config.api_key,
            "openai_api_base": endpoint_config.base_url,
            "model": model_config.model_name,
        }
        
        # 处理特殊参数
        if "timeout" in merged_params:
            langchain_config["request_timeout"] = merged_params.pop("timeout")
        
        if "thinking" in merged_params:
            langchain_config["extra_body"] = {"thinking": merged_params.pop("thinking")}
        
        # 添加其他参数
        langchain_config.update(merged_params)
        
        return langchain_config
    
    def list_models(self, provider: Optional[LLMProvider] = None) -> Dict[str, LLMModelConfig]:
        """列出所有模型配置"""
        if provider is None:
            return self._models.copy()
        
        return {k: v for k, v in self._models.items() if v.provider == provider}
    
    def list_endpoints(self, provider: Optional[LLMProvider] = None) -> Dict[str, LLMEndpointConfig]:
        """列出所有端点配置"""
        if provider is None:
            return self._endpoints.copy()
        
        return {k: v for k, v in self._endpoints.items() if v.provider == provider}
    
    # =============================================================================
    # 配置管理方法
    # =============================================================================
    
    def add_endpoint(self, key: str, config: LLMEndpointConfig):
        """添加端点配置"""
        self._endpoints[key] = config
    
    def add_model(self, key: str, config: LLMModelConfig):
        """添加模型配置"""
        self._models[key] = config
    
    def remove_endpoint(self, key: str):
        """移除端点配置"""
        if key in self._endpoints:
            del self._endpoints[key]
    
    def remove_model(self, key: str):
        """移除模型配置"""
        if key in self._models:
            del self._models[key]
    
    def update_endpoint(self, key: str, **updates):
        """更新端点配置"""
        if key in self._endpoints:
            config = self._endpoints[key]
            for attr, value in updates.items():
                if hasattr(config, attr):
                    setattr(config, attr, value)
    
    def update_model_params(self, key: str, **params):
        """更新模型参数"""
        if key in self._models:
            self._models[key].default_params.update(params)


# =============================================================================
# 全局配置实例
# =============================================================================

# 创建全局配置实例
llm_config_manager = UnifiedLLMConfig()


# =============================================================================
# 便捷函数
# =============================================================================

def get_langchain_config(model_key: str, **override_params) -> Dict[str, Any]:
    """获取LangChain配置的便捷函数"""
    return llm_config_manager.get_langchain_config(model_key, **override_params)


def list_available_models() -> Dict[str, str]:
    """列出所有可用模型的便捷函数"""
    models = llm_config_manager.list_models()
    return {k: v.description for k, v in models.items()}


# =============================================================================
# 使用示例和测试函数
# =============================================================================

def print_config_summary():
    """打印配置摘要"""
    print("=== LLM配置管理器摘要 ===")
    
    print("\n可用端点:")
    for key, config in llm_config_manager.list_endpoints().items():
        print(f"  {key}: {config.base_url} ({config.provider.value})")
    
    print("\n可用模型:")
    for key, config in llm_config_manager.list_models().items():
        print(f"  {key}: {config.model_name} ({config.provider.value})")
        print(f"    {config.description}")


if __name__ == "__main__":
    print_config_summary()
    
    # 测试配置获取
    print("\n=== 测试配置获取 ===")
    
    try:
        config = get_langchain_config("knowledge_graph_analysis", temperature=0.5)
        print("知识图谱分析模型配置:", config)
        
        config = get_langchain_config("qa_main", streaming=True)
        print("QA主模型配置:", config)
        
    except Exception as e:
        print(f"配置获取失败: {e}")
