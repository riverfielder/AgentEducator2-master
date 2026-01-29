"""通用知识工具"""

from typing import Dict, Any
from .base_tool import BaseTool


class GeneralKnowledgeTool(BaseTool):
    """通用知识工具"""
    
    def __init__(self, user_id: str = None):
        super().__init__(user_id=user_id)
    
    def get_display_info(self) -> Dict[str, Any]:
        """获取前端展示信息"""
        return {
            "tool_name": "通用知识库",
            "tool_icon": "mdi-brain",
            "tool_color": "purple",
            "description": "基于通用知识回答问题",
            "context": {
                "knowledge_type": "通用知识库"
            },
            "status_message": "正在基于通用知识分析问题..."
        }
        
    def search(self, query: str) -> str:
        """使用通用知识回答问题"""
        print(f"[FLOW] GeneralKnowledgeTool.search 开始执行")
        print(f"[FLOW] 查询内容: {query[:50]}...")
        
        # 获取展示信息并通知前端
        display_info = self.get_display_info()
        self._notify_tool_start(display_info)
        
        result = f"基于通用知识：对于问题'{query}'，建议查阅相关教学资料或使用检索功能获取更准确的信息。"
        
        # 通知前端执行结果
        self._notify_tool_result({
            "success": True,
            "message": "已基于通用知识提供建议",
            "knowledge_type": "通用知识"
        })
        
        print(f"[FLOW] GeneralKnowledgeTool 执行完成")
        return result
