"""LangSmith配置模块"""
import os
from typing import Optional


class LangSmithConfig:
    """LangSmith配置管理"""
    
    @staticmethod
    def setup_langsmith(
        api_key: Optional[str] = None,
        project_name: str = "AgentEducator-QA",
        endpoint: str = "https://api.smith.langchain.com",
        enable_tracing: bool = True
    ):
        """设置LangSmith环境变量
        
        Args:
            api_key: LangSmith API密钥，如果为None则从环境变量获取
            project_name: 项目名称
            endpoint: LangSmith端点
            enable_tracing: 是否启用追踪
        """
        # 检查API密钥是否存在
        has_api_key = bool(api_key or os.environ.get("LANGSMITH_API_KEY"))
        
        if enable_tracing and has_api_key:
            os.environ["LANGSMITH_TRACING"] = "true"
            os.environ["LANGSMITH_ENDPOINT"] = endpoint
            os.environ["LANGSMITH_PROJECT"] = project_name
            
            # API密钥优先级：参数 > 环境变量
            if api_key:
                os.environ["LANGSMITH_API_KEY"] = api_key
            
            print(f"[INFO] LangSmith追踪已启用")
            print(f"  - 项目: {project_name}")
            print(f"  - 端点: {endpoint}")
        else:
            # 禁用追踪
            os.environ["LANGSMITH_TRACING"] = "false"
            if enable_tracing and not has_api_key:
                print("[WARNING] 未检测到LangSmith API密钥，追踪功能将自动禁用。如需启用，请设置LANGSMITH_API_KEY环境变量。")
            else:
                print("[INFO] LangSmith追踪已禁用")
    
    @staticmethod
    def is_enabled() -> bool:
        """检查LangSmith是否启用"""
        return os.environ.get("LANGSMITH_TRACING", "false").lower() == "true"
    
    @staticmethod
    def get_project_name() -> str:
        """获取当前项目名称"""
        return os.environ.get("LANGSMITH_PROJECT", "AgentEducator-QA")
    
    @staticmethod
    def get_endpoint() -> str:
        """获取LangSmith端点"""
        return os.environ.get("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")


# 自动初始化LangSmith（开发环境）
def init_langsmith_for_development():
    """开发环境自动初始化LangSmith"""
    try:
        # 检查是否在开发环境
        if os.environ.get("FLASK_ENV") != "production":
            LangSmithConfig.setup_langsmith(
                project_name="AgentEducator-QA-Dev",
                enable_tracing=True
            )
        else:
            print("[INFO] 生产环境，请手动配置LangSmith")
    except Exception as e:
        print(f"[WARNING] LangSmith初始化失败: {e}")


# 模块导入时自动初始化
if __name__ != "__main__":
    init_langsmith_for_development()
