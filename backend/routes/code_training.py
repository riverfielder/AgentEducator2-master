import uuid
import json
import sys
import io
import re
from flask import Blueprint, request, jsonify
from utils.auth import token_required
from services.unified_llm_service import UnifiedLLMService
from utils.static_analyzer import CodeStaticAnalyzer

code_training_bp = Blueprint('code_training', __name__)
llm_service = UnifiedLLMService()

def extract_json(text):
    match = re.search(r'```json\n(.*?)\n```', text, re.DOTALL)
    if match: return match.group(1).strip()
    match = re.search(r'```\n(.*?)\n```', text, re.DOTALL)
    if match: return match.group(1).strip()
    if text.startswith('{'): return text.strip()
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        return text[start:end+1]
    return text.strip()

@code_training_bp.route('/generate_task', methods=['POST'])
@token_required
def generate_task():
    data = request.get_json()
    task_type = data.get('task_type', 'debug')
    keyword_name = data.get('keyword', 'Python规范与软件工程')

    if task_type == 'debug':
        desc = '【带Bug的逻辑漏洞代码题】（需修复会导致报错或输出错误的隐藏逻辑问题）'
        bad_code_example = 'def process(data):\n    # 你的逻辑Bug代码写在这里'
    else:
        desc = '【待优化的低质量代码题】（需重构以解决代码冗余、命名不规范、高耦合等代码质量问题，无明显逻辑报错）'
        bad_code_example = 'def Do_thing_1(x, y):\n    # 你的低质量代码写在这里'

    prompt = f"""你是一个高级的编程教师。系统需要在「{keyword_name}」等知识点上，为学生动态生成一道{desc}。
切记：生成的题目必须能够通过点击运行或分析看出具体的问题！
请仅输出严格的JSON，不要添加任何Markdown标记（不要```json等），直接输出花括号结构：
{{
    "title": "题目描述（例如：修复未处理空指针导致计算报错的逻辑Bug）",
    "bad_code": "{bad_code_example}\\n# 在末尾添加几行print测试代码以便学生可以看到运行结果\\nprint(process([1, 2]))",
    "solution_code": "def process(data):\\n    if not data: return 0...",
    "hints": ["提示1：考虑如果输入为空该怎么办？", "提示2：变量命名规范"],
    "knowledge_points": ["异常处理", "边界测试"]
}}
"""
    try:
        llm = llm_service.get_llm('qa_main')
        response = llm.invoke([{'role': 'user', 'content': prompt}])
        json_str = response.content if hasattr(response, 'content') else response['content']
        
        json_str = extract_json(json_str)
        result = json.loads(json_str, strict=False)
        result['id'] = str(uuid.uuid4())
        result['task_type'] = task_type
        return jsonify({'code': 200, 'data': result})
    except Exception as e:
        import traceback
        return jsonify({'code': 500, 'message': str(e), 'trace': traceback.format_exc()}), 500

@code_training_bp.route('/submit_review', methods=['POST'])
@token_required
def submit_review():
    data = request.get_json()
    student_code = data.get('student_code', '')
    task_info = data.get('task_info', {})
    attempts = data.get('attempts', 1)

    analyzer = CodeStaticAnalyzer(student_code)
    static_report = analyzer.analyze()
    static_text = static_report.get('formatted_report', '')

    prompt = f"""你是一个坚定遵守柏拉图/苏格拉底式启发法的编程高级导师。
题目要求：{task_info.get('title')}
学生提交的代码：
{student_code}

【静态AST分析结果】：
{static_text}

这是学生的第 {attempts} 次提交 (最多 5 次)。
规则要求（极端严格）：
1. 绝对、绝对、绝对不要直接指出具体哪行代码错误！绝对不要直接给出修改后的代码！任何借口都不行！
2. 即使学生的代码一塌糊涂，你也只能使用提问式、启发式语言。比如：如果传入空列表会怎样？、看看第X步，有没有考虑过Y的边界？
3. 如果 attempts < 5：你的最终目的是引导，必须让学生自己想出答案。只要 attempts < 5 你的 status 只能是 KEEP_TRYING （除非学生直接写全对）。
4. 只有当 attempts >= 5 且代码依然错误时，你才将 status 设为 "MAX_TRIES_REACHED"，此时在 final_answer 给出正确答案代码，并在 feedback 中进行最终讲解。
5. 如果代码完全正确且符合规范，将 status 标记为 "SUCCESS"。

请严格返回下方JSON格式：
{{
    "status": "KEEP_TRYING",
    "feedback": "一句切中要害的反问语 或 一个破坏性测试用例。如果未达到5次，绝不可出现修复代码片段！",
    "knowledge_links": ["扩展资料：软件工程-安全编程", "扩展资料：防御性设计"],
    "final_answer": "如果是 MAX_TRIES_REACHED 则输出终极代码解答，否则必须为空字符串！！！"
}}
"""
    try:
        llm = llm_service.get_llm('qa_main')
        response = llm.invoke([{'role': 'user', 'content': prompt}])
        json_str = response.content if hasattr(response, 'content') else response['content']
        
        json_str = extract_json(json_str)
        result = json.loads(json_str, strict=False)
        result['static_score'] = static_report.get('quality_score', 0)
        return jsonify({'code': 200, 'data': result})
    except Exception as e:
        import traceback
        return jsonify({'code': 500, 'message': str(e), 'trace': traceback.format_exc()}), 500

@code_training_bp.route('/run_code', methods=['POST'])
@token_required
def run_code():
    data = request.get_json()
    student_code = data.get('student_code', '')
    
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    redirected_output = io.StringIO()
    sys.stdout = redirected_output
    sys.stderr = redirected_output
    
    output = ''
    try:
        local_scope = {}
        exec(student_code, {}, local_scope)
        output = redirected_output.getvalue()
        if not output.strip() and 'def ' in student_code:
            output += '\n\n[系统提示] 代码运行结束。如果没有任何输出，请确认你是否在代码末尾主动调用了相应的函数（例如：print(func(...))）。'
    except Exception as e:
        import traceback
        output = redirected_output.getvalue() + '\n' + traceback.format_exc()
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
    return jsonify({'code': 200, 'data': {'output': output.strip()}})
