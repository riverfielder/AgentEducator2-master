import os
from flask import Blueprint, request, jsonify
from models.models import Users, db
from schemas.user_vo import UserVO
from schemas.user_dto import UserLoginDTO, UserRegisterDTO, UserUpdateProfileDTO
from utils.result import Result
from utils.user_number_generator import generate_unique_user_number
from werkzeug.security import check_password_hash, generate_password_hash
from utils.auth import generate_token, token_required
from flask_cors import CORS, cross_origin  # 确保已安装 flask-cors

user_bp = Blueprint("user", __name__)
# @user_bp.route('/update-profile', methods=['POST'])
# @cross_origin(origins=["http://localhost:5173"], supports_credentials=True)
# @token_required
# def update_profile():
#     # TODO: Implement update profile logic
#     return jsonify(Result.error(501, "未实现"))

@user_bp.route('/login', methods=['POST'])
def teacher_login():
    try:
        # 获取请求 JSON 数据
        data = request.get_json()
        dto = UserLoginDTO(**data)

        # 从数据库中查找用户
        user = Users.query.filter_by(email=dto.email, is_deleted=False).first()

        if not user:
            return jsonify(Result.error(401, "邮箱或密码错误"))

        # 校验密码
        if not check_password_hash(user.password, dto.password):
            return jsonify(Result.error(401, "邮箱或密码错误"))

        # 生成JWT token
        token = generate_token(user.id, user.username, user.role)

        # 构建返回数据
        vo = UserVO(
            id=user.id, 
            name=user.username, 
            role=user.role, 
            token=token
        )

        return jsonify(Result.success(vo.dict()))

    except Exception as e:
        return jsonify(Result.error(400, f"参数错误: {str(e)}"))

@user_bp.route('/register', methods=['POST'])
def user_register():
    try:
        # 获取请求 JSON 数据
        data = request.get_json()
        dto = UserRegisterDTO(**data)  # 验证数据
        
        # 检查用户名是否已存在
        existing_user = Users.query.filter_by(username=dto.username, is_deleted=False).first()
        if existing_user:
            return jsonify(Result.error(400, "用户名已存在"))
            
        # 检查邮箱是否已存在
        existing_email = Users.query.filter_by(email=dto.email, is_deleted=False).first()
        if existing_email:
            return jsonify(Result.error(400, "邮箱已被注册"))
        
        # 创建新用户，使用用户选择的角色或默认角色
        hashed_password = generate_password_hash(dto.password)
        new_user = Users(
            username=dto.username,
            email=dto.email,
            password=hashed_password,
            role=dto.role,  # 使用用户选择的角色
            avatar=None  # 默认为空，使用首字母头像
        )
        
        # 先保存用户以获取UUID
        db.session.add(new_user)
        db.session.flush()  # 获取ID但不提交事务
        
        # 获取现有的用户编号以避免重复
        existing_numbers = {user.user_number for user in Users.query.filter(Users.user_number.isnot(None), Users.is_deleted == False).all()}
        
        # 生成唯一的用户编号
        new_user.user_number = generate_unique_user_number(str(new_user.id), dto.role, existing_numbers)
        
        # 提交事务
        db.session.commit()
        
        # 返回成功信息，包含用户信息
        vo = UserVO(id=new_user.id, name=new_user.username, role=new_user.role, token="fake-jwt-token")
        return jsonify(Result.success(vo.dict(), "注册成功"))
        
    except Exception as e:
        # 如果有错误，回滚事务
        db.session.rollback()
        return jsonify(Result.error(400, f"注册失败: {str(e)}"))

@user_bp.route('/user/info', methods=['GET'])
@token_required
def get_user_info():
    """获取当前登录用户信息"""
    try:
        # 从JWT获取用户ID
        user_id = request.user.get('user_id')
        if not user_id:
            return jsonify(Result.error(401, "未登录"))
        
        # 查询用户信息
        user = Users.query.filter_by(id=user_id, is_deleted=False).first()
        if not user:
            return jsonify(Result.error(404, "用户不存在"))
        
        # 构建返回数据
        user_info = {
            "id": user.id,
            "name": user.username,
            "email": user.email,
            "role": user.role,
            "user_number": user.user_number,
            "avatar": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{user.avatar}" or user.avatar or None
        }
        
        return jsonify(Result.success(user_info, "获取用户信息成功"))
        
    except Exception as e:
        return jsonify(Result.error(500, f"获取用户信息失败: {str(e)}"))

@user_bp.route('/change-password', methods=['POST'])
@token_required
def change_password():
    """修改用户密码"""
    try:
        # 从JWT获取用户ID
        user_id = request.user.get('user_id')
        if not user_id:
            return jsonify(Result.error(401, "未登录"))
        
        # 获取请求数据
        data = request.get_json()
        old_password = data.get('oldPassword')
        new_password = data.get('newPassword')
        
        if not all([old_password, new_password]):
            return jsonify(Result.error(400, "缺少必要参数"))
        
        # 验证密码长度
        if len(new_password) < 6:
            return jsonify(Result.error(400, "新密码长度不能少于6位"))
        
        # 查询用户
        user = Users.query.filter_by(id=user_id, is_deleted=False).first()
        if not user:
            return jsonify(Result.error(404, "用户不存在"))
        
        # 验证旧密码
        if not check_password_hash(user.password, old_password):
            return jsonify(Result.error(400, "当前密码不正确"))
        
        # 更新密码
        user.password = generate_password_hash(new_password)
        db.session.commit()
        
        return jsonify(Result.success(None, "密码修改成功"))
    
    except Exception as e:
        db.session.rollback()
        return jsonify(Result.error(500, f"修改密码失败: {str(e)}"))
    
@user_bp.route('/update-profile', methods=['POST'])
@token_required
def update_profile():
    # 处理 CORS 预检请求

    try:
        # 从JWT获取用户ID
        user_id = request.user.get('user_id')
        if not user_id:
            return jsonify(Result.error(401, "未登录"))
        # 获取请求数据并验证
        data = request.get_json()
        dto = UserUpdateProfileDTO(**data)
        # 查询用户
        user = Users.query.filter_by(id=user_id, is_deleted=False).first()
        if not user:
            return jsonify(Result.error(404, "用户不存在"))
        # 更新用户名
        if dto.username:
            existing_user = Users.query.filter(Users.username == dto.username, Users.id != user_id, Users.is_deleted == False).first()
            if existing_user:
                return jsonify(Result.error(400, "用户名已存在"))
            user.username = dto.username
        # 更新邮箱
        if dto.email:
            existing_email = Users.query.filter(Users.email == dto.email, Users.id != user_id, Users.is_deleted == False).first()
            if existing_email:
                return jsonify(Result.error(400, "邮箱已被注册"))
            user.email = dto.email
        # 更新头像
        if hasattr(dto, 'avatar') and dto.avatar:
            user.avatar = dto.avatar
        db.session.commit()
        # 返回更新后的用户信息
        user_info = {
            "id": user.id,
            "name": user.username,
            "email": user.email,
            "role": user.role,
            "user_number": user.user_number,
            "avatar": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{user.avatar}" or user.avatar or None
        }
        return jsonify(Result.success(user_info, "资料更新成功"))
    except Exception as e:
        db.session.rollback()
        return jsonify(Result.error(500, f"更新资料失败: {str(e)}"))

@user_bp.route('/user/<user_id>', methods=['GET'])
def get_user_by_id(user_id):
    """获取指定用户信息"""
    try:
        # 查询用户信息
        user = Users.query.filter_by(id=user_id, is_deleted=False).first()
        if not user:
            return jsonify(Result.error(404, "用户不存在"))
        
        # 构建返回数据
        user_info = {
            "id": user.id,
            "name": user.username,
            "email": user.email,
            "role": user.role,
            "user_number": user.user_number,
            "avatar": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{user.avatar}" or user.avatar or None
        }
        
        return jsonify(Result.success(user_info, "获取用户信息成功"))
        
    except Exception as e:
        return jsonify(Result.error(500, f"获取用户信息失败: {str(e)}"))

