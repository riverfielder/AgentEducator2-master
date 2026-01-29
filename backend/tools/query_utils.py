"""查询增强工具"""

from typing import List, Optional


class QueryEnhancer:
    """查询增强器"""
    
    @staticmethod
    def enhance_with_keywords(base_query: str, keywords: List[str], max_keywords: int = 5) -> str:
        """
        使用知识点增强查询
        
        Args:
            base_query: 基础查询
            keywords: 知识点列表
            max_keywords: 最多使用的知识点数量
            
        Returns:
            增强后的查询字符串
        """
        enhanced_query = base_query
        
        if keywords:
            selected_keywords = keywords[:max_keywords]
            keyword_text = " ".join(selected_keywords)
            enhanced_query += f" {keyword_text}"
            
        return enhanced_query.strip()
    
    @staticmethod
    def build_context_query(query: Optional[str], keywords: List[str], max_keywords: int = 5) -> str:
        """
        构建带上下文的查询
        
        Args:
            query: 用户查询
            keywords: 上下文知识点
            max_keywords: 最多使用的知识点数量
            
        Returns:
            构建的查询字符串
        """
        parts = []
        
        if query:
            parts.append(query)
            
        if keywords:
            selected_keywords = keywords[:max_keywords]
            parts.append(" ".join(selected_keywords))
            
        return " ".join(parts)
