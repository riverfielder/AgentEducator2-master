from flask import Blueprint, request, jsonify, g, current_app
from models.models import Question, Assignment, db, QuestionKeyword, Keyword, Course, QuestionKeyword
import jwt
from datetime import datetime
from functools import wraps
from tasks.document_processor.markitdown_processor import MarkitdownProcessor
from utils.auth import token_required
import tempfile
import os
import re
from services.llm_service import llm_service
import json
import uuid
from flask import abort
from utils.result import Result
#from config.config import SECRET_KEY

bp = Blueprint('question_bank', __name__, url_prefix='/api/question_bank')

def get_or_create_question_bank_assignment(course_id, teacher_id):
    """获取或创建题库作业"""
    assignment = Assignment.query.filter_by(title='题库题目', course_id=course_id, teacher_id=teacher_id).first()
    if not assignment:
        # 创建新的题库作业
        assignment = Assignment(
            id=uuid.uuid4(),
            title='题库题目',
            course_id=course_id,
            teacher_id=teacher_id,
            due_date=datetime(2099, 12, 31),  # 设置一个很远的截止日期
            status='draft',
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        db.session.add(assignment)
        db.session.commit()
    return assignment

@bp.route('/', methods=['GET'])
@token_required
def list_questions():
    course_id = request.args.get('course_id')
    user_id = request.user.get('user_id')
    
    # 查询所有题库题目（全平台）
    assignments = Assignment.query.filter_by(title='题库题目').all()
    assignment_ids = [a.id for a in assignments]
    
    # 构建查询
    query = Question.query.filter(Question.assignment_id.in_(assignment_ids))
    
    # 如果指定了课程ID，则筛选该课程的题目
    if course_id:
        query = query.filter_by(course_id=course_id)
    
    questions = query.order_by(Question.create_time.desc()).all()
    
    # 构建结果，添加权限信息和课程名称
    result = []
    for q in questions:
        q_dict = q.to_dict()
        
        # 添加是否可编辑的标识（只有题目所属课程的教师可以编辑）
        can_edit = False
        if q.course_id:
            course = Course.query.filter_by(id=q.course_id, is_deleted=False).first()
            if course and str(course.teacher_id) == str(user_id):
                can_edit = True
        
        q_dict['can_edit'] = can_edit
        
        # 添加课程名称信息
        if q.course_id:
            course = Course.query.filter_by(id=q.course_id, is_deleted=False).first()
            q_dict['course_name'] = course.name if course else '未知课程'
        else:
            q_dict['course_name'] = '无课程'
        
        # 添加关联知识点的完整信息（包含id、name、category）
        question_keywords = QuestionKeyword.query.filter_by(question_id=q.id).all()
        extracted_keywords = []
        for qk in question_keywords:
            if qk.keyword:
                extracted_keywords.append({
                    'id': qk.keyword.id,
                    'name': qk.keyword.name,
                    'category': qk.keyword.category
                })
        q_dict['extractedKeywords'] = extracted_keywords
            
        result.append(q_dict)
    
    return jsonify(result)

@bp.route('/', methods=['POST'])
@token_required
def add_question():
    data = request.json
    user_id = request.user.get('user_id')
    # 校验 course_id
    raw_course_id = data.get('course_id') or data.get('course_id')
    try:
        course_id = str(uuid.UUID(raw_course_id))
    except Exception:
        return jsonify({'msg': 'course_id 非法，必须为合法 UUID'}), 400
    
    # 验证课程是否存在且属于当前教师
    course = Course.query.filter_by(id=course_id, teacher_id=user_id, is_deleted=False).first()
    if not course:
        return jsonify({'msg': '课程不存在或无权限访问'}), 403
    
    assignment = get_or_create_question_bank_assignment(course_id, user_id)
    # 校验题干
    if not data.get('content'):
        return jsonify({'msg': '题干内容不能为空'}), 400
    # 校验题型
    if not data.get('question_type'):
        return jsonify({'msg': '题型不能为空'}), 400
    # 校验选项（单选/多选）
    if data['question_type'] in ['single', 'multiple'] and (not data.get('options') or not isinstance(data['options'], list) or len(data['options']) == 0):
        return jsonify({'msg': '选项不能为空'}), 400
    # 校验答案
    if data['question_type'] in ['single', 'multiple'] and not data.get('answer'):
        return jsonify({'msg': '请选择正确答案'}), 400
    if data['question_type'] == 'blank' and not data.get('answer'):
        return jsonify({'msg': '填空题答案不能为空'}), 400
    if data['question_type'] == 'essay' and not data.get('answer'):
        return jsonify({'msg': '问答题参考答案不能为空'}), 400

    # 转换字段映射
    question_type_map = {
        'single': 'single',
        'multiple': 'multiple',
        'blank': 'blank',
        'essay': 'essay'
    }

    # 处理答案字段
    if data['question_type'] in ['single', 'multiple']:
        answers = None
        reference = None
        if isinstance(data['answer'], list):
            if len(data['answer']) == 1:
                answers = data['answer'][0]
            else:
                answers = ','.join(data['answer'])
        else:
            answers = str(data['answer'])
    else:
        answers = None
        reference = str(data['answer'])

    q = Question(
        id=uuid.uuid4(),
        assignment_id=assignment.id,
        type=question_type_map.get(data['question_type'], 'single'),
        content=data['content'],
        options=json.dumps(data.get('options', [])) if data.get('options') else None,
        answers=answers,
        reference=reference,
        explanation=data.get('explanation'),
        order_num=0,
        max_score=5.0,
        keywords=None,
        create_time=datetime.now(),
        update_time=datetime.now(),
        course_id=course_id,
        difficulty=data.get('difficulty'),
        tags=None,  # tags字段不再直接用
        remark=data.get('remark'),
        creator_id=user_id,
        created_at=datetime.now()
    )
    db.session.add(q)
    db.session.commit()  # 先提交以确保问题存在
    # 处理知识点关联
    keyword_ids = data.get('keyword_ids', [])
    for kid in keyword_ids:
        if kid:
            db.session.add(QuestionKeyword(question_id=q.id, keyword_id=kid))
    db.session.commit()  # 提交知识点关联
    # 新增：自动提取并关联关键词
    from services.keyword_extraction_service import global_keyword_extraction_service
    from flask import current_app
    app = current_app._get_current_object()
    try:
        global_keyword_extraction_service.extract_keywords(app, q.id)
    except Exception as e:
        print(f"[自动关键词提取失败] 题目ID: {q.id}, 错误: {e}")
    return jsonify({'msg': '题目添加成功', 'id': str(q.id)})

@bp.route('/<question_id>', methods=['DELETE'])
@token_required
def delete_question(question_id):
    try:
        user_id = request.user.get('user_id')
        q = Question.query.get_or_404(question_id)
        
        # 验证题目所属课程是否属于当前教师
        if q.course_id:
            course = Course.query.filter_by(id=q.course_id, teacher_id=user_id, is_deleted=False).first()
            if not course:
                return jsonify({'msg': '无权限删除该题目，只能删除自己课程的题目'}), 403
        else:
            # 如果题目没有关联课程，也不允许删除（安全考虑）
            return jsonify({'msg': '无权限删除该题目'}), 403
        
        # 先删除关联的知识点记录
        QuestionKeyword.query.filter_by(question_id=question_id).delete()
        # 再删除题目
        db.session.delete(q)
        db.session.commit()
        return jsonify({'msg': '题目已删除'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': f'删除题目失败: {str(e)}'}), 500

@bp.route('/<question_id>', methods=['PUT'])
@token_required
def update_question(question_id):
    user_id = request.user.get('user_id')
    q = Question.query.get_or_404(question_id)
    
    # 验证题目所属课程是否属于当前教师
    if q.course_id:
        course = Course.query.filter_by(id=q.course_id, teacher_id=user_id, is_deleted=False).first()
        if not course:
            return jsonify({'msg': '无权限修改该题目，只能修改自己课程的题目'}), 403
    else:
        # 如果题目没有关联课程，也不允许修改（安全考虑）
        return jsonify({'msg': '无权限修改该题目'}), 403
    
    data = request.json
    
    # 转换字段映射
    question_type_map = {
        'single': 'single',
        'multiple': 'multiple',
        'blank': 'blank',
        'essay': 'essay'
    }
    
    # 处理答案字段
    if data.get('question_type') in ['single', 'multiple']:
        answers = None
        reference = None
        if isinstance(data.get('answer'), list):
            if len(data['answer']) == 1:
                answers = data['answer'][0]
            else:
                answers = ','.join(data['answer'])
        else:
            answers = str(data.get('answer', ''))
    else:
        answers = None
        reference = str(data.get('answer', ''))
    
    q.content = data.get('content', q.content)
    q.type = question_type_map.get(data.get('question_type', q.type), q.type)
    q.options = json.dumps(data.get('options', [])) if data.get('options') else None
    q.answers = answers
    q.reference = reference
    q.explanation = data.get('explanation', q.explanation)
    q.course_id = data.get('course_id', q.course_id)
    q.difficulty = data.get('difficulty', q.difficulty)
    q.tags = None  # tags字段不再直接用
    q.remark = data.get('remark', q.remark)
    q.update_time = datetime.now()
    db.session.flush()
    # 处理知识点关联：先删后加
    db.session.query(QuestionKeyword).filter_by(question_id=q.id).delete()
    keyword_ids = data.get('keyword_ids', [])
    for kid in keyword_ids:
        if kid:
            db.session.add(QuestionKeyword(question_id=q.id, keyword_id=kid))
    db.session.commit()
    return jsonify({'msg': '题目已更新'})

@bp.route('/import', methods=['POST'])
@token_required
def import_questions():
    # file = request.files['file']
    # TODO: 调用AI分析word/pdf并入库
    return jsonify({'msg': '批量导入接口预留，待实现AI分析'})

@bp.route('/import/preview', methods=['POST'])
@token_required
def import_preview():
    file = request.files.get('file')
    number_format = request.form.get('number_format', '3.')
    if not file:
        return jsonify({'msg': '未上传文件'}), 400
    # 保存临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[-1]) as tmp:
        file.save(tmp)
        tmp_path = tmp.name
    try:
        # 1. 转markdown
        processor = MarkitdownProcessor()
        md_result = processor.converter.convert(tmp_path)
        # 兼容新版markitdown返回类型
        if hasattr(md_result, 'markdown'):
            markdown = md_result.markdown
        elif isinstance(md_result, dict) and 'markdown' in md_result:
            markdown = md_result['markdown']
        elif isinstance(md_result, str):
            markdown = md_result
        else:
            return jsonify({'msg': '文档转换失败，未能获取markdown内容'}), 500
        print('==== markdown ====')
        print(repr(markdown))
        # AI分割题目 - 使用统一的LLM配置
        from services.unified_llm_service import create_langchain_llm
        llm = create_langchain_llm("question_import", streaming=False)
        system_prompt = """
你是一个专业的教育题库AI助手。请将用户上传的试题文档内容（markdown格式）分割为结构化题目数组。

**重要说明**：如果原文档中的题目已经包含答案（如"具有风险分析的软件生命周期模型是（ C ）"这种在题干中已标注答案的形式，或者文档末尾有"答案：C"这种形式），你需要：
1. **清理题干中的答案标注**：将"（ C ）"、"（A）"、"（ B ）"等形式替换为空白的"（     ）"或"（          ）"
2. 将检测到的答案保存在answer字段中  
3. 在response_notes字段中说明"检测到原文档包含答案，已自动提取并清理题干"

**清理规则示例**：
- "具有风险分析的软件生命周期模型是（ C ）。" → "具有风险分析的软件生命周期模型是（     ）。"
- "软件工程的基本要素包括方法、工具和（ A ）。" → "软件工程的基本要素包括方法、工具和（          ）。"
- "下列说法正确的是（B）" → "下列说法正确的是（     ）"

支持以下四种题型：
- 单选题（single）：有且仅有一个正确答案，options为**不带**A、B、C、D等前缀的选项数组。
- 多选题（multiple）：有多个正确答案，options为**不带**A、B、C、D等前缀的选项数组。
- 填空题（blank）：无选项，options为[]，answer为标准答案。
- 问答题（essay）：无选项，options为[]，answer为参考答案。

每道题请输出如下JSON结构，且自动为每道题添加题号字段number（从1递增），并智能判断题目难度（difficulty: easy/medium/hard）：

// 单选题示例（原文档有答案的情况）
{
  "number": 1,
  "content": "具有风险分析的软件生命周期模型是（     ）。",  // 已清理答案标注，保留括号但清空内容
  "options": ["瀑布模型", "喷泉模型", "螺旋模型", "增量模型"],
  "answer": "C",  // 从原文档提取的答案
  "question_type": "single",
  "difficulty": "easy",
  "response_notes": "检测到原文档包含答案，已自动提取并清理题干"
}

// 单选题示例（原文档无答案的情况）  
{
  "number": 2,
  "content": "以下哪种模型适合需求变化频繁的项目？",
  "options": ["瀑布模型", "螺旋模型", "V模型", "原型模型"],
  "answer": "",  // 原文档无答案，留空
  "question_type": "single", 
  "difficulty": "medium",
  "response_notes": "原文档未包含答案"
}

// 多选题示例
{
  "number": 3,
  "content": "软件工程的基本要素包括（          ）。",  // 清理了答案标注
  "options": ["方法", "工具", "过程", "人员"],//不要保留前缀
  "answer": "A,B,C",  // 多选答案用逗号分隔
  "question_type": "multiple",
  "difficulty": "medium",
  "response_notes": "检测到原文档包含答案，已自动提取并清理题干"
}

// 填空题示例
{
  "number": 4,
  "content": "软件工程的基本要素包括方法、工具和_____。",
  "options": [],
  "answer": "过程",
  "question_type": "blank",
  "difficulty": "easy",
  "response_notes": "检测到原文档包含答案，已自动提取并清理题干"
}

// 问答题示例
{
  "number": 5,
  "content": "简述螺旋模型的特点和适用场景。",
  "options": [],
  "answer": "螺旋模型结合了瀑布模型和原型模型的优点，强调风险分析，适用于大型复杂项目...",
  "question_type": "essay",
  "difficulty": "hard",
  "response_notes": "检测到原文档包含答案，已自动提取"
}

**处理原则**：
1. **重点**：务必清理题干中的所有答案标注，如"（A）"、"（ C ）"、"（B）"等，替换为相应长度的空白括号
2. 优先保持题目的学术性和专业性
3. 选择题选项不要保留A、B、C、D等前缀
4. 如果原文档中题目已包含正确答案，务必提取并在response_notes中说明
5. 如果原文档中没有答案，answer字段设为空字符串，response_notes说明"原文档未包含答案"
6. 填空题中的空格"_____"或"______"保持不变

请严格返回JSON数组格式，不要输出多余内容。
"""
        user_prompt = f"请分割以下markdown内容为题目数组：\n\n{markdown}"
        try:
            resp = llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
            ai_content = resp.content if hasattr(resp, 'content') else resp['content']
            print('==== AI分割结果 ====')
            print(ai_content)
            # 只提取JSON部分
            json_pattern = r'(\[.*\])'
            import re
            match = re.search(json_pattern, ai_content, re.DOTALL)
            if match:
                questions = json.loads(match.group(1))
            else:
                questions = json.loads(ai_content)
            return jsonify({'questions': questions})
        except Exception as e:
            print('AI分割异常:', e)
            return jsonify({'msg': f'AI分割题目失败: {str(e)}'}), 500
    finally:
        os.remove(tmp_path)

@bp.route('/import/commit', methods=['POST'])
@token_required
def import_commit():
    data = request.json
    user_id = request.user.get('user_id')
    questions = data.get('questions', [])
    course_id = data.get('course_id')
    
    # 验证课程是否存在且属于当前教师
    if course_id:
        course = Course.query.filter_by(id=course_id, teacher_id=user_id, is_deleted=False).first()
        if not course:
            return jsonify({'msg': '课程不存在或无权限访问'}), 403
    
    assignment = get_or_create_question_bank_assignment(course_id, user_id)
    
    # 转换字段映射
    question_type_map = {
        'single': 'single',
        'multiple': 'multiple',
        'blank': 'blank',
        'essay': 'essay'
    }
    
    for q in questions:
        # 处理答案字段
        answers = None
        reference = None
        
        if q.get('question_type') in ['single', 'multiple']:
            # 选择题：答案存储到answers字段
            if isinstance(q.get('answer'), list):
                if len(q['answer']) == 1:
                    answers = q['answer'][0]
                else:
                    answers = ','.join(q['answer'])
            else:
                answers = str(q.get('answer', ''))
        elif q.get('question_type') == 'blank':
            # 填空题：答案存储到answers字段
            answers = str(q.get('answer', ''))
        elif q.get('question_type') == 'essay':
            # 问答题：参考答案存储到reference字段
            reference = str(q.get('answer', ''))
        
        question = Question(
            id=uuid.uuid4(),
            assignment_id=assignment.id,
            type=question_type_map.get(q.get('question_type', 'single'), 'single'),
            content=q['content'],
            options=json.dumps(q.get('options', [])) if q.get('options') else None,
            answers=answers,
            reference=reference,
            explanation=q.get('explanation'),
            order_num=0,
            max_score=5.0,
            keywords=None,
            create_time=datetime.now(),
            update_time=datetime.now(),
            course_id=course_id or q.get('course_id'),  # 优先用批量选择的科目
            difficulty=q.get('difficulty'),  # 新增：写入AI识别的难度
            tags=None,  # tags字段不再直接用
            remark=q.get('remark'),
            creator_id=user_id,
            created_at=datetime.now()
        )
        db.session.add(question)
    db.session.commit()
    # 新增：为每个题目异步提取关键词
    from flask import current_app
    from utils.question_processing_pool import question_processing_pool
    from services.keyword_extraction_service import global_keyword_extraction_service
    app = current_app._get_current_object()
    for question in Question.query.filter_by(assignment_id=assignment.id).order_by(Question.create_time.desc()).limit(len(questions)).all():
        question_processing_pool.submit_task(app, question.id, global_keyword_extraction_service.extract_keywords)
    return jsonify({'msg': f'成功导入{len(questions)}道题'})

@bp.route('/list', methods=['GET'])
@token_required
def list_questions_paginated():
    """分页获取题库题目，支持筛选和搜索，只显示当前教师课程的题目"""
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 10))
    course_id = request.args.get('course_id')
    user_id = request.user.get('user_id')
    qtype = request.args.get('type')
    difficulty = request.args.get('difficulty')
    tag = request.args.get('tag')
    keyword = request.args.get('keyword')
    
    # 获取当前教师的所有课程ID列表
    teacher_courses = Course.query.filter_by(teacher_id=user_id, is_deleted=False).all()
    teacher_course_ids = [course.id for course in teacher_courses]
    
    if not teacher_course_ids:
        # 如果教师没有课程，返回空结果
        return jsonify({'list': [], 'total': 0, 'page': page, 'pageSize': page_size})
    
    if not course_id:
        # 不传course_id时，查当前教师所有课程的题库题目
        assignments = Assignment.query.filter_by(title='题库题目').all()
        assignment_ids = [a.id for a in assignments]
        query = Question.query.join(Course, Question.course_id == Course.id).filter(
            Question.assignment_id.in_(assignment_ids),
            Question.course_id.in_(teacher_course_ids)  # 只查询当前教师课程的题目
        )
        if qtype:
            # 前端题型值到数据库字段值的映射
            question_type_map = {
                'single': 'single',
                'multiple': 'multiple', 
                'blank': 'blank',
                'essay': 'essay'
            }
            db_type = question_type_map.get(qtype, qtype)
            query = query.filter(Question.type == db_type)
        if difficulty:
            query = query.filter(Question.difficulty == difficulty)
        if tag:
            query = query.filter(Question.tags.contains([tag]))
        if keyword:
            query = query.filter(Question.content.like(f"%{keyword}%"))
        total = query.count()
        questions = query.order_by(Question.create_time.desc()).offset((page-1)*page_size).limit(page_size).all()
        # 格式化结果，确保包含课程名称
        result = []
        for q in questions:
            q_dict = q.to_dict()
            # 确保course_name字段存在
            if not q_dict.get('course_name') and q.course_id:
                course = Course.query.get(q.course_id)
                q_dict['course_name'] = course.name if course else '未知课程'
            
            # 添加是否可编辑的标识（只有题目所属课程的教师可以编辑）
            can_edit = False
            if q.course_id:
                course = Course.query.filter_by(id=q.course_id, is_deleted=False).first()
                if course and str(course.teacher_id) == str(user_id):
                    can_edit = True
            q_dict['can_edit'] = can_edit
            
            # 添加关联知识点信息
            question_keywords = QuestionKeyword.query.filter_by(question_id=q.id).all()
            extracted_keywords = []
            for qk in question_keywords:
                if qk.keyword:
                    extracted_keywords.append({
                        'id': qk.keyword.id,
                        'name': qk.keyword.name,
                        'category': qk.keyword.category
                    })
            q_dict['extractedKeywords'] = extracted_keywords
            
            result.append(q_dict)
        
        return jsonify({'list': result, 'total': total, 'page': page, 'pageSize': page_size})
    
    # 验证course_id是否属于当前教师
    try:
        course_uuid = uuid.UUID(course_id)
    except Exception:
        return jsonify({'msg': 'course_id 非法，必须为合法 UUID', 'list': [], 'total': 0, 'page': page, 'pageSize': page_size}), 400
    if course_uuid not in teacher_course_ids:
        print(course_uuid, teacher_course_ids)
        return jsonify({'msg': '无权访问该课程的题目', 'list': [], 'total': 0, 'page': page, 'pageSize': page_size}), 403
    
    assignment = get_or_create_question_bank_assignment(course_id, user_id)
    query = Question.query.join(Course, Question.course_id == Course.id).filter(Question.assignment_id == assignment.id)
    if course_id:
        query = query.filter(Question.course_id == course_id)
    if qtype:
        # 前端题型值到数据库字段值的映射
        question_type_map = {
            'single': 'single',
            'multiple': 'multiple', 
            'blank': 'blank',
            'essay': 'essay'
        }
        db_type = question_type_map.get(qtype, qtype)
        query = query.filter_by(type=db_type)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if tag:
        query = query.filter(Question.tags.contains([tag]))
    if keyword:
        query = query.filter(Question.content.like(f"%{keyword}%"))
    total = query.count()
    questions = query.order_by(Question.create_time.desc()).offset((page-1)*page_size).limit(page_size).all()
    # 格式化结果，确保包含课程名称
    result = []
    for q in questions:
        q_dict = q.to_dict()
        # 确保course_name字段存在
        if not q_dict.get('course_name') and q.course_id:
            course = Course.query.get(q.course_id)
            q_dict['course_name'] = course.name if course else '未知课程'
        
        # 添加是否可编辑的标识（只有题目所属课程的教师可以编辑）
        can_edit = False
        if q.course_id:
            course = Course.query.filter_by(id=q.course_id, is_deleted=False).first()
            if course and str(course.teacher_id) == str(user_id):
                can_edit = True
        q_dict['can_edit'] = can_edit
        
        # 添加关联知识点信息
        question_keywords = QuestionKeyword.query.filter_by(question_id=q.id).all()
        extracted_keywords = []
        for qk in question_keywords:
            if qk.keyword:
                extracted_keywords.append({
                    'id': qk.keyword.id,
                    'name': qk.keyword.name,
                    'category': qk.keyword.category
                })
        q_dict['extractedKeywords'] = extracted_keywords
        
        result.append(q_dict)
    
    return jsonify({'list': result, 'total': total, 'page': page, 'pageSize': page_size})

@bp.route('/<question_id>/detail', methods=['GET'])
def get_question_detail(question_id):
    """获取单个题目详情（学生端使用，无需认证）"""
    try:
        question = Question.query.get(question_id)
        if not question:
            return jsonify(Result.error(404, "题目不存在")), 404
        
        # 构建题目详情数据
        question_data = {
            "id": str(question.id),
            "content": question.content,
            "type": question.type,
            "options": json.loads(question.options) if question.options else [],
            "answers": question.answers,  # 添加answers字段
            "reference": question.reference,  # 添加reference字段
            "explanation": question.explanation,
            "max_score": question.max_score,
            "difficulty": question.difficulty or "medium",  
            "tags": question.tags if question.tags else []
        }
        
        # 获取课程信息
        if question.course_id:
            course = Course.query.get(question.course_id)
            if course:
                question_data["course"] = {
                    "id": str(course.id),
                    "name": course.name,
                    "code": course.code
                }
        
        # 获取作业信息
        if question.assignment_id:
            assignment = Assignment.query.get(question.assignment_id)
            if assignment:
                question_data["assignment"] = {
                    "id": str(assignment.id),
                    "title": assignment.title
                }
        
        # 获取关联的知识点
        question_keywords = QuestionKeyword.query.filter_by(question_id=question_id).all()
        if question_keywords:
            keyword_ids = [qk.keyword_id for qk in question_keywords]
            keywords = Keyword.query.filter(Keyword.id.in_(keyword_ids)).all()
            question_data["keywords"] = [
                {
                    "id": str(kw.id),
                    "name": kw.name,
                    "description": kw.description,
                    "category": kw.category
                } for kw in keywords
            ]
        else:
            question_data["keywords"] = []
        
        return jsonify(Result.success(question_data, "获取题目详情成功"))
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify(Result.error(500, f"获取题目详情失败: {str(e)}")), 500