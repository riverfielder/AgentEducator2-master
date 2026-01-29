import os
from flask import Blueprint, request, jsonify
from backend.models.models import Users
from backend.utils.result import Result
from models.user import User # type: ignore
from utils.jwt_util import generate_token # type: ignore
from utils.db_util import get_user_by_credentials # type: ignore

from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import User # type: ignore
from utils.jwt_util import generate_token, verify_token, token_required # type: ignore
from utils.db_util import db # type: ignore
from datetime import datetime
import uuid
from schemas.user_dto import UserLoginDTO, UserRegisterDTO, UserUpdateProfileDTO


auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'message': '用户名和密码不能为空'}), 400

        user = get_user_by_credentials(username, password)
        if not user:
            return jsonify({'message': '用户名或密码错误'}), 401

        # 如果验证通过，生成 JWT 令牌
        token = generate_token(str(user.id))  # 确保 UUID 转换为字符串

        return jsonify({
            'id': user.id,
            'name': user.name,
            'role': user.role,
            'token': token
        }), 200
    except Exception as e:
        return jsonify({'message': f'登录失败: {str(e)}'}), 500
    

    