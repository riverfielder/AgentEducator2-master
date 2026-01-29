"""
Markitdown处理器
负责将各种文档格式转换为Markdown格式
"""

import os
import traceback
from pathlib import Path
from typing import Dict, Optional, Any

try:
    from markitdown import MarkItDown
    MARKITDOWN_AVAILABLE = True
except ImportError:
    MARKITDOWN_AVAILABLE = False
    MarkItDown = None

from utils.result import Result


class MarkitdownProcessor:
    """
    Markitdown文档转换处理器
    支持多种文档格式转换为Markdown
    """

    def __init__(self):
        """初始化Markitdown处理器"""
        if not MARKITDOWN_AVAILABLE:
            raise ImportError("markitdown库未安装，请先安装: pip install markitdown")
        
        # 初始化MarkItDown实例
        self.converter = MarkItDown()
        
        # 支持的文件格式
        self.supported_formats = {
            '.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls',
            '.txt', '.md', '.html', '.htm', '.csv', '.json', '.xml',
            '.rtf', '.odt', '.odp', '.ods'
        }

    def is_supported(self, file_path: str) -> bool:
        """
        检查文件格式是否支持
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否支持该格式
        """
        file_extension = Path(file_path).suffix.lower()
        return file_extension in self.supported_formats

    def convert_to_markdown(self, file_path: str, output_dir: Optional[str] = None) -> Result:
        """
        将文档转换为Markdown格式
        
        Args:
            file_path: 输入文件路径
            output_dir: 输出目录，如果不指定则使用默认目录
            
        Returns:
            Result: 转换结果，包含markdown内容和保存路径
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return Result.error(f"文件不存在: {file_path}")
            
            # 检查文件格式是否支持
            if not self.is_supported(file_path):
                file_ext = Path(file_path).suffix
                return Result.error(f"不支持的文件格式: {file_ext}")
            
            # 使用MarkItDown转换文档
            result = self.converter.convert(file_path)
            
            if not result or not result.text_content:
                return Result.error("文档转换失败，未能提取到内容")
            
            markdown_content = result.text_content
            
            # 准备输出路径
            if output_dir is None:
                output_dir = "temp_docs"
            
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成输出文件名
            base_name = Path(file_path).stem
            output_file = os.path.join(output_dir, f"{base_name}_markitdown.md")
            
            # 保存Markdown文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            return Result.success({
                'markdown_content': markdown_content,
                'output_file': output_file,
                'content_length': len(markdown_content),
                'source_file': file_path
            })
            
        except Exception as e:
            error_msg = f"Markitdown转换失败: {str(e)}"
            print(f"[ERROR] {error_msg}")
            print(f"[TRACEBACK] {traceback.format_exc()}")
            return Result.error(error_msg)

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        获取文件基本信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict: 文件信息
        """
        try:
            file_stat = os.stat(file_path)
            return {
                'file_name': os.path.basename(file_path),
                'file_extension': Path(file_path).suffix.lower(),
                'file_size': file_stat.st_size,
                'is_supported': self.is_supported(file_path),
                'absolute_path': os.path.abspath(file_path)
            }
        except Exception as e:
            return {
                'error': f"获取文件信息失败: {str(e)}"
            }

    def validate_conversion_result(self, markdown_content: str, min_length: int = 10) -> bool:
        """
        验证转换结果是否有效
        
        Args:
            markdown_content: Markdown内容
            min_length: 最小长度阈值
            
        Returns:
            bool: 是否有效
        """
        if not markdown_content or not isinstance(markdown_content, str):
            return False
        
        # 去除空白字符后检查长度
        content_stripped = markdown_content.strip()
        if len(content_stripped) < min_length:
            return False
        
        # 检查是否只包含空白字符或无意义的内容
        meaningful_chars = sum(1 for char in content_stripped if char.isalnum())
        if meaningful_chars < min_length // 2:
            return False
        
        return True


def create_markitdown_processor() -> Optional[MarkitdownProcessor]:
    """
    创建Markitdown处理器实例
    
    Returns:
        MarkitdownProcessor: 处理器实例，如果创建失败则返回None
    """
    try:
        return MarkitdownProcessor()
    except ImportError as e:
        print(f"[WARNING] 无法创建Markitdown处理器: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] 创建Markitdown处理器时发生错误: {e}")
        return None 