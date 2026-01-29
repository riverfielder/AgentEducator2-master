from flask import Blueprint, request, jsonify, g
from models.models import db, Assignment, Question, Course, StudentAnswer, Users, Keyword, QuestionKeyword, CourseKeyword, StudentCourseEnrollment
from utils.auth import token_required,is_teacher_or_admin
from datetime import datetime, timedelta
from utils.result import Result
import uuid
from services.assignment_grading_service import AssignmentGradingService
from services.keyword_extraction_service import global_keyword_extraction_service
import json
from flask import current_app
from utils.question_processing_pool import question_processing_pool

# 创建蓝图
assignment_bp = Blueprint('assignment', __name__)

def parse_datetime_safe(datetime_str):
    """
    安全解析时间字符串，支持多种格式
    优先处理本地时间格式，避免时区转换问题
    """
    if not datetime_str:
        return None
    
    try:
        # 处理本地时间格式：YYYY-MM-DD HH:mm:ss
        if len(datetime_str) == 19 and ' ' in datetime_str:
            return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        
        # 处理ISO格式（兼容旧数据）
        if 'T' in datetime_str:
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        
        # 其他格式尝试
        return datetime.fromisoformat(datetime_str)
    except ValueError as e:
        print(f"时间解析失败: {datetime_str}, 错误: {e}")
        raise ValueError(f"无效的时间格式: {datetime_str}")

def _calculate_student_assignment_status(assignment, student_id):
    """
    计算学生作业的状态
    返回: 'uncompleted', 'submitted', 'expired'
    
    规则:
    1. 未完成: 学生未提交作业，且未过截止时间
    2. 已提交: 学生已提交作业，教师未完全批改，且未过截止时间  
    3. 已截止: 教师已完全批改 或 已过截止时间
    """
    from datetime import datetime
    
    # 检查学生是否有提交记录
    submitted_answers = StudentAnswer.query.filter_by(
        student_id=student_id,
        assignment_id=assignment.id
    ).all()
    
    # 获取作业总题目数
    total_questions = len(assignment.questions)
    
    # 判断是否已过截止时间
    current_time = datetime.now()
    is_overdue = current_time > assignment.due_date
    
    # 如果没有提交记录
    if not submitted_answers:
        return 'expired' if is_overdue else 'uncompleted'
    
    # 如果提交记录数量不完整
    if len(submitted_answers) < total_questions:
        return 'expired' if is_overdue else 'uncompleted'
    
    # 如果已过截止时间，直接返回已截止
    if is_overdue:
        return 'expired'
    
    # 检查是否所有题目都已批改（有分数）
    all_graded = all(answer.score is not None for answer in submitted_answers)
    
    if all_graded:
        return 'expired'  # 已完全批改，视为已截止
    else:
        return 'submitted'  # 已提交但未完全批改

def _calculate_teacher_assignment_status(assignment):
    """
    计算教师端作业的显示状态
    返回: 'draft', 'scheduled', 'published'
    
    规则:
    1. draft: 草稿状态
    2. scheduled: 已设置定时发布但还未到发布时间 
    3. published: 已发布（立即发布或定时发布已到时间）
    """
    from datetime import datetime
    
    # 如果是草稿状态
    if assignment.status == 'draft':
        return 'draft'
    
    # 如果是已发布状态，需要进一步判断是否是定时发布
    if assignment.status == 'published':
        # 如果没有设置发布时间，认为是立即发布
        if not assignment.publish_time:
            return 'published'
        
        # 如果有发布时间，比较当前时间和发布时间
        current_time = datetime.now()
        if current_time >= assignment.publish_time:
            return 'published'  # 已到发布时间
        else:
            return 'scheduled'  # 未到发布时间，显示为待发布
    
    return assignment.status  # 其他状态直接返回

def parse_datetime_safe(datetime_str):
    """
    安全解析时间字符串，支持多种格式
    优先处理本地时间格式，避免时区转换问题
    """
    if not datetime_str:
        return None
    
    try:
        # 处理本地时间格式：YYYY-MM-DD HH:mm:ss
        if len(datetime_str) == 19 and ' ' in datetime_str:
            return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        
        # 处理ISO格式（兼容旧数据）
        if 'T' in datetime_str:
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        
        # 其他格式尝试
        return datetime.fromisoformat(datetime_str)
    except ValueError as e:
        print(f"时间解析失败: {datetime_str}, 错误: {e}")
        raise ValueError(f"无效的时间格式: {datetime_str}")

@assignment_bp.route('/', methods=['GET'])
@token_required
def get_assignment_list():
    """获取作业列表"""
    try:
        # 获取查询参数 - 支持多种参数名格式
        course_id = request.args.get('courseId') or request.args.get('course_id')
        status = request.args.get('status')
        search = request.args.get('search')  # 添加搜索参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 10))
        
        # 构建基础查询
        query = Assignment.query.filter_by(is_deleted=False)
        
        # 应用过滤条件
        if course_id:
            try:
                course_uuid = uuid.UUID(course_id)
                query = query.filter_by(course_id=course_uuid)
            except ValueError:
                return jsonify(Result.error(400, "无效的课程ID")), 400
        
        # 添加搜索功能
        if search:
            query = query.filter(Assignment.title.ilike(f'%{search}%'))
            
        # 根据用户角色进行权限过滤
        user_id = getattr(request, "user", {}).get("user_id")
        if is_teacher_or_admin(user_id):
            # 教师和管理员：显示自己创建的作业
            query = query.filter_by(teacher_id=user_id)
        else:
            # 学生：只显示已发布且到发布时间的作业，且学生已选修该课程
            current_time = datetime.now()
            query = query.join(StudentCourseEnrollment,
                             Assignment.course_id == StudentCourseEnrollment.course_id).filter(
                Assignment.status == 'published',
                Assignment.publish_time <= current_time,  # 确保已到发布时间
                StudentCourseEnrollment.student_id == user_id
            )
            
        # 计算总数
        total = query.count()
        
        # 分页并按创建时间倒序排序
        assignments = query.order_by(Assignment.create_time.desc())\
            .offset((page - 1) * page_size)\
            .limit(page_size)\
            .all()
          # 转换为字典列表并添加状态信息
        assignments_list = []
        for assignment in assignments:
            assignment_dict = assignment.to_dict()
            
            # 添加课程和老师信息
            if assignment.course:
                assignment_dict['courseName'] = assignment.course.name
            if assignment.teacher:
                assignment_dict['teacherName'] = assignment.teacher.username
            
            # 根据用户类型添加相应的状态信息
            if is_teacher_or_admin(user_id):
                # 教师用户：添加教师端状态信息（包含定时发布状态）
                teacher_status = _calculate_teacher_assignment_status(assignment)
                assignment_dict['teacherStatus'] = teacher_status
                
                # 应用教师端状态筛选
                if status and status != 'all' and teacher_status != status:
                    continue  # 跳过不匹配的作业
            else:
                # 学生用户：添加学生特定的状态信息
                assignment_dict['studentStatus'] = _calculate_student_assignment_status(
                    assignment, user_id
                )
            
            assignments_list.append(assignment_dict)
        
        return jsonify({
            'code': 200,
            'message': '获取作业列表成功',
            'data': {
                'list': assignments_list,
                'total': total,
                'page': page,
                'pageSize': page_size
            }
        })
        
    except Exception as e:
        print(f"获取作业列表失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'获取作业列表失败: {str(e)}'
        }), 500

@assignment_bp.route('/<assignment_id>', methods=['GET'])
@token_required
def get_assignment_detail(assignment_id):
    """获取作业详情"""
    try:
        assignment = Assignment.query.get_or_404(assignment_id)
        
        # 检查权限
        user_id = getattr(request, "user", {}).get("user_id")
        if is_teacher_or_admin(user_id):
            # 教师和管理员：检查是否是作业创建者
            if assignment.teacher_id != uuid.UUID(user_id):
                return jsonify({
                    'code': 403,
                    'message': '无权访问此作业'
                }), 403
                
            # 为教师用户添加teacherStatus字段
            result_data = assignment.to_dict()
            result_data['teacherStatus'] = _calculate_teacher_assignment_status(assignment)
            
            # 添加课程和老师信息
            if assignment.course:
                result_data['courseName'] = assignment.course.name
            if assignment.teacher:
                result_data['teacherName'] = assignment.teacher.username
        else:
            # 学生：检查是否选修了该课程且作业已发布
            enrollment = StudentCourseEnrollment.query.filter_by(
                student_id=user_id,
                course_id=assignment.course_id
            ).first()
            
            if not enrollment:
                return jsonify({
                    'code': 403,
                    'message': '您未选修该课程，无权访问此作业'
                }), 403
            
            if assignment.status != 'published':
                return jsonify({
                    'code': 403,
                    'message': '作业尚未发布'
                }), 403
                
            # 检查是否已到发布时间
            current_time = datetime.now()
            if assignment.publish_time and assignment.publish_time > current_time:
                return jsonify({
                    'code': 403,
                    'message': '作业尚未发布'
                }), 403
                
            # 学生用户使用原始数据
            result_data = assignment.to_dict()
            
            # 添加课程和老师信息
            if assignment.course:
                result_data['courseName'] = assignment.course.name
            if assignment.teacher:
                result_data['teacherName'] = assignment.teacher.username
            
        return jsonify({
            'code': 200,
            'message': '获取作业详情成功',
            'data': result_data
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取作业详情失败: {str(e)}'
        }), 500

@assignment_bp.route('/draft', methods=['POST'])
@token_required
def create_draft():
    """创建作业草稿"""
    try:
        current_user_id = getattr(request, "user", {}).get("user_id")

        if not is_teacher_or_admin(current_user_id):
            print(f"权限检查失败 - 用户ID: {current_user_id} 不是教师或管理员")
            return jsonify(Result.error(403, "权限不足，只有教师和管理员可以创建作业"))

        data = request.get_json()
        print(f"接收到的数据: {data}")
        
       # 验证必要字段
        if not all(key in data for key in ['title', 'courseId', 'dueDate', 'questions']):
            return jsonify({
                'code': 400,
                'message': '缺少必要字段'
            }), 400
            
        # 获取课程ID，支持courseId和course_id两种格式
        course_id = data.get('courseId') or data.get('course_id')
        if not course_id:
            return jsonify({
                'code': 400,
                'message': '缺少课程ID'
            }), 400
            
        # 验证课程是否存在
        course_id = uuid.UUID(str(course_id))
        course = Course.query.get(course_id)
        if not course:
            print(f"课程不存在: {course_id}")
            return jsonify({
                'code': 404,
                'message': '课程不存在'
            }), 404
            
        # 创建作业
        try:
            assignment = Assignment(
                title=data['title'],
                course_id=course_id,
                teacher_id=uuid.UUID(current_user_id),
                due_date=parse_datetime_safe(data['dueDate']),
                status='draft'
            )
            print(f"作业基本信息创建成功: {assignment.title}")
            
            # 添加题目
            for index, q_data in enumerate(data['questions']):
                print(f"处理第{index + 1}个题目: {q_data}")
                
                # 判断是否是从题库导入的题目
                if q_data.get('id'):
                    # 从题库导入的题目，创建新的题目记录（复制题库中的题目信息）
                    question = Question(
                        assignment_id=assignment.id,
                        type=q_data['type'],
                        content=q_data['content'],
                        order_num=index,
                        max_score=float(q_data.get('maxScore', 5.0)),
                        options=json.dumps(q_data.get('options')),
                        answers=q_data.get('answers'),
                        reference=q_data.get('reference'),
                        explanation=q_data.get('explanation'),
                        course_id=str(course_id),  # 设置题目所属课程ID
                        # 保留题库中的其他字段
                        difficulty=q_data.get('difficulty'),
                        tags=q_data.get('tags'),
                        remark=q_data.get('remark'),
                        creator_id=q_data.get('creator_id'),
                        created_at=parse_datetime_safe(q_data.get('created_at')) if q_data.get('created_at') else datetime.now()
                    )
                else:
                    # 新建的题目，创建新的题目记录
                    question = Question(
                        assignment_id=assignment.id,
                        type=q_data['type'],
                        content=q_data['content'],
                        order_num=index,
                        max_score=float(q_data.get('maxScore', 5.0)),
                        options=json.dumps(q_data.get('options')),
                        answers=q_data.get('answers'),
                        reference=q_data.get('reference'),
                        explanation=q_data.get('explanation'),
                        course_id=str(course_id),  # 设置题目所属课程ID
                        # 为新建题目设置默认难度
                        difficulty=q_data.get('difficulty', 'medium'),
                        tags=q_data.get('tags'),
                        remark=q_data.get('remark'),
                        creator_id=current_user_id,
                        created_at=datetime.now()
                    )
                
                assignment.questions.append(question)
                
            db.session.add(assignment)
            db.session.commit()
            print(f"草稿创建成功 - ID: {assignment.id}")
            
            # 新增：为每个题目异步提取关键词
            app = current_app._get_current_object()
            for q in assignment.questions:
                question_processing_pool.submit_task(app, q.id, global_keyword_extraction_service.extract_keywords)
            
            return jsonify({
                'code': 200,
                'message': '创建草稿成功',
                'data': assignment.to_dict()
            })
            
        except Exception as e:
            print(f"创建作业对象时出错: {str(e)}")
            raise
            
    except Exception as e:
        db.session.rollback()
        print(f"创建草稿失败 - 错误: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'创建草稿失败: {str(e)}'
        }), 500

@assignment_bp.route('/', methods=['POST'])
@token_required
def publish_assignment():
    """发布作业"""
    try:
        current_user_id = getattr(request, "user", {}).get("user_id")
        if not is_teacher_or_admin(current_user_id):
            return jsonify(Result.error(403, "权限不足，只有教师和管理员可以发布作业"))

        data = request.get_json()
        
        # 验证必要字段
        if not all(key in data for key in ['title', 'courseId', 'dueDate', 'questions']):
            return jsonify({
                'code': 400,
                'message': '缺少必要字段'
            }), 400
            
        # 获取课程ID，支持courseId和course_id两种格式
        course_id = data.get('courseId') or data.get('course_id')
        if not course_id:
            return jsonify({
                'code': 400,
                'message': '缺少课程ID'
            }), 400
            
        # 验证课程是否存在
        course_id = uuid.UUID(str(course_id))
        course = Course.query.get(course_id)
        if not course:
            return jsonify({
                'code': 404,
                'message': '课程不存在'
            }), 404
            
        # 创建作业
        assignment = Assignment(
            id=uuid.uuid4(),  # 显式生成ID
            title=data['title'],
            course_id=course_id,
            teacher_id=uuid.UUID(current_user_id),
            due_date=parse_datetime_safe(data['dueDate']),
            publish_time=datetime.now() if not data.get('publishTime') else parse_datetime_safe(data['publishTime']),
            status='published'
        )
        
        # 添加题目
        for index, q_data in enumerate(data['questions']):
            # 判断是否是从题库导入的题目
            if q_data.get('id'):
                # 从题库导入的题目，创建新的题目记录（复制题库中的题目信息）
                question = Question(
                    assignment_id=assignment.id,
                    type=q_data['type'],
                    content=q_data['content'],
                    order_num=index,
                    max_score=float(q_data.get('maxScore', 5.0)),
                    options=json.dumps(q_data.get('options')),
                    answers=q_data.get('answers'),
                    reference=q_data.get('reference'),
                    explanation=q_data.get('explanation'),
                    course_id=str(course_id),  # 设置题目所属课程ID
                    # 保留题库中的其他字段
                    difficulty=q_data.get('difficulty'),
                    tags=q_data.get('tags'),
                    remark=q_data.get('remark'),
                    creator_id=q_data.get('creator_id'),
                    created_at=parse_datetime_safe(q_data.get('created_at')) if q_data.get('created_at') else datetime.now()
                )
            else:
                # 新建的题目，创建新的题目记录
                question = Question(
                    assignment_id=assignment.id,
                    type=q_data['type'],
                    content=q_data['content'],
                    order_num=index,
                    max_score=float(q_data.get('maxScore', 5.0)),
                    options=json.dumps(q_data.get('options')),
                    answers=q_data.get('answers'),
                    reference=q_data.get('reference'),
                    explanation=q_data.get('explanation'),
                    course_id=str(course_id),  # 设置题目所属课程ID
                    # 为新建题目设置默认难度
                    difficulty=q_data.get('difficulty', 'medium'),
                    tags=q_data.get('tags'),
                    remark=q_data.get('remark'),
                    creator_id=current_user_id,
                    created_at=datetime.now()
                )
            
            assignment.questions.append(question)
            
        db.session.add(assignment)
        db.session.commit()
        
        # 新增：为每个题目异步提取关键词
        app = current_app._get_current_object()
        for q in assignment.questions:
            question_processing_pool.submit_task(app, q.id, global_keyword_extraction_service.extract_keywords)
        
        return jsonify({
            'code': 200,
            'message': '发布作业成功',
            'data': assignment.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"发布作业失败: {str(e)}")  # 添加错误日志
        return jsonify({
            'code': 500,
            'message': f'发布作业失败: {str(e)}'
        }), 500

@assignment_bp.route('/<assignment_id>', methods=['PUT'])
@token_required
def update_assignment(assignment_id):
    """更新作业"""
    try:
        current_user_id = getattr(request, "user", {}).get("user_id")
        if not is_teacher_or_admin(current_user_id):
            return jsonify(Result.error(403, "权限不足，只有教师和管理员可以更新作业"))

        assignment = Assignment.query.get_or_404(assignment_id)
        
        # 检查权限
        if assignment.teacher_id != uuid.UUID(current_user_id):
            return jsonify({
                'code': 403,
                'message': '无权修改此作业'
            }), 403
            
        data = request.get_json()
        
        # 更新基本信息
        assignment.title = data.get('title', assignment.title)
        if 'dueDate' in data:
            assignment.due_date = parse_datetime_safe(data['dueDate'])
        if 'status' in data:
            assignment.status = data['status']
            if data['status'] == 'published' and not assignment.publish_time:
                assignment.publish_time = datetime.now()
                
        # 如果有题目更新，先删除旧题目
        if 'questions' in data:
            Question.query.filter_by(assignment_id=assignment_id).delete()
            
            # 添加新题目
            for index, q_data in enumerate(data['questions']):
                # 判断是否是从题库导入的题目
                if q_data.get('id'):
                    # 从题库导入的题目，创建新的题目记录（复制题库中的题目信息）
                    question = Question(
                        assignment_id=assignment.id,
                        type=q_data['type'],
                        content=q_data['content'],
                        order_num=index,
                        max_score=float(q_data.get('maxScore', 5.0)),
                        options=json.dumps(q_data.get('options')),
                        answers=q_data.get('answers'),
                        reference=q_data.get('reference'),
                        explanation=q_data.get('explanation'),
                        course_id=str(assignment.course_id),  # 设置题目所属课程ID
                        # 保留题库中的其他字段
                        difficulty=q_data.get('difficulty'),
                        tags=q_data.get('tags'),
                        remark=q_data.get('remark'),
                        creator_id=q_data.get('creator_id'),
                        created_at=parse_datetime_safe(q_data.get('created_at')) if q_data.get('created_at') else datetime.now()
                    )
                else:
                    # 新建的题目，创建新的题目记录
                    question = Question(
                        assignment_id=assignment.id,
                        type=q_data['type'],
                        content=q_data['content'],
                        order_num=index,
                        max_score=float(q_data.get('maxScore', 5.0)),
                        options=json.dumps(q_data.get('options')),
                        answers=q_data.get('answers'),
                        reference=q_data.get('reference'),
                        explanation=q_data.get('explanation'),
                        course_id=str(assignment.course_id),  # 设置题目所属课程ID
                        # 为新建题目设置默认难度
                        difficulty=q_data.get('difficulty', 'medium'),
                        tags=q_data.get('tags'),
                        remark=q_data.get('remark'),
                        creator_id=current_user_id,
                        created_at=datetime.now()
                    )
                
                assignment.questions.append(question)
                
        assignment.update_time = datetime.now()
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '更新作业成功',
            'data': assignment.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'更新作业失败: {str(e)}'
        }), 500

@assignment_bp.route('/<assignment_id>', methods=['DELETE'])
@token_required
def delete_assignment(assignment_id):
    """删除作业"""
    try:
        current_user_id = getattr(request, "user", {}).get("user_id")
        if not is_teacher_or_admin(current_user_id):
            return jsonify(Result.error(403, "权限不足，只有教师和管理员可以删除作业"))

        assignment = Assignment.query.get_or_404(assignment_id)
        
        # 软删除
        assignment.is_deleted = True
        assignment.update_time = datetime.now()
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '删除作业成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'删除作业失败: {str(e)}'
        }), 500
    
@assignment_bp.route('/student/submit', methods=['POST'])
@token_required
def submit_student_assignment():
    """学生提交作业"""
    try:
        data = request.get_json()
        student_id = request.user.get('user_id')
        
        # 验证必要字段
        if not all(key in data for key in ['assignment_id', 'questions_and_answers']):
            return jsonify({
                'code': 400,
                'message': '缺少必要字段'
            }), 400
            
        # 验证作业是否存在
        assignment = Assignment.query.get(data['assignment_id'])
        if not assignment:
            return jsonify({
                'code': 404,
            'message': '作业不存在'
        }), 404
        
        # 验证作业是否已发布
        if assignment.status != 'published':
            return jsonify({
                'code': 400,
                'message': '作业尚未发布，无法提交'
            }), 400
        
        # 验证学生是否有权限提交该作业（检查是否选修了该课程）
        enrollment = StudentCourseEnrollment.query.filter_by(
            student_id=student_id,
            course_id=assignment.course_id
        ).first()
        
        if not enrollment:
            return jsonify({
                'code': 403,
                'message': '您未选修该课程，无权提交此作业'
            }), 403
            
        # 检查作业是否已截止
        current_time = datetime.now()
        if current_time > assignment.due_date + timedelta(hours=8):
            return jsonify({
                'code': 400,
                'message': '作业已截止，无法提交'
            }), 400
            
        # 处理每个题目的答案
        answers = []
        for answer_data in data['questions_and_answers']:
            # 验证题目是否存在
            question = Question.query.get(answer_data['question_id'])
            if not question or question.assignment_id != assignment.id:
                return jsonify({
                    'code': 400,
                    'message': f'题目不存在或不属于该作业: {answer_data["question_id"]}'
                }), 400
                
            # 创建或更新答案
            student_answer = StudentAnswer.query.filter_by(
                student_id=student_id,
                assignment_id=data['assignment_id'],
                question_id=answer_data['question_id']
            ).first()
            
            if student_answer:
                # 更新已存在的答案
                student_answer.answer = answer_data['student_answer']
                student_answer.update_time = datetime.now()
            else:
                # 创建新答案
                student_answer = StudentAnswer(
                    student_id=student_id,                assignment_id=data['assignment_id'],
                    question_id=answer_data['question_id'],
                    answer=answer_data['student_answer']
                )
                db.session.add(student_answer)
                answers.append(student_answer)
            
        # 提交所有更改
        db.session.commit()
        
        # 自动批改选择题
        auto_graded_count = 0
        try:
            # 获取当前作业的所有选择题
            choice_questions = Question.query.filter(
                Question.assignment_id == assignment.id,
                Question.type.in_(['single', 'multiple'])
            ).all()
            
            for question in choice_questions:
                # 找到该题目对应的学生答案
                student_answer = next((ans for ans in answers if ans.question_id == question.id), None)
                if student_answer and student_answer.score is None:  # 只处理未批改的题目
                    # 解析题目选项
                    options = question.get_options()
                    
                    # 自动批改选择题
                    result = AssignmentGradingService.auto_grade_choice_question(
                        question_type=question.type,
                        options=options,
                        student_answer=student_answer.answer,
                        max_score=question.max_score
                    )
                      # 更新答题记录
                    student_answer.score = result['score']
                    student_answer.is_correct = result['is_correct']
                    student_answer.comment = result['comment']  # 保存批改评语
                    student_answer.update_time = datetime.now()
                    
                    auto_graded_count += 1
            
            # 提交批改结果
            db.session.commit()
            print(f"自动批改了 {auto_graded_count} 道选择题")
            
        except Exception as grading_error:
            print(f"自动批改选择题时发生错误: {str(grading_error)}")
            # 不影响作业提交，继续执行
        
        return jsonify({
            'code': 200,
            'message': '提交作业成功',
            'data': {
                'answers': [answer.to_dict() for answer in answers],
                'auto_graded_choices': auto_graded_count
            }
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"提交作业失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'提交作业失败: {str(e)}'
        }), 500

@assignment_bp.route('/<assignment_id>/auto-grade-choices', methods=['POST'])
@token_required
def auto_grade_assignment_choices(assignment_id):
    """自动批改作业中的所有选择题"""
    try:
        # 验证教师权限
        if not is_teacher_or_admin(request.user.get('user_id')):
            return jsonify({
                'code': 403,
                'message': '权限不足，只有教师和管理员可以进行批改'
            }), 403
        
        # 验证作业是否存在
        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            return jsonify({
                'code': 404,
                'message': '作业不存在'
            }), 404
        
        # 获取作业中的所有选择题
        choice_questions = Question.query.filter(
            Question.assignment_id == assignment_id,
            Question.type.in_(['single', 'multiple'])
        ).all()
        
        if not choice_questions:
            return jsonify({
                'code': 200,
                'message': '该作业没有选择题',
                'data': {'processed_count': 0}
            })
        
        # 获取所有学生的答题记录
        processed_count = 0
        total_students = 0
        
        for question in choice_questions:
            # 获取该题目的所有学生答案
            student_answers = StudentAnswer.query.filter_by(
                assignment_id=assignment_id,
                question_id=question.id            ).all()
            
            total_students = max(total_students, len(student_answers))
            
            for student_answer in student_answers:
                # 解析题目选项
                options = question.get_options()
                
                # 自动批改（支持重新批改已有分数的题目）
                result = AssignmentGradingService.auto_grade_choice_question(
                    question_type=question.type,
                    options=options,
                    student_answer=student_answer.answer,
                    max_score=question.max_score
                )
                
                # 更新答题记录
                student_answer.score = result['score']
                student_answer.is_correct = result['is_correct']
                student_answer.comment = result['comment']  # 更新批改评语
                student_answer.update_time = datetime.now()
                
                processed_count += 1
        
        # 提交数据库更改
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': f'自动批改完成，共处理了{processed_count}道选择题',
            'data': {
                'processed_count': processed_count,
                'choice_questions_count': len(choice_questions),
                'total_students': total_students
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'自动批改失败: {str(e)}'
        }), 500

@assignment_bp.route('/grade-choice-question', methods=['POST'])
@token_required
def grade_choice_question():
    """自动批改选择题"""
    try:
        data = request.get_json()
        question_type = data.get('question_type')  # 'single' 或 'multiple'
        options = data.get('options')  # 选项列表
        student_answer = data.get('student_answer')  # 学生答案
        max_score = data.get('max_score', 5)  # 满分
        
        if not all([question_type, options is not None]):
            return jsonify({
                'code': 400,
                'message': '缺少必要参数'
            }), 400
            
        if question_type not in ['single', 'multiple']:
            return jsonify({
                'code': 400,
                'message': '不支持的题目类型'
            }), 400
        
        result = AssignmentGradingService.auto_grade_choice_question(
            question_type=question_type,
            options=options,
            student_answer=student_answer,
            max_score=max_score
        )
        
        return jsonify({
            'code': 200,
            'message': '批改成功',
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'批改失败: {str(e)}'
        }), 500

@assignment_bp.route('/grade-fill-blank-question', methods=['POST'])
@token_required
def grade_fill_blank_question():
    """自动批改填空题"""
    try:
        data = request.get_json()
        print(f"收到填空题批改请求数据: {data}")
        
        question = data.get('question')  # 题目内容
        standard_answer = data.get('standard_answer')  # 标准答案
        student_answer = data.get('student_answer')  # 学生答案
        max_score = data.get('max_score', 5)  # 满分
        grading_criteria = data.get('grading_criteria')  # 评分标准
        question_id = data.get('question_id')  # 题目ID
        
        # 新增：支持通过 question_id 查询题目信息
        if question_id:
            from models.models import Question
            q = Question.query.get(question_id)
            if not q:
                print(f"未找到题目ID: {question_id}")
                return jsonify({'code': 404, 'message': '未找到对应题目'}), 404
            if not question:
                question = q.content
            if not standard_answer:
                # 填空题使用answers字段作为标准答案
                standard_answer = q.answers if q.type == 'blank' else q.reference
            if not max_score:
                max_score = q.max_score
            if not grading_criteria:
                grading_criteria = q.answers if q.type == 'blank' else q.reference
                
        print(f"处理后的参数 - 题目: {question}, 标准答案: {standard_answer}, 学生答案: {student_answer}")
        
        # 修改参数验证逻辑，允许student_answer为空字符串
        if not question or not standard_answer or student_answer is None:
            missing_params = []
            if not question: missing_params.append('question')
            if not standard_answer: missing_params.append('standard_answer')
            if student_answer is None: missing_params.append('student_answer')
            print(f"填空题批改缺少必要参数: {missing_params}")
            return jsonify({
                'code': 400,
                'message': f'缺少必要参数: {", ".join(missing_params)}'
            }), 400
            
        # 如果学生答案为空字符串，给出默认评分
        if not student_answer.strip():
            print("学生填空题答案为空，返回默认评分")
            return jsonify({
                'code': 200,
                'message': '填空题批改成功',
                'data': {
                    'score': 0,
                    'comment': '学生未作答',
                    'feedback': '该填空题学生未提供答案'
                }
            })
        
        print(f"调用填空题批改服务 - 题目: {question}, 标准答案: {standard_answer}, 学生答案: {student_answer}")
        
        result = AssignmentGradingService.auto_grade_fill_blank_question(
            question=question,
            standard_answer=standard_answer,
            student_answer=student_answer,
            max_score=max_score,
            grading_criteria=grading_criteria
        )
        
        print(f"填空题批改结果: {result}")
        
        return jsonify({
            'code': 200,
            'message': '填空题批改成功',
            'data': result
        })
        
    except Exception as e:
        print(f"填空题批改失败，错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'code': 500,
            'message': f'填空题批改失败: {str(e)}'
        }), 500

@assignment_bp.route('/grade-answer', methods=['POST'])
@token_required
def grade_answer():
    """自动批改单题答案"""
    try:
        data = request.get_json()
        print(f"收到批改请求数据: {data}")
        
        question = data.get('question')
        standard_answer = data.get('standard_answer')
        student_answer = data.get('student_answer')
        score_full = data.get('score_full', 5)
        grading_criteria = data.get('grading_criteria')
        question_id = data.get('question_id')
        
        # 新增：支持通过 question_id 查询题目信息
        if question_id:
            from models.models import Question
            q = Question.query.get(question_id)
            if not q:
                print(f"未找到题目ID: {question_id}")
                return jsonify({'code': 404, 'message': '未找到对应题目'}), 404
            if not question:
                question = q.content
            if not standard_answer:
                # 根据题型选择正确的标准答案字段：填空题用answers，简答题用reference
                standard_answer = q.answers if q.type == 'blank' else q.reference
            if not score_full:
                score_full = q.max_score
            if not grading_criteria:
                grading_criteria = q.answers if q.type == 'blank' else q.reference
                
        print(f"处理后的参数 - 题目: {question}, 标准答案: {standard_answer}, 学生答案: {student_answer}")
        
        # 修改参数验证逻辑，允许student_answer为空字符串
        if not question or not standard_answer or student_answer is None:
            missing_params = []
            if not question: missing_params.append('question')
            if not standard_answer: missing_params.append('standard_answer')
            if student_answer is None: missing_params.append('student_answer')
            print(f"缺少必要参数: {missing_params}")
            return jsonify({
                'code': 400,
                'message': f'缺少必要参数: {", ".join(missing_params)}'
            }), 400
            
        # 如果学生答案为空字符串，给出默认评分
        if not student_answer.strip():
            print("学生答案为空，返回默认评分")
            return jsonify({
                'code': 200,
                'message': '批改成功',
                'data': {
                    'score': 0,
                    'comment': '学生未作答',
                    'feedback': '该题目学生未提供答案'
                }
            })
            
        result = AssignmentGradingService.grade_answer(
            question=question,
            standard_answer=standard_answer,
            student_answer=student_answer,
            score_full=score_full,
            grading_criteria=grading_criteria
        )
        print(f"批改结果: {result}")
        
        return jsonify({
            'code': 200,
            'message': '批改成功',
            'data': result
        })
    except Exception as e:
        print(f"批改失败，错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'code': 500,
            'message': f'批改失败: {str(e)}'
        }), 500

@assignment_bp.route('/<assignment_id>/submissions', methods=['GET'])
@token_required
def get_student_submissions(assignment_id):
    """获取学生作业提交列表"""
    try:
        # 验证教师权限
        if not is_teacher_or_admin(request.user.get('user_id')):
            return jsonify({
                'code': 403,
                'message': '权限不足，只有教师和管理员可以查看提交列表'
            }), 403
            
        # 验证作业是否存在
        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            return jsonify({
                'code': 404,
                'message': '作业不存在'
            }), 404
            
        # 获取所有学生的提交情况，包括答题详情
        submissions = db.session.query(
            StudentAnswer.student_id,
            Users.username,
            db.func.count(StudentAnswer.id).label('answered_count'),
            db.func.sum(StudentAnswer.score).label('total_score')
        ).join(
            Users, StudentAnswer.student_id == Users.id
        ).filter(
            StudentAnswer.assignment_id == assignment_id
        ).group_by(
            StudentAnswer.student_id,
            Users.username
        ).all()
        
        # 获取作业的总题目数
        total_questions = len(assignment.questions)
        
        # 构建返回数据
        submission_list = []
        for sub in submissions:
            # 获取该学生的所有答题记录，去重处理
            student_answers = db.session.query(StudentAnswer).join(
                Question, StudentAnswer.question_id == Question.id
            ).filter(
                StudentAnswer.student_id == sub.student_id,
                StudentAnswer.assignment_id == assignment_id
            ).order_by(
                Question.order_num,
                StudentAnswer.update_time.desc()  # 按更新时间倒序，取最新的记录
            ).all()
            
            # 去重：每个题目只保留最新的一条记录
            unique_answers = {}
            for answer in student_answers:
                question_id = str(answer.question_id)
                if question_id not in unique_answers:
                    unique_answers[question_id] = answer
            
            # 构建答题详情
            questions_and_answers = []
            for answer in unique_answers.values():
                question = answer.question
                answer_data = {
                    'question_id': str(question.id),
                    'question_type': question.type,
                    'question_content': question.content,
                    'options': question.options,
                    'student_answer': answer.answer,
                    'score': answer.score,
                    'max_score': question.max_score,
                    'is_correct': answer.is_correct,
                    'comment': answer.comment or ''
                }
                questions_and_answers.append(answer_data)
            
            # 按题目顺序排序
            questions_and_answers.sort(key=lambda x: next(
                (q.order_num for q in assignment.questions if str(q.id) == x['question_id']), 0
            ))
            
            submission_data = {
                'student_id': str(sub.student_id),
                'student_name': sub.username,
                'answered_count': sub.answered_count,
                'total_questions': total_questions,
                'completion_rate': sub.answered_count / total_questions if total_questions > 0 else 0,
                'total_score': float(sub.total_score) if sub.total_score else 0,
                'questions_and_answers': questions_and_answers
            }
            submission_list.append(submission_data)
            
        return jsonify({
            'code': 200,
            'message': '获取提交列表成功',
            'data': {
                'submissions': submission_list,
                'total_students': len(submission_list)
            }
        })
        
    except Exception as e:
        print(f"获取提交列表失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'提交作业失败: {str(e)}'
        }), 500 
    
@assignment_bp.route('/<assignment_id>/marking/submit', methods=['POST'])
@token_required
def submit_marking(assignment_id):
    """提交批改进度"""
    try:
        data = request.get_json()
        student_id = request.user.get('user_id')
        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            return jsonify({
                'code': 404,
                'message': '作业不存在'
            }), 404
        if not is_teacher_or_admin(request.user.get('user_id')):
            return jsonify({
                'code': 403,
                'message': '权限不足，只有教师和管理员可以提交批改'
            }), 403
        scores = data.get('scores')
        for score in scores:
            student_answer = StudentAnswer.query.filter_by(
                student_id=score['student_id'],
                assignment_id=assignment_id,
                question_id=score['question_id']
            ).first()
            if student_answer:
                student_answer.score = score['score']
                student_answer.is_correct = score['is_correct']
                student_answer.update_time = datetime.now()
                student_answer.comment = score['comment']
        db.session.commit()
        return jsonify({
            'code': 200,
            'message': '批改成功'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'提交批改失败: {str(e)}'
        }), 500 

@assignment_bp.route('/<assignment_id>/marking', methods=['GET'])
@token_required
def get_marking_info(assignment_id):
    """获取作业批改信息"""
    try:
        print(f"正在获取作业批改信息 - 作业ID: {assignment_id}")
        student_id = request.user.get('user_id')
        print(f"当前学生ID: {student_id}")
        
        # 验证作业ID格式
        try:
            assignment_uuid = uuid.UUID(assignment_id)
        except ValueError:
            print(f"无效的作业ID格式: {assignment_id}")
            return jsonify({
                'code': 400,
                'message': '无效的作业ID格式'
            }), 400
        
        # 查找作业
        assignment = Assignment.query.get(assignment_uuid)
        if not assignment:
            print(f"作业不存在: {assignment_id}")
            return jsonify({
                'code': 404,
                'message': '作业不存在'
            }), 404
            
        # 检查作业是否已发布
        if assignment.status != 'published':
            print(f"作业未发布: {assignment_id}")
            return jsonify({
                'code': 400,
                'message': '作业未发布'
            }), 400
        
        # 验证学生是否有权限访问该作业（检查是否选修了该课程）
        enrollment = StudentCourseEnrollment.query.filter_by(
            student_id=student_id,
            course_id=assignment.course_id
        ).first()
        
        if not enrollment:
            print(f"学生未选修该课程 - 学生ID: {student_id}, 课程ID: {assignment.course_id}")
            return jsonify({
                'code': 403,
                'message': '您未选修该课程，无权访问此作业'
            }), 403

        # 获取学生在这个作业的所有答题记录
        student_answers = StudentAnswer.query.join(
            Question, StudentAnswer.question_id == Question.id
        ).filter(
            StudentAnswer.student_id == student_id,
            StudentAnswer.assignment_id == assignment_uuid
        ).order_by(
            Question.order_num
        ).all()
        
        print(f"找到 {len(student_answers)} 条答题记录")

        # 如果没有找到答题记录
        if not student_answers:
            print(f"未找到学生答题记录 - 学生ID: {student_id}, 作业ID: {assignment_id}")
            return jsonify({
                'code': 404,
                'message': '未找到答题记录'
            }), 404        # 构建答题详情
        questions_and_answers = []
        total_score = 0
        max_total_score = 0
        
        for answer in student_answers:
            question = answer.question
            answer_data = {
                'question_id': str(question.id),
                'question_type': question.type,
                'question_content': question.content,
                'student_answer': answer.answer,
                'score': answer.score,
                'max_score': question.max_score,
                'is_correct': answer.is_correct,
                'comment': answer.comment,  # 教师评语
                'reference_answer': question.reference,  # 参考答案
                'explanation': question.explanation,  # 解析
                'options': question.get_options() if question.type in ['single', 'multiple'] else None  # 选择题选项
            }
            questions_and_answers.append(answer_data)
            
            # 计算总分
            if answer.score is not None:
                total_score += answer.score
            max_total_score += question.max_score
        
        response_data = {
            'code': 200,
            'message': '获取批改信息成功',
            'data': {
                'assignment_title': assignment.title,
                'course_name': assignment.course.name if assignment.course else '未知课程',
                'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
                'total_score': total_score,
                'max_total_score': max_total_score,
                'questions_and_answers': questions_and_answers,
                'status': 'marked' if len(questions_and_answers) > 0 and all(q['score'] is not None for q in questions_and_answers) else 'unmarked'
            }
        }
        print(f"成功获取批改信息 - 学生ID: {student_id}, 作业ID: {assignment_uuid}")
        return jsonify(response_data)

    except Exception as e:
        print(f"获取批改信息失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'获取批改信息失败: {str(e)}'
        }), 500 
    


        # 查询当前已有关联的 QuestionKeyword 数据
        question_keywords = QuestionKeyword.query.filter_by(question_id=question_id).all()
        qk_list = [qk.to_dict() for qk in question_keywords] if question_keywords else []
        return jsonify(Result.success({"result": result, "question_keywords": qk_list}, "关键词提取已完成"))
    except Exception as e:
        return jsonify(Result.error(500, f"关键词提取任务提交失败: {str(e)}"))


        question = Question.query.get(qid)
        if not question:
            print(f"[DEBUG] 题目不存在: {qid}")
            return jsonify(Result.error(404, "题目不存在"))
        question_keywords = QuestionKeyword.query.filter_by(question_id=qid).all()
        if not question_keywords:
            return jsonify(Result.error(404, "该题目还没有提取到关键词"))
        keyword_ids = [qk.keyword_id for qk in question_keywords]
        keywords = Keyword.query.filter(Keyword.id.in_(keyword_ids)).all() if keyword_ids else []
        course_ids = set()
        for kw in keywords:
            for course_kw in getattr(kw, 'course_keywords', []):
                course_ids.add(course_kw.course_id)
        related_keywords = set()
        for course_id in course_ids:
            course_keywords = CourseKeyword.query.filter_by(course_id=course_id).all()
            for ck in course_keywords:
                related_keywords.add(ck.keyword_id)
        result = {
            "question_id": str(question_id),
            "question_content": question.content,
            "extracted_keywords": [kw.name for kw in keywords],
            "related_courses": list(map(str, course_ids)),
            "related_keywords": list(map(str, related_keywords)),
            "question_keywords": [qk.to_dict() for qk in question_keywords]
        }
        return jsonify(Result.success(result, "查询成功"))
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify(Result.error(500, f"查询失败: {str(e)}"))
    
@assignment_bp.route('/question/<question_id>/extract-keywords/result', methods=['GET'])
@token_required
def get_question_extracted_keywords(question_id):
    """获取题目已提取的知识点"""
    try:
        question = Question.query.get(question_id)
        if not question:
            return jsonify(Result.error(404, "题目不存在")), 404
        question_keywords = QuestionKeyword.query.filter_by(question_id=question_id).all()
        if not question_keywords:
            return jsonify(Result.error(404, "该题目还没有提取到关键词")), 404
        keyword_ids = [qk.keyword_id for qk in question_keywords]
        keywords = Keyword.query.filter(Keyword.id.in_(keyword_ids)).all() if keyword_ids else []
        course_ids = set()
        for kw in keywords:
            for course_kw in getattr(kw, 'course_keywords', []):
                course_ids.add(course_kw.course_id)
        related_keywords = set()
        for course_id in course_ids:
            course_keywords = CourseKeyword.query.filter_by(course_id=course_id).all()
            for ck in course_keywords:
                related_keywords.add(ck.keyword_id)
        result = {
            "question_id": str(question_id),
            "question_content": question.content,
            "extracted_keywords": [kw.name for kw in keywords],
            "related_courses": list(map(str, course_ids)),
            "related_keywords": list(map(str, related_keywords)),
            "question_keywords": [qk.to_dict() for qk in question_keywords]
        }
        return jsonify(Result.success(result, "查询成功"))
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify(Result.error(500, f"查询失败: {str(e)}")), 500
    