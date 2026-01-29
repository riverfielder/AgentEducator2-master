"""SSL配置模块 - 解决证书验证问题"""
import os
import ssl
import urllib3
from urllib3.exceptions import InsecureRequestWarning


class SSLConfig:
    """SSL配置管理"""
    
    @staticmethod
    def setup_ssl_environment():
        """配置SSL环境，解决证书验证问题"""
        try:
            # 方案1: 设置SSL验证环境变量
            os.environ["PYTHONHTTPSVERIFY"] = "0"
            os.environ["SSL_VERIFY"] = "false"
            
            # 方案2: 创建不验证SSL的上下文
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # 方案3: 禁用urllib3的SSL警告
            urllib3.disable_warnings(InsecureRequestWarning)
            
            print("[INFO] SSL配置已设置 - 开发环境跳过证书验证")
            
        except Exception as e:
            print(f"[WARNING] SSL配置设置失败: {e}")
    
    @staticmethod
    def get_httpx_client_kwargs():
        """获取httpx客户端的SSL配置"""
        return {
            "verify": False,  # 跳过SSL验证
            "timeout": 60.0   # 设置超时
        }
    
    @staticmethod
    def get_openai_client_kwargs():
        """获取OpenAI客户端的配置"""
        return {
            "timeout": 60.0,
            "max_retries": 3
        }


# 全局SSL配置
ssl_config = SSLConfig()
