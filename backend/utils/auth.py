import jwt
from functools import wraps
from flask import request, jsonify, current_app
from utils.result import Result
from models.models import Users
from config import Config
from datetime import datetime, timedelta
import uuid

# 从config读取SECRET_KEY
SECRET_KEY = Config.SECRET_KEY

# 创建正确类型的密钥对象
try:
    # 尝试创建JWK密钥
    from jwt.jwk import OctetJWK
    key = OctetJWK(SECRET_KEY.encode('utf-8'))
except (ImportError, AttributeError):
    # 如果上面的不可用，尝试使用简单字符串
    key = SECRET_KEY

def generate_token(user_id, username, role):
    """生成JWT token"""
    # 将UUID转换为字符串
    if isinstance(user_id, uuid.UUID):
        user_id = str(user_id)
    
    # 添加过期时间
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": int((datetime.utcnow() + timedelta(hours=24)).timestamp()),  # 24小时后过期
        "iat": int(datetime.utcnow().timestamp())  # 发行时间
    }
    
    try:
        # 尝试多种编码方式
        try:
            # 尝试使用jwt.JWT类
            JWT = jwt.JWT()
            return JWT.encode(payload, key, 'HS256')
        except (AttributeError, TypeError):
            # 如果jwt.JWT不可用，尝试直接使用jwt.encode
            return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    except Exception as e:
        # 记录错误信息便于调试
        print(f"JWT encode error: {str(e)}")
        # 尝试最基本的编码方法
        import json
        import base64
        import hmac
        import hashlib
        
        # 手动实现JWT编码
        header = {'alg': 'HS256', 'typ': 'JWT'}
        header_json = json.dumps(header, separators=(',', ':')).encode('utf-8')
        header_b64 = base64.urlsafe_b64encode(header_json).decode('utf-8').rstrip('=')
        
        payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        payload_b64 = base64.urlsafe_b64encode(payload_json).decode('utf-8').rstrip('=')
        
        to_sign = f"{header_b64}.{payload_b64}".encode('utf-8')
        signature = hmac.new(SECRET_KEY.encode('utf-8'), to_sign, hashlib.sha256).digest()
        signature_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
        
        return f"{header_b64}.{payload_b64}.{signature_b64}"

def verify_token():
    """验证JWT token并返回用户信息（支持Header和查询参数两种方式）"""
    token = None
    
    # 首先尝试从Authorization头获取token
    auth_header = request.headers.get("Authorization")
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
    
    # 如果Header中没有token，尝试从查询参数获取（用于预览等场景）
    if not token:
        token = request.args.get('token')
    
    if not token:
        return None
    
    try:
        # 尝试多种解码方式
        try:
            # 尝试使用jwt.JWT类
            JWT = jwt.JWT()
            payload = JWT.decode(token, key, ['HS256'])
        except (AttributeError, TypeError):
            # 如果jwt.JWT不可用，尝试直接使用jwt.decode
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            
        user_id = payload.get("user_id")
        
        # 验证用户是否存在
        user = Users.query.filter_by(id=user_id, is_deleted=False).first()
        if not user:
            return None
            
        return payload
    except Exception as e:
        # 捕获所有异常
        print(f"Token verification error: {str(e)}")
        return None

def token_required(f):
    """需要token的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        payload = verify_token()
        if not payload:
            return jsonify(Result.error(401, "未授权，请登录")), 401
        
        # 将用户信息添加到request对象
        request.user = payload
        # 为了兼容性，也设置current_user
        request.current_user = payload
        return f(*args, **kwargs)
    return decorated_function

    
    return decorated

def get_current_user_id():
    """从JWT token获取用户ID"""
    payload = verify_token()
    if payload:
        return payload.get("user_id")
    return None

def role_required(required_role):
    """需要特定角色的装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            payload = verify_token()
            if not payload:
                return jsonify(Result.error(401, "未授权，请登录")), 401
            
            user_role = payload.get("role")
            if user_role != required_role and user_role != 'admin':  # admin可以访问所有角色的功能
                return jsonify(Result.error(403, f"需要{required_role}权限")), 403
            
            # 将用户信息添加到request对象
            request.user = payload
            # 为了兼容性，也设置current_user
            request.current_user = payload
            return f(*args, **kwargs)
        
        return decorated
    return decorator

def is_teacher_or_admin(user_id):
    """
    检查用户是否为教师或管理员
    
    Args:
        user_id: 用户ID (str或UUID)
    
    Returns:
        bool: 如果用户是教师或管理员返回True，否则返回False
    """
    try:
        # 将UUID字符串转换为UUID对象
        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                return False
        
        # 查询用户
        user = Users.query.filter_by(id=user_id, is_deleted=False).first()
        
        # 检查用户是否存在且角色是teacher或admin
        if user and user.role in ['teacher', 'admin']:
            return True
            
        return False
    except Exception as e:
        current_app.logger.error(f"检查教师或管理员权限时出错: {str(e)}")
        return False
