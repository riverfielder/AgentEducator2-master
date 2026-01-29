"""结果格式化工具"""

from typing import List, Dict, Any, Optional


class ResultFormatter:
    """结果格式化器"""
    
    @staticmethod
    def format_document_results(docs_with_indices: List[Any], prefix: str = "片段") -> List[str]:
        """
        格式化文档结果
        
        Args:
            docs_with_indices: 带索引的文档列表
            prefix: 前缀文本，如"片段"、"教学片段"等
            
        Returns:
            格式化的结果列表
        """
        results = []
        for doc in docs_with_indices:
            global_idx = getattr(doc, '_global_index', '?')
            results.append(f"{prefix}[{global_idx}]: {doc.page_content}")
        return results
    
    @staticmethod
    def build_result_with_header(
        results: List[str], 
        title: str, 
        query: Optional[str] = None,
        additional_info: Optional[Dict[str, str]] = None
    ) -> str:
        """
        构建带头部信息的结果
        
        Args:
            results: 格式化的结果列表
            title: 主标题（如视频标题、课程名称）
            query: 查询内容
            additional_info: 额外信息字典
            
        Returns:
            完整的结果字符串
        """
        header_parts = [f"标题: {title}"]
        
        if query:
            header_parts.append(f"查询内容: {query}")
            
        if additional_info:
            for key, value in additional_info.items():
                header_parts.append(f"{key}: {value}")
        
        header = "\n".join(header_parts)
        header += "\n\n检索到的相关内容:\n"
        for i in range(len(results)):
            if "屏幕内容" in results[i]:
                results[i] = f"【视频】{results[i]}"
            else:
                results[i] = f"【课件】{results[i]}"
        result_text = "\n".join(results)
        return header + result_text
    
    @staticmethod
    def format_video_result(
        docs_with_indices: List[Any], 
        video_title: str, 
        query: Optional[str] = None
    ) -> str:
        """格式化视频检索结果"""
        results = ResultFormatter.format_document_results(docs_with_indices, "片段")
        return ResultFormatter.build_result_with_header(
            results, 
            f"视频: {video_title}", 
            query
        )
    
    @staticmethod
    def format_course_result(
        docs_with_indices: List[Any], 
        course_name: str, 
        query: Optional[str] = None,
        core_concepts: Optional[List[str]] = None
    ) -> str:
        """格式化课程检索结果"""
        results = ResultFormatter.format_document_results(docs_with_indices, "教学片段")
        
        additional_info = {}
        if core_concepts:
            additional_info["一级知识点"] = ", ".join(core_concepts[:3])
            
        return ResultFormatter.build_result_with_header(
            results, 
            f"课程: {course_name}", 
            query,
            additional_info
        )

    @staticmethod
    def format_document_result(
        docs_with_indices: List[Any], 
        document_title: str, 
        query: Optional[str] = None,
        document_type: Optional[str] = None
    ) -> str:
        """格式化文档检索结果"""
        results = ResultFormatter.format_document_results(docs_with_indices, "文档片段")
        
        additional_info = {}
        if document_type:
            additional_info["文档类型"] = document_type
            
        return ResultFormatter.build_result_with_header(
            results, 
            f"文档: {document_title}", 
            query,
            additional_info
        )
