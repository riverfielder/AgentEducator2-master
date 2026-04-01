import ast
import pytest

class ASTAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.func_count = 0
        self.issues = []
        
    def visit_FunctionDef(self, node):
        self.func_count += 1
        if not node.name.islower():
            self.issues.append(f"函数命名 '{node.name}' 不符合规范")
        self.generic_visit(node)
        
    def analyze(self, code_str):
        try:
            tree = ast.parse(code_str)
            self.visit(tree)
            return len(self.issues) == 0, self.issues
        except SyntaxError:
            return False, ["语法错误"]

def test_ast_analyzer_valid():
    code = "def valid_func():\n    pass"
    analyzer = ASTAnalyzer()
    is_valid, issues = analyzer.analyze(code)
    assert is_valid == True
    assert len(issues) == 0

def test_ast_analyzer_invalid_name():
    code = "def InvalidFunc():\n    pass"
    analyzer = ASTAnalyzer()
    is_valid, issues = analyzer.analyze(code)
    assert is_valid == False
    assert "不符合规范" in issues[0]

def test_ast_analyzer_syntax_error():
    code = "def error_func() pass"
    analyzer = ASTAnalyzer()
    is_valid, issues = analyzer.analyze(code)
    assert is_valid == False
    assert "语法错误" in issues[0]
