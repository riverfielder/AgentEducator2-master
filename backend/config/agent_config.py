"""Agent配置模块"""
from .config import Config
from typing import Dict, Any


class AgentConfig:
    """Agent配置类"""
    
    @classmethod
    def is_agent_mode_enabled(cls) -> bool:
        """检查Agent模式是否启用"""
        return Config.is_agent_mode_enabled()
    
    @classmethod
    def get_max_iterations(cls) -> int:
        """获取最大迭代次数"""
        return Config.get_agent_max_iterations()
    
    @classmethod
    def is_handle_parsing_errors(cls) -> bool:
        """检查是否处理解析错误"""
        return Config.is_agent_handle_parsing_errors()
    
    @classmethod
    def is_verbose(cls) -> bool:
        """检查是否启用详细输出"""
        return Config.is_agent_verbose()
    
    # 工具配置
    TOOL_CONFIGS = {
        "video_search": {
            "enabled": True,
            "max_docs": 5
        },
        "course_search": {
            "enabled": True,
            "max_docs": 6
        },
        "document_search": {
            "enabled": True,
            "max_docs": 5
        },
        "general_search": {
            "enabled": True,
            "max_docs": 5
        },
        "general_knowledge": {
            "enabled": True
        }
    }
    
    # Agent提示模板配置
    PROMPT_CONFIGS = {
        "video_context_description": "你正在为学生解答关于特定视频内容的问题",
        "course_context_description": "你正在为学生解答关于整个课程的问题",
        "general_context_description": "你正在为学生解答教学相关问题",
        
        "video_strategy_guidance": """
优先策略：
1. 如果问题涉及当前视频的具体内容，使用video_search工具
2. 如果问题涉及课程的整体概念或跨视频内容，使用course_search工具
3. 如果检索无结果或问题比较通用，使用general_search工具


""",
        "course_strategy_guidance": """
优先策略：
1. 如果问题涉及课程的教学内容，使用course_search工具
2. 如果检索无结果或问题比较通用，使用general_knowledge工具
""",
        "general_strategy_guidance": """
优先策略：
1. 如果问题涉及教学内容，使用general_search工具
2. 如果检索无结果或问题比较通用，使用general_knowledge工具
"""
    }
      # 缓存配置 - 简化版
    CACHE_CONFIGS = {
        "enabled": False,  # 暂时禁用复杂缓存
        "max_cache_size": 10,
        "cache_timeout": 300   # 5分钟
    }
    
    @classmethod
    def get_tool_config(cls, tool_name: str) -> Dict[str, Any]:
        """获取工具配置"""
        return cls.TOOL_CONFIGS.get(tool_name, {})
    
    @classmethod
    def get_prompt_config(cls, config_key: str) -> str:
        """获取提示模板配置"""
        return cls.PROMPT_CONFIGS.get(config_key, "")
    
    @classmethod
    def is_tool_enabled(cls, tool_name: str) -> bool:
        """检查工具是否启用"""
        return cls.get_tool_config(tool_name).get("enabled", False)
    
    @classmethod
    def update_config(cls, config_dict: Dict[str, Any]):
        """动态更新配置"""
        for key, value in config_dict.items():
            if hasattr(cls, key):
                setattr(cls, key, value)
