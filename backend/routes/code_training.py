import uuid
import json
import sys
import io
from flask import Blueprint, request, jsonify
from utils.auth import token_required
from services.unified_llm_service import UnifiedLLMService
from utils.static_analyzer import CodeStaticAnalyzer

code_training_bp = Blueprint('code_training', __name__)
llm_service = UnifiedLLMService()

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

    prompt = f\"\"\"你是一个高级的编程教师。系统需要在「{keyword_name}」等知识点上，为学生动态生成一道{desc}。
切记：生成的题目必须能够通过点击运行或分析看出具体的问题！
请仅输出严格的JSON，不要添加任何Markdown标记（不要`json等），直接输出花括号结构：
{{
    "title": "题目描述（例如：修复未处理空指针导致计算报错的逻辑Bug）",
    "bad_code": "{bad_code_example}\\n# 在末尾添加几行print测试代码以便学生可以看到运行结果\\nprint(process([1, 2]))",
    "solution_code": "def process(data):\\n    if not data: return 0...",
    "hints": ["提示1：考虑如果输入为空该怎么办？", "提示2：变量命名规范"],
    "knowledge_points": ["异常处理", "边界测试"]
}}
\"\"\"
    try:
        llm = llm_service.get_llm('qa_main')
        response = llm.invoke([{'role': 'user', 'content': prompt}])
        json_str = response.content if hasattr(response, 'content') else response['content']
        if '`json' in json_str: json_str = json_str.split('`json')[1].split('`')[0].strip()
        elif '`' in json_str: json_str = json_str.split('`')[1].split('`')[0].strip()
        result = json.loads(json_str, strict=False)
        result['id'] = str(uuid.uuid4())
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

    prompt = f\"\"\"你是一个使用柏拉图/苏格拉底式启发法的编程导师。
题目要求：{task_info.get('title')}
学生提交的代码：
{student_code}

【静态AST分析结果】：
{static_text}

规则要求：
1. 绝对不要直接指出具体哪行代码错误，也不要直接给出修复代码！
2. 必须使用提问式、启发式的语言。例如：如果传入一个空列表，你的代码在第X步会发生什么？ 或者抛出一个典型的会引发错误的边缘测试用例。
3. 让学生自己思考应该如何改进。将错误点与软件工程规范（如异常处理、防御性编程等）结合起来进行提问。
4. 这个学生是第{attempts}次（最多5次）尝试。如果 attempts >= 5次依然错误，你才可以结束启发，并在 final_answer 中给出正确的最终答案代码。
5. 如果代码完全正确且规范（静态打分完美），请将status标记为 SUCCESS。

请严格返回下方JSON格式：
{{
    "status": "KEEP_TRYING", // 如果成功答对为 "SUCCESS", 如果超出5次为 "MAX_TRIES_REACHED"
    "feedback": "柏拉图式启发反问语 或 一个破坏性的测试用例（不要直接给答案代码）",
    "knowledge_links": ["扩展资料：软件工程-安全编程", "扩展资料：防御性设计"],
    "final_answer": "如果是 MAX_TRIES_REACHED 则输出终极代码解答，否则始终为空字符串"
}}
\"\"\"
    try:
        llm = llm_service.get_llm('qa_main')
        response = llm.invoke([{'role': 'user', 'content': prompt}])
        json_str = response.content if hasattr(response, 'content') else response['content']
        if '`json' in json_str: json_str = json_str.split('`json')[1].split('`')[0].strip()
        elif '`' in json_str: json_str = json_str.split('`')[1].split('`')[0].strip()
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
