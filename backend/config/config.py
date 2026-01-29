import os
from typing import Any, Dict, Optional

class RuntimeConfigMixin:
    """支持运行时修改配置的混入类"""
    _runtime_overrides: Dict[str, Any] = {}
    
    @classmethod
    def get_config_value(cls, key: str, default: Any = None) -> Any:
        """获取配置值，优先级：运行时覆盖 > 环境变量 > 类属性 > 默认值"""
        if key in cls._runtime_overrides:
            return cls._runtime_overrides[key]
        
        # 获取环境变量名的映射
        env_key_map = getattr(cls, '_env_key_map', {})
        env_key = env_key_map.get(key, key)
        
        # 检查环境变量
        env_value = os.environ.get(env_key)
        if env_value is not None:
            return env_value
            
        # 获取类属性
        class_value = getattr(cls, key, None)
        if class_value is not None:
            return class_value
            
        return default
    
    @classmethod
    def set_config_value(cls, key: str, value: Any) -> None:
        """设置运行时配置值"""
        cls._runtime_overrides[key] = value
    
    @classmethod
    def reset_config_value(cls, key: str) -> None:
        """重置运行时配置值"""
        if key in cls._runtime_overrides:
            del cls._runtime_overrides[key]
    
    @classmethod
    def get_all_overrides(cls) -> Dict[str, Any]:
        """获取所有运行时覆盖的配置"""
        return cls._runtime_overrides.copy()
    
    @classmethod
    def clear_all_overrides(cls) -> None:
        """清除所有运行时覆盖的配置"""
        cls._runtime_overrides.clear()

class Config(RuntimeConfigMixin):
    # 环境变量名映射
    _env_key_map = {
        'OPENAI_API_KEY': 'OPENAI_API_KEY',
        'SILICON_API_BASE': 'SILICON_API_BASE',
        'NEO4J_URI': 'NEO4J_URI',
        'NEO4J_USERNAME': 'NEO4J_USERNAME',
        'NEO4J_PASSWORD': 'NEO4J_PASSWORD',
        'UPLOAD_BASE_PATH': 'UPLOAD_BASE_PATH',
        'UPLOAD_IMAGE_FOLDER': 'UPLOAD_IMAGE_FOLDER',
        'UPLOAD_VIDEO_FOLDER': 'UPLOAD_VIDEO_FOLDER',
        'UPLOAD_DOCUMENT_FOLDER': 'UPLOAD_DOCUMENT_FOLDER',
        'UPLOAD_AVATAR_FOLDER': 'UPLOAD_AVATAR_FOLDER',
        'UPLOAD_DEFAULT_FOLDER': 'UPLOAD_DEFAULT_FOLDER',
        'AGENT_MODE_ENABLED': 'AGENT_MODE_ENABLED',
        'AGENT_MAX_ITERATIONS': 'AGENT_MAX_ITERATIONS',
        'AGENT_HANDLE_PARSING_ERRORS': 'AGENT_HANDLE_PARSING_ERRORS',
        'AGENT_VERBOSE': 'AGENT_VERBOSE',
    }
    
    # 数据库配置 - 阿里云RDS MySQL（使用正确的外网地址）
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://wendao_manager:wendao_123@rm-bp1cbv056401an0hcso.mysql.rds.aliyuncs.com:3306/wendao_platform'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # 连接池预检查
        'pool_recycle': 3600,   # 连接回收时间
        'pool_timeout': 20,     # 连接超时
        'max_overflow': 0,      # 最大溢出连接数
        'pool_size': 10,        # 连接池大小
        'echo': False           # 不显示SQL语句（生产环境）
    }
    
    # JWT配置
    SECRET_KEY = 'your-very-secret-key-for-jwt-encoding'
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 令牌过期时间(秒)
    

    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 最大500MB
    

    SILICON_API_BASE = "https://api.siliconflow.cn/v1"
    
    # Neo4j 配置
    NEO4J_URI = 'bolt://localhost:7687'
    NEO4J_USERNAME = 'neo4j'
    NEO4J_PASSWORD = 'neo4j'
    
    # 文件上传路径配置
    UPLOAD_BASE_PATH = '.'
    UPLOAD_IMAGE_FOLDER = 'temp_img'
    UPLOAD_VIDEO_FOLDER = 'temp_video'
    UPLOAD_DOCUMENT_FOLDER = 'temp_docs'
    UPLOAD_AVATAR_FOLDER = 'temp_avatars'
    UPLOAD_DEFAULT_FOLDER = 'temp_uploads'
    
    # Agent 配置
    AGENT_MODE_ENABLED = False
    AGENT_MAX_ITERATIONS = 5
    AGENT_HANDLE_PARSING_ERRORS = True
    AGENT_VERBOSE = True
    
    TENCENT_OCR_SECRET_ID = os.environ.get('TENCENT_OCR_SECRET_ID', '')
    TENCENT_OCR_SECRET_KEY = os.environ.get('TENCENT_OCR_SECRET_KEY', '')
    OCR_ENGINE='paddle'  # 可选值: 'cnocr', 'tencent', 'paddle'
    
    # PaddleOCR配置
    PADDLE_OCR_USE_GPU = False  # 是否使用GPU
    PADDLE_OCR_LANG = 'ch'      # 语言: 'ch'(中文), 'en'(英文), 'korean', 'japan'等
    PADDLE_OCR_USE_ANGLE_CLS = True  # 是否使用角度分类模型
    
    @classmethod
    def get_openai_api_key(cls) -> Optional[str]:
        """获取OpenAI API Key"""
        return cls.get_config_value('OPENAI_API_KEY')
    
    @classmethod
    def get_silicon_api_base(cls) -> str:
        """获取Silicon API Base URL"""
        return cls.get_config_value('SILICON_API_BASE', cls.SILICON_API_BASE)
    
    @classmethod
    def get_neo4j_uri(cls) -> str:
        """获取Neo4j URI"""
        return cls.get_config_value('NEO4J_URI', cls.NEO4J_URI)
    
    @classmethod
    def get_neo4j_username(cls) -> str:
        """获取Neo4j用户名"""
        return cls.get_config_value('NEO4J_USERNAME', cls.NEO4J_USERNAME)
    
    @classmethod
    def get_neo4j_password(cls) -> str:
        """获取Neo4j密码"""
        return cls.get_config_value('NEO4J_PASSWORD', cls.NEO4J_PASSWORD)
    
    @classmethod
    def get_upload_base_path(cls) -> str:
        """获取上传基础路径"""
        return cls.get_config_value('UPLOAD_BASE_PATH', cls.UPLOAD_BASE_PATH)
    
    @classmethod
    def get_upload_folder(cls, folder_type: str) -> str:
        """获取特定类型的上传文件夹"""
        folder_map = {
            'image': 'UPLOAD_IMAGE_FOLDER',
            'video': 'UPLOAD_VIDEO_FOLDER', 
            'document': 'UPLOAD_DOCUMENT_FOLDER',
            'avatar': 'UPLOAD_AVATAR_FOLDER',
            'default': 'UPLOAD_DEFAULT_FOLDER'
        }
        key = folder_map.get(folder_type, 'UPLOAD_DEFAULT_FOLDER')
        default_value = getattr(cls, key, cls.UPLOAD_DEFAULT_FOLDER)
        return cls.get_config_value(key, default_value)
    
    @classmethod
    def is_agent_mode_enabled(cls) -> bool:
        """检查Agent模式是否启用"""
        value = cls.get_config_value('AGENT_MODE_ENABLED', cls.AGENT_MODE_ENABLED)
        if isinstance(value, str):
            return value.lower() == "true"
        return bool(value)
    
    @classmethod
    def get_agent_max_iterations(cls) -> int:
        """获取Agent最大迭代次数"""
        value = cls.get_config_value('AGENT_MAX_ITERATIONS', cls.AGENT_MAX_ITERATIONS)
        return int(value) if value is not None else cls.AGENT_MAX_ITERATIONS
    
    @classmethod
    def is_agent_handle_parsing_errors(cls) -> bool:
        """检查Agent是否处理解析错误"""
        value = cls.get_config_value('AGENT_HANDLE_PARSING_ERRORS', cls.AGENT_HANDLE_PARSING_ERRORS)
        if isinstance(value, str):
            return value.lower() == "true"
        return bool(value)
    
    @classmethod
    def is_agent_verbose(cls) -> bool:
        """检查Agent是否启用详细输出"""
        value = cls.get_config_value('AGENT_VERBOSE', cls.AGENT_VERBOSE)
        if isinstance(value, str):
            return value.lower() == "true"
        return bool(value)

class WinstarConfig(RuntimeConfigMixin):
    # 环境变量名映射 (与Config相同)
    _env_key_map = Config._env_key_map.copy()
    
    # 数据库配置 - 阿里云RDS MySQL (调试环境，使用正确的外网地址)
    
    # 数据库配置 - 阿里云RDS MySQL（使用正确的外网地址）
    #SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://wendao_manager:wendao_123@rm-bp1cbv056401an0hcso.mysql.rds.aliyuncs.com:3306/wendao_platform'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # 连接池预检查
        'pool_recycle': 3600,   # 连接回收时间
        'pool_timeout': 40,     # 连接超时
        'max_overflow': 0,      # 最大溢出连接数
        'pool_size': 20,        # 连接池大小
        'echo': False           # 不显示SQL语句（生产环境）
    }
      # JWT配置
    SECRET_KEY = 'your-very-secret-key-for-jwt-encoding'
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 令牌过期时间(秒)

    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 最大500MB
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://wendao:wendao@localhost:3306/wendao_platform'
    SILICON_API_BASE = "https://api.siliconflow.cn/v1"
    
    # Neo4j 配置
    NEO4J_URI = 'bolt://localhost:7687'
    NEO4J_USERNAME = 'neo4j'
    NEO4J_PASSWORD = 'neo4j'
    
    # 文件上传路径配置
    UPLOAD_BASE_PATH = '.'
    UPLOAD_IMAGE_FOLDER = 'temp_img'
    UPLOAD_VIDEO_FOLDER = 'temp_video'
    UPLOAD_DOCUMENT_FOLDER = 'temp_docs'
    UPLOAD_AVATAR_FOLDER = 'temp_avatars'
    UPLOAD_DEFAULT_FOLDER = 'temp_uploads'
    
    # Agent 配置
    AGENT_MODE_ENABLED = False
    AGENT_MAX_ITERATIONS = 5
    AGENT_HANDLE_PARSING_ERRORS = True
    AGENT_VERBOSE = True
    
    TENCENT_OCR_SECRET_ID = os.environ.get('TENCENT_OCR_SECRET_ID', '')
    TENCENT_OCR_SECRET_KEY = os.environ.get('TENCENT_OCR_SECRET_KEY', '')
    OCR_ENGINE='paddle'  # 可选值: 'cnocr', 'tencent', 'paddle'
    
    # PaddleOCR配置
    PADDLE_OCR_USE_GPU = False  # 是否使用GPU
    PADDLE_OCR_LANG = 'ch'      # 语言: 'ch'(中文), 'en'(英文), 'korean', 'japan'等
    PADDLE_OCR_USE_ANGLE_CLS = True  # 是否使用角度分类模型
    
    
    
    # 继承Config的所有方法
    get_openai_api_key = Config.get_openai_api_key
    get_silicon_api_base = Config.get_silicon_api_base
    get_neo4j_uri = Config.get_neo4j_uri
    get_neo4j_username = Config.get_neo4j_username
    get_neo4j_password = Config.get_neo4j_password
    get_upload_base_path = Config.get_upload_base_path
    get_upload_folder = Config.get_upload_folder
    is_agent_mode_enabled = Config.is_agent_mode_enabled
    get_agent_max_iterations = Config.get_agent_max_iterations
    is_agent_handle_parsing_errors = Config.is_agent_handle_parsing_errors
    is_agent_verbose = Config.is_agent_verbose
