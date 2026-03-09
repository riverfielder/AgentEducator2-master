import uuid
import json
from flask import Blueprint, request, jsonify
from utils.auth import token_required
from services.unified_llm_service import UnifiedLLMService
from models.models import db, KnowledgePointMastery, Keyword
from utils.static_analyzer import CodeStaticAnalyzer
import time

training_bp = Blueprint('training', __name__)
llm_service = UnifiedLLMService()

@training_bp.route('/generate', methods=['POST'])
@token_required
def generate_training():
    """动态产生知识点专属训练卷"""
    data = request.get_json()
    user_id = request.user.get('user_id')
    keyword_name = data.get('keyword', 'Python Basics')
    count = data.get('count', 3)
    
    prompt = f"""
你是一个专业的编程导师。学生在掌握“{keyword_name}”这个知识点上存在薄弱环节。
请你实时为其动态生成一套专项训练题，包含不同题型。
请严格输出JSON数组格式，不要包含任何markdown修饰符（如 ```json 等），严格只输出一层列表：
[
  {{
    "id": "q1",
    "type": "single",
    "content": "关于这个知识点，以下哪个说法是正确的？",
    "options": ["A. xxx", "B. xxx", "C. xxx", "D. xxx"],
    "answers": "A",
    "reference": "",
    "explanation": "题目解析..."
  }},
  {{
    "id": "q2",
    "type": "essay",
    "content": "请编写一个Python函数来实现...",
    "options": [],
    "answers": "",
    "reference": "def my_func():...",
    "explanation": "本题考察的是..."
  }}
]
要求：
1. 确保生成 {count} 道题目（务必包含至少1道主观代码题`"type": "essay"`）。
2. 每道题目都必须紧扣“{keyword_name}”知识点。
3. "type" 只能是 "single", "multiple", "blank" 或 "essay" 之一。
"""
    try:
        llm = llm_service.get_llm("qa")
        response = llm.predict(prompt)
        
        # 提取 JSON
        json_str = response
        if '```json' in json_str:
            json_str = json_str.split('```json')[1].split('```')[0].strip()
        elif '```' in json_str:
            json_str = json_str.split('```')[1].split('```')[0].strip()
            
        questions = json.loads(json_str)
        # 为生成的题目赋上随机 UUID
        for q in questions:
            q['id'] = str(uuid.uuid4())
            if q.get('type') == 'essay':
               q['max_score'] = 10
            else:
               q['max_score'] = 5
        
        return jsonify({
            "code": 200,
            "message": "生成训练卷成功",
            "data": questions
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"生成试卷失败: {str(e)}"
        }), 500

@training_bp.route('/grade', methods=['POST'])
@token_required
def grade_training():
    """动态训练题专用批改接口，主观题自动执行AST代码规范验证"""
    data = request.get_json()
    user_id = request.user.get('user_id')
    question = data.get('question', {})
    student_answer = data.get('student_answer', '')
    keyword_name = data.get('keyword', '未知考点')
    
    q_type = question.get('type')
    
    # 客观题或填空题直接比对
    if q_type in ['single', 'multiple', 'blank']:
        correct_answer = question.get('answers', '')
        # 简单比对（实际生产中可更复杂）
        is_correct = (str(student_answer).strip().lower() == str(correct_answer).strip().lower())
        return jsonify({
            "code": 200,
            "data": {
                "score": 5 if is_correct else 0,
                "feedback": "回答正确！" if is_correct else f"回答错误。正确答案是 {correct_answer}。",
                "explanation": question.get('explanation', '')
            }
        })
        
    # 主观代码题批改 (引入静态分析)
    if q_type == 'essay':
        static_analysis_result = ""
        code_to_analyze = student_answer
        
        if '```python' in student_answer:
            code_parts = student_answer.split('```python')
            if len(code_parts) > 1:
                code_to_analyze = code_parts[1].split('```')[0]
        elif '```' in student_answer:
            code_parts = student_answer.split('```')
            if len(code_parts) > 1:
                code_to_analyze = code_parts[1].split('```')[0]
            
        if "def " in code_to_analyze or "class " in code_to_analyze or "import " in code_to_analyze:
            try:
                analyzer = CodeStaticAnalyzer(code_to_analyze)
                report = analyzer.analyze()
                if report['errors']:
                    static_analysis_result = f"\n✓【系统静态分析报告】：\n{report['formatted_report']}\n"
                else:
                    static_analysis_result = "\n✓【系统静态分析报告】：\n静态检查通过，代码规范优秀！\n"
            except Exception as e:
                pass
                
        eval_prompt = f"""
你是一个严格且公平的AI编程导师。
当前训练主要针对薄弱知识点：{keyword_name}
【题目描述】：{question.get('content')}
【参考答案】：{question.get('reference')}
【学生作答】：
{student_answer}

{static_analysis_result}

请根据以上作答内容和静态分析报告，使用中文对学生进行评分和详细点评。重点考察学生在该知识点上的掌握情况并指出不足。
务必只返回严格的JSON格式：
{{
    "score": 85,
    "feedback": "你的代码逻辑较好，但存在以下问题..."
}}
"""
        try:
            llm = llm_service.get_llm("qa")
            response = llm.predict(eval_prompt)
            # 解析 json
            json_str = response
            if '```json' in json_str:
                json_str = json_str.split('```json')[1].split('```')[0].strip()
            elif '```' in json_str:
                json_str = json_str.split('```')[1].split('```')[0].strip()
            
            result = json.loads(json_str)
            return jsonify({
                "code": 200,
                "data": result
            })
        except Exception as e:
            return jsonify({"code": 500, "message": str(e)}), 500

