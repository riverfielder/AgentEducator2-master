import re

with open('services/assignment_grading_service.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_str = """    @staticmethod
    def grade_answer(question, standard_answer, student_answer, score_full=5, grading_criteria=None):
        \"\"\"
        调用大模型对学生答案进行自动评分
        :param question: 题目内容
        :param standard_answer: 标准答案
        :param student_answer: 学生答案
        :param score_full: 满分
        :param grading_criteria: 评分标准（可选）
        :return: dict, 包含分数、评语、批注等
        \"\"\"
        # 构造 prompt
        prompt = f\"\"\"
你是一名公平、公正的教师，请根据以下信息对学生作答进行评分和点评。
题目：{question}
标准答案：{standard_answer}
学生答案：{student_answer}
评分标准：{grading_criteria or '准确性、完整性、表达清晰度'}

评分要求：
1. 请详细分析学生答案的优点和不足
2. 对于有一定道理或部分正确的答案，应给予相应分数
3. 即使答案不够完美，但能看出学生有思考和努力，可酌情给予\"辛苦分\"
4. 鼓励学生的学习态度和思考过程

请按照满分{score_full}分进行评分，返回如下JSON格式：
{{
  \\"score\\": int, // 得分
  \\"is_correct\\": bool, // 是否答对
  \\"comment\\": str // 教师评语
}}
        \"\"\""""

new_str = """    @staticmethod
    def grade_answer(question, standard_answer, student_answer, score_full=5, grading_criteria=None):
        \"\"\"
        调用大模型对学生答案进行自动评分
        :param question: 题目内容
        :param standard_answer: 标准答案
        :param student_answer: 学生答案
        :param score_full: 满分
        :param grading_criteria: 评分标准（可选）
        :return: dict, 包含分数、评语、批注等
        \"\"\"
        # 尝试进行代码静态分析
        static_analysis_result = \"\"
        is_code = False
        import re
        code_block_match = re.search(r'```python\\s*(.*?)\\s*```', student_answer, re.DOTALL)
        code_to_analyze = code_block_match.group(1) if code_block_match else student_answer
        
        if \"def \" in code_to_analyze or \"class \" in code_to_analyze or \"import \" in code_to_analyze:
            is_code = True
            try:
                from utils.static_analyzer import CodeStaticAnalyzer
                analyzer = CodeStaticAnalyzer(code_to_analyze)
                analysis_report = analyzer.analyze()
                static_analysis_result = f\"\\n✅ 【系统已执行代码静态分析】结果如下：\\n{analysis_report['formatted_report']}\\n\"
            except Exception as e:
                print(f\"Static analysis error: {e}\")

        # 构造 prompt
        prompt = f\"\"\"
你是一名公平、公正的教师，请根据以下信息对学生作答进行评分和点评。
题目：{question}
标准答案：{standard_answer}
学生答案：{student_answer}
{static_analysis_result}
评分标准：{grading_criteria or '准确性、完整性、表达清晰度'}

评分要求：
1. 请详细分析学生答案的优点和不足
2. 对于有一定道理或部分正确的答案，应给予相应分数
3. 即使答案不够完美，但能看出学生有思考和努力，可酌情给予\"辛苦分\"
4. 鼓励学生的学习态度和思考过程
{\"5. 针对编程题，请务必将上方提供的【系统代码静态分析】整合到你的评语中，强制要求学生关注命名规范、注释和模块化问题！\" if is_code else \"\"}

请按照满分{score_full}分进行评分，返回如下JSON格式：
{{
  \\"score\\": int, // 得分
  \\"is_correct\\": bool, // 是否答对
  \\"comment\\": str // 教师评语
}}
        \"\"\""""

if old_str in text:
    with open('services/assignment_grading_service.py', 'w', encoding='utf-8') as f:
        f.write(text.replace(old_str, new_str))
    print("SUCCESS")
else:
    print("NOT FOUND")
