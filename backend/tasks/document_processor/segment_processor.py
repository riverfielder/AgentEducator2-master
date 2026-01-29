"""
智能分段处理器
实现基于结构和语义的文档智能分段功能
"""

import re
import math
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from utils.result import Result
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain.schema import Document


@dataclass
class DocumentSegment:
    """文档片段数据结构"""
    content: str
    start_position: int
    end_position: int
    segment_type: str  # 'heading', 'paragraph', 'list', 'table', 'code', 'mixed'
    level: int = 0  # 标题级别（如果是标题类型）
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class DocumentSegmentProcessor:
    """
    文档智能分段处理器 - 使用 LangChain 内置分段方法
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, min_chunk_size: int = 100):
        """
        初始化分段处理器
        
        Args:
            chunk_size: 分段大小
            chunk_overlap: 分段重叠大小
            min_chunk_size: 最小分段大小，小于此值的段会被合并
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        
        # 创建 Markdown 头部分割器
        self.headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
            ("#####", "Header 5"),
            ("######", "Header 6"),
        ]
        
        self.markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on
        )
        
        # 创建递归字符分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def segment_document(self, content: str) -> Result:
        """
        对文档内容进行智能分段
        
        Args:
            content: Markdown格式的文档内容
            
        Returns:
            Result: 包含分段结果的结果对象
        """
        try:
            if not content or not content.strip():
                return Result.error("文档内容为空")
            
            # 使用 Markdown 头部分割器处理
            md_header_splits = self.markdown_splitter.split_text(content)
            
            # 进一步使用递归字符分割器细分
            final_documents = self.text_splitter.split_documents(md_header_splits)
            
            # 转换为我们的分段格式
            segments = []
            start_pos = 0
            
            for i, doc in enumerate(final_documents):
                content_text = doc.page_content
                
                # 确定分段类型
                segment_type = "paragraph"
                level = 0
                
                # 从元数据中获取头部信息
                if doc.metadata:
                    for key, value in doc.metadata.items():
                        if key.startswith("Header"):
                            segment_type = "heading"
                            level = int(key.split()[-1])
                            break
                
                # 检查是否是代码块
                if content_text.strip().startswith("```"):
                    segment_type = "code"
                
                # 检查是否是列表
                if any(line.strip().startswith(("- ", "* ", "+ ")) or 
                        re.match(r"^\d+\. ", line.strip()) for line in content_text.split("\n")):
                    segment_type = "list"
                
                segment = DocumentSegment(
                    content=content_text,
                    start_position=start_pos,
                    end_position=start_pos + len(content_text),
                    segment_type=segment_type,
                    level=level,
                    metadata=doc.metadata
                )
                
                segments.append(segment)
                start_pos += len(content_text)
            
            # 合并太小的段
            segments = self._merge_small_segments(segments)
            
            # 重新计算位置
            self._recalculate_positions(segments)
            
            # 生成统计信息
            statistics = self._generate_statistics(segments)
            
            return Result.success({
                'segments': [self._segment_to_dict(seg) for seg in segments],
                'total_segments': len(segments),
                'statistics': statistics,
                'original_length': len(content)
            })
            
        except Exception as e:
            return Result.error(f"文档分段失败: {str(e)}")
    
    def _merge_small_segments(self, segments: List[DocumentSegment]) -> List[DocumentSegment]:
        """合并太小的段"""
        if not segments:
            return segments
        
        merged_segments = []
        i = 0
        
        while i < len(segments):
            current_segment = segments[i]
            
            # 如果当前段太小且不是标题，尝试合并
            if (len(current_segment.content) < self.min_chunk_size and 
                current_segment.segment_type != 'heading'):
                
                # 向前合并
                if merged_segments and merged_segments[-1].segment_type != 'heading':
                    last_segment = merged_segments[-1]
                    merged_content = last_segment.content + "\n\n" + current_segment.content
                    merged_metadata = {**last_segment.metadata, **current_segment.metadata}
                    
                    merged_segments[-1] = DocumentSegment(
                        content=merged_content,
                        start_position=last_segment.start_position,
                        end_position=current_segment.end_position,
                        segment_type="mixed",
                        level=0,
                        metadata=merged_metadata
                    )
                # 向后合并
                elif (i + 1 < len(segments) and 
                        segments[i + 1].segment_type != 'heading'):
                    next_segment = segments[i + 1]
                    merged_content = current_segment.content + "\n\n" + next_segment.content
                    merged_metadata = {**current_segment.metadata, **next_segment.metadata}
                    
                    merged_segment = DocumentSegment(
                        content=merged_content,
                        start_position=current_segment.start_position,
                        end_position=next_segment.end_position,
                        segment_type="mixed",
                        level=0,
                        metadata=merged_metadata
                    )
                    merged_segments.append(merged_segment)
                    i += 1  # 跳过下一个段，因为已经合并了
                else:
                    merged_segments.append(current_segment)
            else:
                merged_segments.append(current_segment)
            
            i += 1
        
        return merged_segments
    
    def _recalculate_positions(self, segments: List[DocumentSegment]):
        """重新计算段的位置"""
        current_pos = 0
        for segment in segments:
            segment.start_position = current_pos
            segment.end_position = current_pos + len(segment.content)
            current_pos = segment.end_position + 2  # 加上分隔符长度
    
    def _generate_statistics(self, segments: List[DocumentSegment]) -> Dict[str, Any]:
        """生成分段统计信息"""
        if not segments:
            return {}
        
        lengths = [len(seg.content) for seg in segments]
        type_counts = {}
        level_counts = {}
        
        for seg in segments:
            type_counts[seg.segment_type] = type_counts.get(seg.segment_type, 0) + 1
            if seg.segment_type == 'heading':
                level_counts[f'h{seg.level}'] = level_counts.get(f'h{seg.level}', 0) + 1
        
        return {
            'total_segments': len(segments),
            'average_length': sum(lengths) / len(lengths) if lengths else 0,
            'min_length': min(lengths) if lengths else 0,
            'max_length': max(lengths) if lengths else 0,
            'segment_types': type_counts,
            'heading_levels': level_counts
        }
    
    def _segment_to_dict(self, segment: DocumentSegment) -> Dict[str, Any]:
        """将分段对象转换为字典"""
        return {
            'content': segment.content,
            'start_position': segment.start_position,
            'end_position': segment.end_position,
            'segment_type': segment.segment_type,
            'level': segment.level,
            'length': len(segment.content),
            'metadata': segment.metadata or {}
        }


def create_segment_processor(chunk_size: int = 1000, chunk_overlap: int = 200, min_chunk_size: int = 100) -> DocumentSegmentProcessor:
    """
    创建文档分段处理器实例

    Args:
        chunk_size: 分段大小
        chunk_overlap: 分段重叠大小
        min_chunk_size: 最小分段大小
        
    Returns:
        DocumentSegmentProcessor: 分段处理器实例
    """
    return DocumentSegmentProcessor(chunk_size, chunk_overlap, min_chunk_size)


def segment_document_content(content: str, chunk_size: int = 1000, chunk_overlap: int = 300, min_chunk_size: int = 200) -> Result:
    """
    便捷函数：对文档内容进行分段
    
    Args:
        content: 文档内容
        chunk_size: 分段大小
        chunk_overlap: 分段重叠大小
        min_chunk_size: 最小分段大小
        
    Returns:
        Result: 分段结果
    """
    processor = create_segment_processor(chunk_size, chunk_overlap, min_chunk_size)
    return processor.segment_document(content)
