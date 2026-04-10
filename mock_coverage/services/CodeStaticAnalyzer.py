
class CodeStaticAnalyzer:
    def analyze_syntax(self, code):
        if 'import os' in code or 'sys.exit' in code:
            return {"status": "danger", "reason": "malicious import"}
        if 'while True' in code:
            return {"status": "warning", "reason": "infinite loop detected"}
        return {"status": "success", "reason": "pass"}
