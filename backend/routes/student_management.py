from flask import Blueprint, request, jsonify, current_app, send_file
from models.models import db, Users, Course, StudentCourseEnrollment
from utils.result import Result
from utils.auth import token_required, is_teacher_or_admin
from werkzeug.security import generate_password_hash
import uuid
import csv
import io
import pandas as pd
import os
import tempfile

# 创建学生管理蓝图
student_management_bp = Blueprint("student_management", __name__)

@student_management_bp.route('/list', methods=['GET'])
@token_required
def list_students():
    """
    获取学生列表
    可选参数: page, size, keyword(搜索关键字), class(班级)
    """
    try:
        # 检查权限 (仅教师和管理员可访问)
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
            
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)
        keyword = request.args.get('keyword', '')
        class_name = request.args.get('class', '')
        course_id = request.args.get('courseId', '')  # 新增：按课程ID筛选
        sort = request.args.get('sort', 'username')
        direction = request.args.get('direction', 'asc')
        
        # 处理sort参数，如果是'name'则映射到'username'
        if sort == 'name':
            sort = 'username'
        
        # 获取当前用户信息（用于查询教师的课程）
        current_user = Users.query.filter_by(id=uuid.UUID(user_id), is_deleted=False).first()
        
        # 构建基础查询
        if course_id and course_id != 'all':
            # 如果指定了课程筛选，查询选修了该课程的学生
            query = db.session.query(Users).join(
                StudentCourseEnrollment, Users.id == StudentCourseEnrollment.student_id
            ).filter(
                Users.role == 'student',
                Users.is_deleted == False,
                StudentCourseEnrollment.course_id == uuid.UUID(course_id)
            )
            
            # 如果是教师，还要确保课程是该教师的
            if current_user.role == 'teacher':
                query = query.join(Course, StudentCourseEnrollment.course_id == Course.id).filter(
                    Course.teacher_id == current_user.id,
                    Course.is_deleted == False
                )
        else:
            # 没有课程筛选，查询所有学生
            query = Users.query.filter_by(role='student', is_deleted=False)
        
        # 添加搜索条件
        if keyword:
            query = query.filter(
                (Users.username.contains(keyword)) |
                (Users.email.contains(keyword)) |
                (Users.class_name.contains(keyword))
            )
        
        # 添加班级筛选
        if class_name and class_name != 'all':
            query = query.filter(Users.class_name == class_name)
        
        # 添加排序
        if direction == 'desc':
            query = query.order_by(getattr(Users, sort).desc())
        else:
            query = query.order_by(getattr(Users, sort).asc())
        
        # 计算总数
        total = query.count()
        
        # 分页查询
        students = query.paginate(page=page, per_page=size, error_out=False)
        
        # 构建响应数据
        student_list = []
        for student in students.items:
            # 查询该学生在当前教师课程中的选课情况
            teacher_courses = []
            if current_user.role == 'teacher':
                # 如果是教师，查询学生选了该教师的哪些课程
                enrollments = db.session.query(StudentCourseEnrollment, Course).join(
                    Course, StudentCourseEnrollment.course_id == Course.id
                ).filter(
                    StudentCourseEnrollment.student_id == student.id,
                    Course.teacher_id == current_user.id,
                    Course.is_deleted == False
                ).all()
                
                for enrollment, course in enrollments:
                    teacher_courses.append({
                        "id": str(course.id),
                        "name": course.name,
                        "code": course.code
                    })
            elif current_user.role == 'admin':
                # 如果是管理员，显示学生的所有课程
                enrollments = db.session.query(StudentCourseEnrollment, Course).join(
                    Course, StudentCourseEnrollment.course_id == Course.id
                ).filter(
                    StudentCourseEnrollment.student_id == student.id,
                    Course.is_deleted == False
                ).all()
                
                for enrollment, course in enrollments:
                    teacher_courses.append({
                        "id": str(course.id),
                        "name": course.name,
                        "code": course.code
                    })
            
            student_list.append({
                "id": str(student.id),
                "username": student.username,
                "name": student.username,  # 假设名称与用户名相同，实际应返回姓名
                "user_number": student.user_number,  # 新增学号字段
                "email": student.email,
                "class": student.class_name,
                "status": student.status or "active",
                "avatar": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{student.avatar}" or student.avatar or "/temp_img/avatar_1.jpg",
                "create_time": student.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                "teacherCourses": teacher_courses  # 新增：学生在当前教师的课程列表
            })
        
        return jsonify(Result.success({
            "list": student_list,
            "total": total,
            "page": page,
            "size": size
        }, "获取学生列表成功"))
        
    except Exception as e:
        import traceback
        current_app.logger.error(f"获取学生列表错误: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(500, f"获取学生列表失败: {str(e)}"))

@student_management_bp.route('/<student_id>', methods=['GET'])
@token_required
def get_student_details(student_id):
    """获取学生详情"""
    try:
        # 检查权限 (仅教师和管理员可访问)
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
            
        # 查找学生
        student = Users.query.filter_by(id=uuid.UUID(student_id), is_deleted=False).first()
        
        # 检查学生是否存在
        if not student:
            return jsonify(Result.error(404, "学生不存在"))
            
        # 检查是否为学生角色
        if student.role != 'student':
            return jsonify(Result.error(400, "指定用户不是学生"))
            
        # 构建响应数据
        student_info = {
            "id": str(student.id),
            "username": student.username,
            "name": student.username,  # 假设名称与用户名相同，实际应返回姓名
            "email": student.email,
            "class": student.class_name,
            "status": student.status or "active",
            "avatar": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{student.avatar}" or student.avatar or "/temp_img/avatar_1.jpg",
            "create_time": student.create_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify(Result.success(student_info, "获取学生详情成功"))
        
    except Exception as e:
        import traceback
        current_app.logger.error(f"获取学生详情错误: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(500, f"获取学生详情失败: {str(e)}"))

@student_management_bp.route('/add', methods=['POST'])
@token_required
def add_student():
    """添加单个学生并关联课程"""
    try:
        # 检查权限 (仅教师和管理员可访问)
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
            
        # 获取请求数据
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['username', 'email', 'courseId']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify(Result.error(400, f"缺少必要字段: {field}"))
        
        email = data['email'].strip().lower()
        name = data['username'].strip()  # 这里的username实际上是name
        course_id = uuid.UUID(data['courseId'])
        
        # 验证邮箱格式
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify(Result.error(400, "邮箱格式不正确"))
        
        # 验证课程是否存在
        course = Course.query.get(course_id)
        if not course or course.is_deleted:
            return jsonify(Result.error(400, "指定的课程不存在"))
        
        # 查找或创建学生用户
        existing_user = Users.query.filter_by(email=email, role='student', is_deleted=False).first()
        
        if existing_user:
            # 用户已存在，检查是否已选过该课程
            existing_enrollment = StudentCourseEnrollment.query.filter_by(
                student_id=existing_user.id, 
                course_id=course_id
            ).first()
            
            if existing_enrollment:
                return jsonify(Result.error(400, f"学生已选过课程 {course.name}"))
            
            student_user = existing_user
            is_new_student = False
        else:
            # 确保用户名唯一
            counter = 1
            username = name
            while Users.query.filter_by(username=username, is_deleted=False).first():
                username = f"{name}_{counter}"
                counter += 1
            
            # 创建新学生
            student_user = Users(
                id=uuid.uuid4(),
                username=username,  # 使用可能添加了计数器的用户名
                user_number=data.get('user_number', ''),
                password=generate_password_hash('123456'),  # 默认密码
                email=email,
                role='student',
                status=data.get('status', 'active'),
                avatar=data.get('avatar', None)
            )
            
            db.session.add(student_user)
            is_new_student = True
        
        # 创建选课关系
        enrollment = StudentCourseEnrollment(
            id=uuid.uuid4(),
            student_id=student_user.id,
            course_id=course_id
        )
        
        db.session.add(enrollment)
        
        # 更新课程学生数量
        course.student_count += 1
        
        # 提交更改
        db.session.commit()
        
        # 构建响应数据
        student_info = {
            "id": str(student_user.id),
            "username": student_user.username,
            "user_number": student_user.user_number,
            "email": student_user.email,
            "course": course.name,
            "courseId": str(course.id),
            "status": student_user.status,
            "isNewStudent": is_new_student
        }
        
        return jsonify(Result.success(student_info, "学生添加并选课成功"))
        
    except Exception as e:
        # 如果有错误，回滚事务
        db.session.rollback()
        import traceback
        current_app.logger.error(f"添加学生错误: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(500, f"添加学生失败: {str(e)}"))

@student_management_bp.route('/<student_id>', methods=['PUT'])
@token_required
def update_student(student_id):
    """更新学生信息"""
    try:
        # 检查权限 (仅教师和管理员可访问)
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
            
        # 查找学生
        student = Users.query.filter_by(id=uuid.UUID(student_id), is_deleted=False).first()
        
        # 检查学生是否存在
        if not student:
            return jsonify(Result.error(404, "学生不存在"))
            
        # 检查是否为学生角色
        if student.role != 'student':
            return jsonify(Result.error(400, "指定用户不是学生"))
            
        # 获取请求数据
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['username', 'email', 'user_number', 'status']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify(Result.error(400, f"缺少必要字段: {field}"))
        
        # 检查邮箱是否已被其他用户使用
        if data['email'] != student.email:
            existing_email = Users.query.filter_by(email=data['email'], is_deleted=False).first()
            if existing_email and str(existing_email.id) != student_id:
                return jsonify(Result.error(400, "邮箱已被其他用户注册"))
        
        # 检查学号是否已被其他用户使用
        if data['user_number'] != student.user_number:
            existing_user_number = Users.query.filter_by(user_number=data['user_number'], is_deleted=False).first()
            if existing_user_number and str(existing_user_number.id) != student_id:
                return jsonify(Result.error(400, "学号已被其他用户使用"))
        
        # 更新学生信息
        student.username = data['username']
        student.email = data['email']
        student.user_number = data['user_number']
        student.status = data['status']
        
        # 如果提供了密码，更新密码
        if 'password' in data and data['password']:
            student.password = generate_password_hash(data['password'])
        
        # 提交更改
        db.session.commit()
        
        # 构建响应数据
        student_info = {
            "id": str(student.id),
            "username": student.username,
            "name": student.username,
            "user_number": student.user_number,
            "email": student.email,
            "class": student.class_name,
            "status": student.status,
            "avatar": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{student.avatar}" or student.avatar or "/temp_img/avatar_1.jpg",
            "create_time": student.create_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify(Result.success(student_info, "学生信息更新成功"))
        
    except Exception as e:
        # 如果有错误，回滚事务
        db.session.rollback()
        import traceback
        current_app.logger.error(f"更新学生信息错误: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(500, f"更新学生信息失败: {str(e)}"))

@student_management_bp.route('/<student_id>', methods=['DELETE'])
@token_required
def delete_student(student_id):
    """删除学生（软删除）"""
    try:
        # 检查权限 (仅教师和管理员可访问)
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
            
        # 查找学生
        student = Users.query.filter_by(id=uuid.UUID(student_id), is_deleted=False).first()
        
        # 检查学生是否存在
        if not student:
            return jsonify(Result.error(404, "学生不存在"))
            
        # 检查是否为学生角色
        if student.role != 'student':
            return jsonify(Result.error(400, "指定用户不是学生"))
            
        # 软删除学生
        student.is_deleted = True
        
        # 提交更改
        db.session.commit()
        
        return jsonify(Result.success(None, "学生删除成功"))
        
    except Exception as e:
        # 如果有错误，回滚事务
        db.session.rollback()
        import traceback
        current_app.logger.error(f"删除学生错误: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(500, f"删除学生失败: {str(e)}"))

@student_management_bp.route('/<student_id>/courses', methods=['GET'])
@token_required
def get_student_courses(student_id):
    """获取学生课程列表"""
    try:
        # 检查权限 (仅教师和管理员可访问，或学生自己访问自己的数据)
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id) and str(user_id) != student_id:
            return jsonify(Result.error(403, "无权操作"))
            
        # 查找学生
        student = Users.query.filter_by(id=uuid.UUID(student_id), is_deleted=False).first()
        
        # 检查学生是否存在
        if not student:
            return jsonify(Result.error(404, "学生不存在"))
            
        # 检查是否为学生角色
        if student.role != 'student':
            return jsonify(Result.error(400, "指定用户不是学生"))
            
        # 获取学生选修的课程
        enrollments = StudentCourseEnrollment.query.filter_by(student_id=student.id).all()
        course_ids = [enrollment.course_id for enrollment in enrollments]
        
        # 查询课程详情
        courses = Course.query.filter(Course.id.in_(course_ids), Course.is_deleted==False).all()
        
        # 构建响应数据
        course_list = []
        for course in courses:
            # 获取教师信息
            teacher_info = {"id": "0", "name": "未分配"}
            if course.teacher:
                teacher_info = {"id": course.teacher.id, "name": course.teacher.username,"avatar":course.teacher.avatar}
                
            course_list.append({
                "id": str(course.id),
                "name": course.name,
                "code": course.code,
                "description": course.description or "",
                "imageUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{course.image_url}" or course.image_url or "",
                "startDate": course.start_date if course.start_date else 0,
                "endDate": course.end_date if course.end_date else 0,
                "hours": course.hours,
                "semester": course.semester,
                "teacherInfo": teacher_info
            })
        
        return jsonify(Result.success(course_list, "获取学生课程成功"))
        
    except Exception as e:
        import traceback
        current_app.logger.error(f"获取学生课程错误: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(500, f"获取学生课程失败: {str(e)}"))

@student_management_bp.route('/<student_id>/assign-courses', methods=['POST'])
@token_required
def assign_student_courses(student_id):
    """为学生分配课程"""
    try:
        # 检查权限 (仅教师和管理员可访问)
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
            
        # 查找学生
        student = Users.query.filter_by(id=uuid.UUID(student_id), is_deleted=False).first()
        
        # 检查学生是否存在
        if not student:
            return jsonify(Result.error(404, "学生不存在"))
            
        # 检查是否为学生角色
        if student.role != 'student':
            return jsonify(Result.error(400, "指定用户不是学生"))
            
        # 获取请求数据
        data = request.get_json()
        course_ids = data.get('courseIds', [])
        
        # 验证课程ID列表
        if not isinstance(course_ids, list):
            return jsonify(Result.error(400, "课程ID必须是数组"))
            
        # 删除现有的选课记录
        StudentCourseEnrollment.query.filter_by(student_id=student.id).delete()
        
        # 添加新的选课记录
        for course_id in course_ids:
            # 检查课程是否存在
            course = Course.query.get(uuid.UUID(course_id))
            if course and not course.is_deleted:
                enrollment = StudentCourseEnrollment(
                    id=uuid.uuid4(),
                    student_id=student.id,
                    course_id=course.id
                )
                db.session.add(enrollment)
                
                # 更新课程的学生数量
                course.student_count = StudentCourseEnrollment.query.filter_by(course_id=course.id).count()
        
        # 提交更改
        db.session.commit()
        
        return jsonify(Result.success(None, "课程分配成功"))
        
    except Exception as e:
        # 如果有错误，回滚事务
        db.session.rollback()
        import traceback
        current_app.logger.error(f"分配课程错误: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(500, f"分配课程失败: {str(e)}"))

@student_management_bp.route('/classes', methods=['GET'])
@token_required
def get_class_list():
    """获取班级列表"""
    try:
        # 检查权限 (仅教师和管理员可访问)
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
            
        # 查询所有学生的班级
        classes = db.session.query(Users.class_name).filter_by(role='student').filter(Users.class_name != None).distinct().all()
        
        # 提取班级名称
        class_list = [cls[0] for cls in classes if cls[0]]
        
        return jsonify(Result.success(class_list, "获取班级列表成功"))
        
    except Exception as e:
        import traceback
        current_app.logger.error(f"获取班级列表错误: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(500, f"获取班级列表失败: {str(e)}"))

@student_management_bp.route('/upload', methods=['POST'])
@token_required
def upload_student_list():
    """上传学生名单文件(Excel/CSV)进行预览"""
    try:
        # 检查权限 (仅教师和管理员可访问)
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
        
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify(Result.error(400, "未上传文件"))
            
        file = request.files['file']
        
        # 检查文件是否为空
        if file.filename == '':
            return jsonify(Result.error(400, "文件为空"))
            
        # 检查文件类型
        filename = file.filename.lower()
        if not any(filename.endswith(ext) for ext in ['.xlsx', '.xls', '.csv']):
            return jsonify(Result.error(400, "仅支持.xlsx、.xls、.csv格式"))
        
        # 解析文件
        valid_students = []
        invalid_records = []
        try:
            if filename.endswith('.csv'):
                # 处理CSV文件
                # 尝试不同的编码方式
                encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312', 'gb18030']
                decoded_content = None
                used_encoding = None
                
                # 保存文件内容
                file_content = file.read()
                
                for encoding in encodings:
                    try:
                        decoded_content = file_content.decode(encoding)
                        used_encoding = encoding
                        break
                    except UnicodeDecodeError:
                        continue
                
                if decoded_content is None:
                    return jsonify(Result.error(400, "无法解析文件编码，请确保文件使用UTF-8、GBK、GB2312或GB18030编码"))
                
                # 将解码后的内容写入StringIO对象
                stream = io.StringIO(decoded_content)
                csv_data = list(csv.reader(stream))
                
                # 第一行应该是表头
                headers = [h.strip().lower() for h in csv_data[0]]
                
                # 必要的字段
                required_fields = ['name', 'email', 'course', 'user_number']
                for field in required_fields:
                    if field not in headers:
                        return jsonify(Result.error(400, f"CSV文件缺少必要字段: {field}"))
                
                # 处理每一行数据
                for i, row in enumerate(csv_data[1:], 1):
                    try:
                        if len(row) < len(headers):
                            invalid_records.append({"row": i+1, "reason": "数据不完整"})
                            continue
                            
                        student_data = dict(zip(headers, row))
                        
                        # 验证必要字段
                        if not all(student_data.get(field) for field in required_fields):
                            invalid_records.append({"row": i+1, "reason": "缺少必要字段"})
                            continue
                        
                        # 验证邮箱格式
                        import re
                        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                        if not re.match(email_pattern, student_data['email']):
                            invalid_records.append({"row": i+1, "reason": f"邮箱格式不正确: {student_data['email']}"})
                            continue
                        
                        # 检查课程是否存在
                        course = Course.query.filter(
                            (Course.code == student_data['course']) | 
                            (Course.name == student_data['course'])
                        ).filter_by(is_deleted=False).first()
                        
                        if not course:
                            invalid_records.append({"row": i+1, "reason": f"课程不存在: {student_data['course']}"})
                            continue
                        
                        # 检查是否已经选过该课程（如果用户存在）
                        existing_user = Users.query.filter_by(email=student_data['email'], role='student', is_deleted=False).first()
                        if existing_user:
                            existing_enrollment = StudentCourseEnrollment.query.filter_by(
                                student_id=existing_user.id, 
                                course_id=course.id
                            ).first()
                            if existing_enrollment:
                                invalid_records.append({"row": i+1, "reason": f"学生已选过课程 {course.name}"})
                                continue
                            
                        # 添加到有效学生列表
                        valid_students.append({
                            "name": student_data['name'].strip(),
                            "email": student_data['email'].strip().lower(),
                            "user_number": student_data['user_number'].strip(),
                            "course": student_data['course'].strip(),
                            "courseId": str(course.id),
                            "courseName": course.name
                        })
                    except Exception as row_error:
                        invalid_records.append({"row": i+1, "reason": str(row_error)})
            else:
                # 处理Excel文件
                df = pd.read_excel(file)
                
                # 检查必要列是否存在
                required_cols = ['name', 'email', 'course']
                for col in required_cols:
                    if col not in df.columns:
                        return jsonify(Result.error(400, f"Excel文件缺少必要列: {col}"))
                
                # 处理每一行数据
                for i, row in df.iterrows():
                    try:
                        # 验证必要字段
                        if any(pd.isna(row[col]) for col in required_cols):
                            invalid_records.append({"row": i+2, "reason": "缺少必要字段"})
                            continue
                        
                        # 验证邮箱格式
                        import re
                        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                        email = str(row['email']).strip().lower()
                        if not re.match(email_pattern, email):
                            invalid_records.append({"row": i+2, "reason": f"邮箱格式不正确: {email}"})
                            continue
                        
                        # 检查课程是否存在
                        course_id_or_course_name = str(row['course']).strip()
                        course = Course.query.filter(
                            (Course.code == course_id_or_course_name) | 
                            (Course.name == course_id_or_course_name)
                        ).filter_by(is_deleted=False).first()
                        
                        if not course:
                            invalid_records.append({"row": i+2, "reason": f"课程不存在: {course_id_or_course_name}"})
                            continue
                        
                        # 检查是否已经选过该课程（如果用户存在）
                        existing_user = Users.query.filter_by(email=email, role='student', is_deleted=False).first()
                        if existing_user:
                            existing_enrollment = StudentCourseEnrollment.query.filter_by(
                                student_id=existing_user.id, 
                                course_id=course.id
                            ).first()
                            if existing_enrollment:
                                invalid_records.append({"row": i+2, "reason": f"学生已选过课程 {course.name}"})
                                continue
                            
                        # 添加到有效学生列表
                        valid_students.append({
                            "name": str(row['name']).strip(),
                            "email": email,
                            "course": course_id_or_course_name,
                            "courseId": str(course.id),
                            "courseName": course.name
                        })
                    except Exception as row_error:
                        invalid_records.append({"row": i+2, "reason": str(row_error)})
                        
            return jsonify(Result.success({
                "validStudents": valid_students,
                "invalidRecords": invalid_records
            }, "文件解析成功"))
            
        except Exception as parse_error:
            import traceback
            current_app.logger.error(f"文件解析错误: {str(parse_error)}\n{traceback.format_exc()}")
            return jsonify(Result.error(400, f"文件解析失败: {str(parse_error)}"))
            
    except Exception as e:
        import traceback
        current_app.logger.error(f"上传学生名单错误: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(500, f"上传学生名单失败: {str(e)}"))

@student_management_bp.route('/import', methods=['POST'])
@token_required
def import_students():
    """批量导入学生并关联课程"""
    try:
        # 检查权限 (仅教师和管理员可访问)
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
            
        # 获取请求数据
        data = request.get_json()
        students = data.get('students', [])
        
        # 验证学生数据
        if not isinstance(students, list) or len(students) == 0:
            return jsonify(Result.error(400, "学生数据无效"))
        
        # 导入计数
        success_count = 0
        new_student_count = 0
        enrollment_count = 0
        error_messages = []
        
        # 批量导入学生并创建选课关系
        for student_data in students:
            try:
                # 检查必要字段
                if not all(student_data.get(key) for key in ['name', 'email', 'courseId', 'user_number']):
                    error_messages.append(f"学生 {student_data.get('name', '未知')} 数据不完整")
                    continue
                
                email = student_data['email'].strip().lower()
                name = student_data['name'].strip()
                course_id = uuid.UUID(student_data['courseId'])
                user_number = student_data['user_number'].strip()
                
                # 验证课程是否存在
                course = Course.query.get(course_id)
                if not course or course.is_deleted:
                    error_messages.append(f"课程不存在: {student_data.get('courseName', course_id)}")
                    continue
                
                # 查找或创建学生用户
                existing_user = Users.query.filter_by(email=email, role='student', is_deleted=False).first()
                
                if existing_user:
                    # 用户已存在，直接创建选课关系
                    student_user = existing_user
                else:
                    # 确保用户名唯一
                    counter = 1
                    username = name
                    while Users.query.filter_by(username=username, is_deleted=False).first():
                        username = f"{name}_{counter}"
                        counter += 1
                    
                    # 创建新学生
                    student_user = Users(
                        id=uuid.uuid4(),
                        username=username,
                        user_number=user_number,
                        password=generate_password_hash('123456'),  # 默认密码
                        email=email,
                        role='student',
                        status=data.get('status', 'active'),
                        avatar=data.get('avatar', None)
                    )
                    
                    db.session.add(student_user)
                    new_student_count += 1
                
                # 检查是否已经选过该课程
                existing_enrollment = StudentCourseEnrollment.query.filter_by(
                    student_id=student_user.id, 
                    course_id=course_id
                ).first()
                
                if existing_enrollment:
                    error_messages.append(f"学生 {name} 已选过课程 {course.name}")
                    continue
                
                # 创建选课关系
                enrollment = StudentCourseEnrollment(
                    id=uuid.uuid4(),
                    student_id=student_user.id,
                    course_id=course_id
                )
                
                db.session.add(enrollment)
                
                # 更新课程学生数量
                course.student_count += 1
                
                enrollment_count += 1
                success_count += 1
                
            except Exception as student_error:
                error_message = f"导入学生 {student_data.get('name', '未知')} 错误: {str(student_error)}"
                current_app.logger.error(error_message)
                error_messages.append(error_message)
                continue
        
        # 提交更改
        db.session.commit()
        
        result_message = f"成功导入 {success_count} 条记录"
        if new_student_count > 0:
            result_message += f"，其中新创建学生 {new_student_count} 个"
        if enrollment_count > 0:
            result_message += f"，创建选课关系 {enrollment_count} 个"
        
        response_data = {
            "successCount": success_count,
            "newStudentCount": new_student_count,
            "enrollmentCount": enrollment_count,
            "errorMessages": error_messages
        }
        
        return jsonify(Result.success(response_data, result_message))
        
    except Exception as e:
        # 如果有错误，回滚事务
        db.session.rollback()
        import traceback
        current_app.logger.error(f"批量导入学生错误: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(500, f"批量导入学生失败: {str(e)}"))

@student_management_bp.route('/<student_id>/reset-password', methods=['POST'])
@token_required
def reset_student_password(student_id):
    """重置学生密码"""
    try:
        # 检查权限 (仅教师和管理员可访问)
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
            
        # 查找学生
        student = Users.query.filter_by(id=uuid.UUID(student_id), is_deleted=False).first()
        
        # 检查学生是否存在
        if not student:
            return jsonify(Result.error(404, "学生不存在"))
            
        # 检查是否为学生角色
        if student.role != 'student':
            return jsonify(Result.error(400, "指定用户不是学生"))
            
        # 重置密码为默认密码
        student.password = generate_password_hash('123456')
        
        # 提交更改
        db.session.commit()
        
        return jsonify(Result.success(None, "密码已重置为: 123456"))
        
    except Exception as e:
        # 如果有错误，回滚事务
        db.session.rollback()
        import traceback
        current_app.logger.error(f"重置密码错误: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(500, f"重置密码失败: {str(e)}"))

@student_management_bp.route('/template', methods=['GET'])
@token_required
def download_student_template():
    """下载学生导入模板"""
    try:
        # 检查权限 (仅教师和管理员可访问)
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
            
        # 创建临时CSV文件
        fd, path = tempfile.mkstemp(suffix='.csv')
        try:
            with os.fdopen(fd, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                # 写入表头 - 修改为新格式
                writer.writerow(['name', 'email', 'course'])
                # 写入示例数据 - 使用实际的课程代码
                writer.writerow(['张三', 'zhangsan@example.com', 'PY101'])
                writer.writerow(['李四', 'lisi@example.com', 'CS-B201'])
                writer.writerow(['王五', 'wangwu@example.com', 'NetworkApp'])
            
            # 返回文件下载响应
            return send_file(
                path,
                as_attachment=True,
                download_name='学生导入模板.csv',
                mimetype='text/csv'
            )
        finally:
            # 确保临时文件被删除
            try:
                os.unlink(path)
            except Exception as e:
                current_app.logger.error(f"删除临时文件错误: {str(e)}")
                
    except Exception as e:
        import traceback
        current_app.logger.error(f"下载学生模板错误: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(500, f"下载学生模板失败: {str(e)}"))

@student_management_bp.route('/available-courses', methods=['GET'])
@token_required
def get_available_courses():
    """获取可选择的课程列表"""
    try:
        # 检查权限 (仅教师和管理员可访问)
        user_id = request.user.get('user_id')
        current_app.logger.info(f"获取课程列表 - 用户ID: {user_id}")
        
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
            
        # 获取当前用户信息
        current_user = Users.query.filter_by(id=uuid.UUID(user_id), is_deleted=False).first()
        if not current_user:
            return jsonify(Result.error(404, "用户不存在"))
        
        current_app.logger.info(f"当前用户 - ID: {current_user.id}, 角色: {current_user.role}, 用户名: {current_user.username}")
        
        # 构建查询条件
        query = Course.query.filter_by(is_deleted=False)
        
        # 如果是教师，只显示自己的课程
        if current_user.role == 'teacher':
            query = query.filter_by(teacher_id=current_user.id)
            current_app.logger.info(f"教师用户，筛选teacher_id = {current_user.id}的课程")
        
        # 获取课程列表
        courses = query.order_by(Course.name.asc()).all()
        current_app.logger.info(f"查询到 {len(courses)} 门课程")
        
        # 打印课程详细信息
        for course in courses:
            current_app.logger.info(f"课程: {course.id} - {course.name} - teacher_id: {course.teacher_id}")
        
        # 构建响应数据
        course_list = []
        for course in courses:
            course_list.append({
                "id": str(course.id),
                "code": course.code,
                "name": course.name,
                "description": course.description,
                "studentCount": course.student_count,
                "semester": course.semester
            })
        
        current_app.logger.info(f"返回 {len(course_list)} 门课程给前端")
        return jsonify(Result.success(course_list, "获取课程列表成功"))
        
    except Exception as e:
        import traceback
        current_app.logger.error(f"获取课程列表错误: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(500, f"获取课程列表失败: {str(e)}"))