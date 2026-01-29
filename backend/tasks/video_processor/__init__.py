"""
视频处理器模块包
包含各种视频处理相关的功能模块
"""

from .keyframe_extractor import extract_keyframes, is_significant_change
from .ocr_processor import OCRProcessor
from .asr_processor import ASRProcessor
from .vector_indexer import build_vector_index, check_vector_index_exists
from .summary_generator import generate_video_summary, generate_section_summary, group_keyframes_into_sections
from .cache_manager import get_section_cache_key, check_section_cache, save_section_cache
from .db_handler import save_keyframes_to_db, load_keyframes_from_db, check_video_summary_exists, check_video_processing_steps_status, get_uncompleted_processing_steps, get_all_processing_steps
from .task_logger import add_task_log
from .main_processor import process_video_task

__all__ = [
    'extract_keyframes', 
    'is_significant_change', 
    'OCRProcessor',
    'ASRProcessor',
    'build_vector_index',
    'check_vector_index_exists',
    'generate_video_summary',
    'generate_section_summary',
    'group_keyframes_into_sections',
    'get_section_cache_key',
    'check_section_cache',
    'save_section_cache',
    'save_keyframes_to_db',
    'load_keyframes_from_db',
    'check_video_summary_exists',
    'check_video_processing_steps_status',
    'get_uncompleted_processing_steps',
    'get_all_processing_steps',
    'add_task_log',
    'process_video_task'
]