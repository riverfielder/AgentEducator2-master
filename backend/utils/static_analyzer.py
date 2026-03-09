import ast
import re

class CodeStaticAnalyzer:
    """
    静态代码分析工具，用于检查学生提交代码的质量：
    - 命名规范 (snake_case/CamelCase)
    - 模块化 (函数过长)
    - 注释覆盖率 (是否有docstring)
    """
    
    def __init__(self, code: str):
        self.code = code
        self.issues = []
        self.score = 100
        try:
            self.tree = ast.parse(code)
            self.parse_success = True
        except SyntaxError as e:
            self.tree = None
            self.parse_success = False
            self.issues.append(f"语法错误: 第{e.lineno}行 - {e.msg}")
            self.score = 0
            
    def analyze(self):
        if not self.parse_success:
            return self._build_report()
            
        self._check_naming_conventions()
        self._check_modularity()
        self._check_comments_and_docstrings()
        
        return self._build_report()
        
    def _check_naming_conventions(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                if not re.match(r'^[a-z_][a-z0-9_]*$', node.name) and node.name != '__init__':
                    self.issues.append(f"命名不规范: 函数名 '{node.name}' 应该使用小写字母和下划线 (snake_case)。")
                    self.score -= 5
            elif isinstance(node, ast.ClassDef):
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                    self.issues.append(f"命名不规范: 类名 '{node.name}' 应该使用首字母大写拼写法 (CamelCase)。")
                    self.score -= 5
            elif isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store) and not re.match(r'^[a-z_][a-z0-9_]*$', node.id):
                    # 忽略常量大写
                    if not re.match(r'^[A-Z_][A-Z0-9_]*$', node.id):
                        self.issues.append(f"命名不规范: 变量名 '{node.id}' 建议使用小写字母和下划线 (snake_case)。")
                        self.score -= 2
                        
    def _check_modularity(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                # 简单估算函数行数
                lines = getattr(node, 'end_lineno', node.lineno) - node.lineno
                if lines > 30:
                    self.issues.append(f"模块化建议: 函数 '{node.name}' 过长 ({lines}行)，建议将其拆分为更小的子函数。")
                    self.score -= 10
                    
    def _check_comments_and_docstrings(self):
        # 检查模块级别docstring
        if not ast.get_docstring(self.tree):
            self.issues.append("注释建议: 缺少模块级别的文档字符串 (Docstring)。")
            self.score -= 5
            
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    type_name = "函数" if isinstance(node, ast.FunctionDef) else "类"
                    self.issues.append(f"注释建议: {type_name} '{node.name}' 缺少文档字符串。说明功能和参数有助于提高代码可读性。")
                    self.score -= 5
                    
    def _build_report(self):
        import json
        self.score = max(0, self.score)
        
        status = "优秀"
        if self.score < 60:
            status = "需要改进"
        elif self.score < 80:
            status = "良好"
            
        # 去重
        self.issues = list(set(self.issues))
            
        return {
            "parse_success": self.parse_success,
            "quality_score": self.score,
            "quality_status": status,
            "issues": self.issues[:10], # 最多返回10条
            "formatted_report": self._format_text_report(status)
        }
        
    def _format_text_report(self, status):
        if not self.parse_success:
            return f"❌ 代码静态分析失败：存在语法错误。\n{self.issues[0]}"
            
        if not self.issues:
            return "✅ 代码静态分析通过！规范度极高，代码结构清晰，命名标准。"
            
        report = f"📊 代码静态分析报告 (评分: {self.score}/100, 评级: {status})\n\n"
        report += "发现以下可改进点，请注意代码规范：\n"
        for i, issue in enumerate(self.issues[:10], 1):
            report += f"{i}. {issue}\n"
            
        return report

if __name__ == '__main__':
    # Test
    test_code = '''
def CALCULATESum(  items ):
    total = 0
    for i in range(len(items)):
        total += items[i]
    return total
'''
    analyzer = CodeStaticAnalyzer(test_code)
    print(analyzer.analyze()['formatted_report'])
