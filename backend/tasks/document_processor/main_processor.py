"""
文档处理主协调器
负责协调文档处理的各个步骤，目前支持Markitdown转换
"""

import os
import traceback
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from models.models import Document, DocumentProcessingTask, DocumentSegment, db
from utils.result import Result
from .markitdown_processor import create_markitdown_processor
from .segment_processor import create_segment_processor
from .summary_processor import process_document_summary_step
from .task_logger import create_document_task_logger


class DocumentMainProcessor:
    """
    文档处理主协调器
    负责协调文档处理的各个步骤
    """

    def __init__(self, document_id: int):
        """
        初始化文档处理器
        
        Args:
            document_id: 文档ID
        """
        self.document_id = document_id
        self.logger = create_document_task_logger(document_id)
        self.markitdown_processor = create_markitdown_processor()
        self.segment_processor = create_segment_processor()
        
        # 当前支持markitdown、segment、vector和summary步骤
        self.available_steps = ['markitdown', 'segment', 'vector', 'summary']
        
        # 任务记录
        self.processing_task = None

    def process_document(self, processing_steps: List[str]) -> Result:
        """
        处理文档
        
        Args:
            processing_steps: 处理步骤列表
            
        Returns:
            Result: 处理结果
        """
        processing_task = None
        try:
            # 获取文档信息
            document = db.session.query(Document).filter_by(id=self.document_id).first()
            if not document:
                return Result.error(f"未找到文档ID: {self.document_id}")

            # 创建处理任务记录
            processing_task = self._create_processing_task(document, processing_steps)
            self.processing_task = processing_task
            # 更新logger的task_id，以便记录到正确的任务日志
            self.logger.task_id = processing_task.task_id

            self.logger.log_info('init', f'开始处理文档: {document.title}', 
                               f'处理步骤: {processing_steps}')

            # 验证处理步骤
            invalid_steps = [step for step in processing_steps if step not in self.available_steps]
            if invalid_steps:
                error_msg = f"不支持的处理步骤: {invalid_steps}, 支持的步骤: {self.available_steps}"
                self.logger.log_error('validation', error_msg)
                if processing_task:
                    self._update_processing_task(processing_task, 'failed', error_msg)
                return Result.error(error_msg)

            # 检查文档文件是否存在
            # 处理文件路径，移除开头的斜杠
            file_path = document.get_local_path()
            if not os.path.exists(file_path):
                error_msg = f"文档文件不存在: {file_path} (原路径: {document.file_url})"
                self.logger.log_error('file_check', error_msg)
                if processing_task:
                    self._update_processing_task(processing_task, 'failed', error_msg)
                return Result.error(error_msg)

            # 更新任务状态为处理中
            if processing_task:
                self._update_processing_task(processing_task, 'processing', f'开始处理 {len(processing_steps)} 个步骤', progress=0.1)

            results = {}
            total_steps = len(processing_steps)
            current_step = 0
            
            # 处理markitdown步骤
            if 'markitdown' in processing_steps:
                current_step += 1
                if processing_task:
                    progress = 0.1 + (current_step - 1) * 0.8 / total_steps
                    self._update_processing_task(processing_task, 'processing', f'正在进行Markitdown转换... ({current_step}/{total_steps})', progress=progress)
                
                markitdown_result = self._process_markitdown_step(document)
                if markitdown_result['code'] != 200:
                    if processing_task:
                        self._update_processing_task(processing_task, 'failed', markitdown_result.get('message', '处理失败'))
                    return markitdown_result
                results['markitdown'] = markitdown_result['data']
            
            # 处理智能分段步骤（需要先有markitdown内容）
            if 'segment' in processing_steps:
                current_step += 1
                if processing_task:
                    progress = 0.1 + (current_step - 1) * 0.8 / total_steps
                    self._update_processing_task(processing_task, 'processing', f'正在进行智能分段... ({current_step}/{total_steps})', progress=progress)
                
                segment_result = self._process_segment_step(document, results)
                if segment_result['code'] != 200:
                    if processing_task:
                        self._update_processing_task(processing_task, 'failed', segment_result.get('message', '分段处理失败'))
                    return segment_result
                results['segment'] = segment_result['data']

            # 处理向量化步骤（需要先有分段数据）
            if 'vector' in processing_steps:
                current_step += 1
                if processing_task:
                    progress = 0.1 + (current_step - 1) * 0.8 / total_steps
                    self._update_processing_task(processing_task, 'processing', f'正在进行向量化处理... ({current_step}/{total_steps})', progress=progress)
                
                vector_result = self._process_vector_step(document, results)
                if vector_result['code'] != 200:
                    if processing_task:
                        self._update_processing_task(processing_task, 'failed', vector_result.get('message', '向量化处理失败'))
                    return vector_result
                results['vector'] = vector_result['data']

            # 处理智能摘要步骤（需要先有分段数据）
            if 'summary' in processing_steps:
                current_step += 1
                if processing_task:
                    progress = 0.1 + (current_step - 1) * 0.8 / total_steps
                    self._update_processing_task(processing_task, 'processing', f'正在生成智能摘要... ({current_step}/{total_steps})', progress=progress)
                
                summary_result = self._process_summary_step(document, results)
                if summary_result['code'] != 200:
                    if processing_task:
                        self._update_processing_task(processing_task, 'failed', summary_result.get('message', '摘要处理失败'))
                    return summary_result
                results['summary'] = summary_result['data']

            # 更新文档状态
            self._update_document_status(document, 'completed', results)

            success_msg = f"文档处理完成，共处理 {len(processing_steps)} 个步骤"
            self.logger.log_success('complete', success_msg)
            
            # 更新任务状态为完成
            if processing_task:
                self._update_processing_task(processing_task, 'completed', success_msg, results)
            
            return Result.success({
                'document_id': self.document_id,
                'document_name': document.title,
                'processing_steps': processing_steps,
                'results': results,
                'message': success_msg,
                'task_id': processing_task.id if processing_task else None
            })

        except Exception as e:
            error_msg = f"文档处理失败: {str(e)}"
            self.logger.log_exception('process', error_msg, e)
            if processing_task:
                self._update_processing_task(processing_task, 'failed', error_msg)
            return Result.error(error_msg)

    def _process_markitdown_step(self, document: Document) -> Result:
        """
        处理Markitdown转换步骤
        
        Args:
            document: 文档对象
            
        Returns:
            Result: 处理结果
        """
        try:
            self.logger.start_step('markitdown', 'Markitdown文档转换')

            # 检查Markitdown处理器是否可用
            if not self.markitdown_processor:
                error_msg = "Markitdown处理器不可用，请检查markitdown库是否正确安装"
                self.logger.fail_step('markitdown', 'Markitdown转换', error_msg)
                return Result.error(error_msg)

            # 获取完整的本地文件路径
            from utils.file_util import get_full_path
            file_path = get_full_path(document.file_url, 'document')

            # 设置输出目录
            output_dir = os.path.join('temp_docs')
            os.makedirs(output_dir, exist_ok=True)

            # 执行markitdown转换
            conversion_result = self.markitdown_processor.convert_to_markdown(
                file_path, 
                output_dir
            )

            if conversion_result['code'] != 200:
                error_msg = conversion_result.get('message', '转换失败')
                self.logger.fail_step('markitdown', 'Markitdown转换', error_msg)
                return Result.error(error_msg)

            markdown_content = conversion_result['data']['markdown_content']
            output_file = conversion_result['data']['output_file']

            # 验证转换结果
            if not self.markitdown_processor.validate_conversion_result(markdown_content):
                error_msg = "转换结果验证失败，内容可能为空或无效"
                self.logger.fail_step('markitdown', 'Markitdown转换', error_msg)
                return Result.error(error_msg)

            # 保存到数据库
            document.markitdown_content = markdown_content
            document.processing_status = 'markitdown_completed'
            db.session.commit()

            self.logger.log_info('markitdown', '已保存Markdown内容到数据库')

            result_data = {
                'markdown_content': markdown_content,
                'content_length': len(markdown_content),
                'output_file': output_file,
                'source_file': file_path
            }

            self.logger.complete_step('markitdown', 'Markitdown转换', {
                'content_length': len(markdown_content),
                'output_file': output_file
            })

            return Result.success(result_data)

        except Exception as e:
            error_msg = f"Markitdown转换失败: {str(e)}"
            self.logger.log_exception('markitdown', error_msg, e)
            return Result.error(error_msg)

    def _process_segment_step(self, document: Document, results: Dict[str, Any]) -> Result:
        """
        处理智能分段步骤
        
        Args:
            document: 文档对象
            results: 之前步骤的处理结果
            
        Returns:
            Result: 处理结果
        """
        try:
            self.logger.start_step('segment', '智能文档分段')

            # 检查分段处理器是否可用
            if not self.segment_processor:
                error_msg = "分段处理器不可用"
                self.logger.fail_step('segment', '智能分段', error_msg)
                return Result.error(error_msg)

            # 获取Markdown内容
            markdown_content = None
            
            # 如果当前流程中有markitdown结果，使用它
            if 'markitdown' in results:
                markdown_content = results['markitdown']['markdown_content']
            # 否则尝试从数据库获取
            elif document.markitdown_content:
                markdown_content = document.markitdown_content
            else:
                error_msg = "未找到Markdown内容，请先完成Markitdown转换"
                self.logger.fail_step('segment', '智能分段', error_msg)
                return Result.error(error_msg)

            if not markdown_content or not markdown_content.strip():
                error_msg = "Markdown内容为空"
                self.logger.fail_step('segment', '智能分段', error_msg)
                return Result.error(error_msg)

            # 执行智能分段
            self.logger.log_info('segment', f'开始对{len(markdown_content)}字符的内容进行分段')
            
            segmentation_result = self.segment_processor.segment_document(markdown_content)

            if segmentation_result['code'] != 200:
                error_msg = segmentation_result.get('message', '分段失败')
                self.logger.fail_step('segment', '智能分段', error_msg)
                return Result.error(error_msg)

            segment_data = segmentation_result['data']
            segments = segment_data['segments']
            statistics = segment_data['statistics']

            # 保存分段结果到数据库
            saved_segments = self._save_segments_to_database(document, segments)
            self.logger.log_info('segment', f'已保存 {len(saved_segments)} 个分段到数据库')

            result_data = {
                'segments': segments,
                'total_segments': statistics['total_segments'],
                'statistics': statistics,
                'original_length': len(markdown_content)
            }

            self.logger.complete_step('segment', '智能分段', {
                'total_segments': statistics['total_segments'],
                'average_length': statistics['average_length'],
                'segment_types': statistics['segment_types']
            })

            return Result.success(result_data)

        except Exception as e:
            error_msg = f"智能分段失败: {str(e)}"
            self.logger.log_exception('segment', error_msg, e)
            return Result.error(error_msg)

    def _process_vector_step(self, document: Document, results: Dict[str, Any]) -> Result:
        """
        处理文档向量化步骤
        
        Args:
            document: 文档对象
            results: 之前步骤的处理结果
            
        Returns:
            Result: 处理结果
        """
        try:
            self.logger.start_step('vector', '文档向量化')

            # 导入向量处理器
            from .vector_processor import process_document_vector_step

            # 检查是否有分段数据
            segments_available = False
            
            # 如果当前流程中有分段结果，可以直接处理
            if 'segment' in results:
                segments_available = True
                self.logger.log_info('vector', '使用当前流程的分段数据')
            else:
                # 否则检查数据库中是否有分段数据
                from models.models import DocumentSegment
                segment_count = DocumentSegment.query.filter_by(document_id=document.id).count()
                if segment_count > 0:
                    segments_available = True
                    self.logger.log_info('vector', f'发现数据库中的分段数据: {segment_count} 个分段')

            if not segments_available:
                error_msg = "未找到分段数据，请先完成文档分段步骤"
                self.logger.fail_step('vector', '文档向量化', error_msg)
                return Result.error(error_msg)

            # 执行向量化处理
            self.logger.log_info('vector', '开始构建文档向量索引')
            
            vector_result = process_document_vector_step(document.id)

            if not vector_result['success']:
                error_msg = vector_result.get('message', '向量化失败')
                self.logger.fail_step('vector', '文档向量化', error_msg)
                return Result.error(error_msg)

            result_data = {
                'index_path': vector_result.get('index_path', ''),
                'embedding_model': vector_result.get('embedding_model', 'Pro/BAAI/bge-m3'),
                'total_vectors': vector_result.get('total_vectors', 0),
                'action': vector_result.get('action', 'unknown')
            }

            self.logger.complete_step('vector', '文档向量化', {
                'total_vectors': vector_result.get('total_vectors', 0),
                'index_path': vector_result.get('index_path', ''),
                'action': vector_result.get('action', 'unknown')
            })

            return Result.success(result_data)

        except Exception as e:
            error_msg = f"文档向量化失败: {str(e)}"
            self.logger.log_exception('vector', error_msg, e)
            return Result.error(error_msg)

    def _process_summary_step(self, document: Document, results: Dict[str, Any]) -> Result:
        """
        处理智能摘要步骤
        
        Args:
            document: 文档对象
            results: 之前处理步骤的结果
            
        Returns:
            Result: 处理结果
        """
        try:
            self.logger.start_step('summary', '智能文档摘要')

            # 检查依赖：必须先完成分段处理
            if 'segment' not in results:
                # 检查数据库中是否有分段数据
                from models.models import DocumentSegment
                existing_segments = db.session.query(DocumentSegment).filter_by(document_id=document.id).count()
                if existing_segments == 0:
                    error_msg = "智能摘要需要先完成分段处理"
                    self.logger.fail_step('summary', '智能摘要', error_msg)
                    return Result.error(error_msg)
                else:
                    self.logger.log_info('summary', '使用数据库中的现有分段数据')

            # 调用摘要处理器，传递当前任务的task_id
            summary_result = process_document_summary_step(document.id, False,self.logger.task_id)
            
            if not summary_result['success']:
                error_msg = summary_result.get('message', '摘要生成失败')
                self.logger.fail_step('summary', '智能摘要', error_msg)
                return Result.error(error_msg)

            # 更新文档状态
            document.processing_status = 'summarized'
            db.session.commit()

            result_data = {
                'summary_length': summary_result.get('summary_length', 0),
                'keywords_count': summary_result.get('keywords_count', 0),
                'main_points_count': summary_result.get('main_points_count', 0),
                'sections_count': summary_result.get('sections_count', 0),
                'difficulty_level': summary_result.get('difficulty_level', 3),
                'action': summary_result.get('action', 'created')
            }

            self.logger.complete_step('summary', '智能摘要', result_data)

            return Result.success(result_data)

        except Exception as e:
            error_msg = f"智能摘要处理失败: {str(e)}"
            self.logger.log_exception('summary', error_msg, e)
            return Result.error(error_msg)

    def _save_segments_to_database(self, document: Document, segments: List[Dict[str, Any]]) -> List[DocumentSegment]:
        """
        将分段结果保存到数据库
        
        Args:
            document: 文档对象
            segments: 分段列表
            
        Returns:
            List[DocumentSegment]: 保存的分段对象列表
        """
        try:
            # 清除该文档的旧分段记录
            db.session.query(DocumentSegment).filter_by(document_id=document.id).delete()
            
            saved_segments = []
            
            for i, segment_data in enumerate(segments, 1):
                # 提取段落标题（如果是标题类型）
                title = None
                if segment_data['segment_type'] == 'heading':
                    # 去掉Markdown标题标记
                    content = segment_data['content']
                    if content.startswith('#'):
                        title = content.lstrip('#').strip()
                
                # 创建数据库记录
                segment = DocumentSegment(
                    document_id=document.id,
                    segment_number=i,
                    title=title,
                    content=segment_data['content'],
                    segment_type=segment_data['segment_type'],
                    page_number=None  # 当前没有页码信息，可以后续扩展
                )
                
                db.session.add(segment)
                saved_segments.append(segment)
            
            # 提交事务
            db.session.commit()
            
            self.logger.log_info('segment_save', f'成功保存 {len(saved_segments)} 个分段', 
                               f'文档ID: {document.id}')
            
            return saved_segments
            
        except Exception as e:
            db.session.rollback()
            self.logger.log_exception('segment_save', '保存分段到数据库失败', e)
            raise

    def _update_document_status(self, document: Document, status: str, results: Dict[str, Any]):
        """
        更新文档处理状态
        
        Args:
            document: 文档对象
            status: 处理状态
            results: 处理结果
        """
        try:
            # 根据完成的处理步骤确定状态
            if status == 'completed':
                if 'summary' in results:
                    document.processing_status = 'summarized'
                elif 'vector' in results:
                    document.processing_status = 'vectorized'
                elif 'segment' in results:
                    document.processing_status = 'segmented'
                elif 'markitdown' in results:
                    document.processing_status = 'markitdown_completed'
                else:
                    document.processing_status = 'completed'
            else:
                document.processing_status = status
            
            # 如果有markitdown结果，更新相应字段
            if 'markitdown' in results:
                document.markitdown_content = results['markitdown']['markdown_content']

            db.session.commit()
            
            self.logger.log_info('status_update', f'文档状态已更新为: {document.processing_status}')
            
        except Exception as e:
            self.logger.log_exception('status_update', '更新文档状态失败', e)

    def _create_processing_task(self, document: Document, processing_steps: List[str]) -> DocumentProcessingTask:
        """
        创建文档处理任务记录
        
        Args:
            document: 文档对象
            processing_steps: 处理步骤列表
            
        Returns:
            DocumentProcessingTask: 创建的任务对象
        """
        try:
            # 为每个步骤创建单独的任务记录，或创建一个综合任务
            # 根据现有数据库结构，processing_type只能是单个类型
            # 我们创建一个综合任务，类型为主要步骤
            main_type = processing_steps[0] if processing_steps else 'markitdown'
            task_uuid = str(uuid.uuid4())
            
            task = DocumentProcessingTask(
                id=task_uuid,
                document_id=document.id,
                task_id=f'doc_proc_{task_uuid[:8]}',
                status='pending',
                processing_type=main_type,  # 使用第一个处理步骤作为主类型
                progress=0.0,
                start_time=datetime.now()
            )
            
            db.session.add(task)
            db.session.commit()
            
            self.logger.log_info('task_created', f'已创建处理任务: {task.id}', 
                               f'处理步骤: {processing_steps}, 主类型: {main_type}')
            
            return task
            
        except Exception as e:
            self.logger.log_exception('task_creation', '创建处理任务失败', e)
            raise

    def _update_processing_task(self, task: DocumentProcessingTask, status: str, 
                              message: str = None, results: Dict[str, Any] = None, progress: float = None):
        """
        更新文档处理任务状态
        
        Args:
            task: 任务对象
            status: 新状态
            message: 状态消息
            results: 处理结果
            progress: 自定义进度值（0.0-1.0），如果不提供则使用默认值
        """
        try:
            task.status = status
            
            if message and status == 'failed':
                task.error_message = message
            elif status != 'failed':
                task.error_message = None
                
            # 更新进度
            if progress is not None:
                task.progress = max(0.0, min(1.0, progress))  # 确保进度在0-1之间
            elif status == 'pending':
                task.progress = 0.0
            elif status == 'processing':
                task.progress = 0.5
            elif status == 'completed':
                task.progress = 1.0
                task.end_time = datetime.now()
            elif status == 'failed':
                task.end_time = datetime.now()
                
            db.session.commit()
            
            self.logger.log_info('task_updated', f'任务状态已更新: {task.id} -> {status} (进度: {task.progress:.1%})', 
                               message or f'状态变更为: {status}')
            
        except Exception as e:
            self.logger.log_exception('task_update', '更新任务状态失败', e)

    def get_supported_steps(self) -> List[str]:
        """
        获取支持的处理步骤
        
        Returns:
            List[str]: 支持的步骤列表
        """
        return self.available_steps.copy()

    def check_prerequisites(self) -> Dict[str, bool]:
        """
        检查处理前提条件
        
        Returns:
            Dict[str, bool]: 各个组件的可用状态
        """
        return {
            'markitdown_processor': self.markitdown_processor is not None,
            'document_exists': db.session.query(Document).filter_by(id=self.document_id).first() is not None
        }


def create_document_processor(document_id: int) -> DocumentMainProcessor:
    """
    创建文档处理器实例
    
    Args:
        document_id: 文档ID
        
    Returns:
        DocumentMainProcessor: 文档处理器实例
    """
    return DocumentMainProcessor(document_id)


def process_document_async(document_id: int, processing_steps: List[str]) -> Result:
    """
    异步处理文档的入口函数
    
    Args:
        document_id: 文档ID
        processing_steps: 处理步骤列表
        
    Returns:
        Result: 处理结果
    """
    processor = create_document_processor(document_id)
    return processor.process_document(processing_steps)


def check_document_processing_steps_status(document_id: int) -> Dict[str, bool]:
    """
    检查文档各处理步骤的完成状态
    
    Args:
        document_id: 文档ID
        
    Returns:
        dict: 各步骤的完成状态
        {
            "markitdown": bool,  # Markitdown转换是否完成
            "segment": bool,     # 智能分段是否完成
            "vector": bool,      # 向量化处理是否完成
            "summary": bool      # 智能摘要是否完成
        }
    """
    try:
        from models.models import DocumentSegment, DocumentVectorIndex, DocumentSummary
        
        status = {
            "markitdown": False,
            "segment": False,
            "vector": False,
            "summary": False
        }
        
        # 检查Markitdown转换 - 通过检查是否有分段来判断
        # 因为Markitdown转换的结果通常会进一步处理为分段
        
        # 检查智能分段
        segments_count = DocumentSegment.query.filter_by(document_id=document_id).count()
        if segments_count > 0:
            status["markitdown"] = True  # 有分段说明Markitdown已完成
            status["segment"] = True
        
        # 检查向量化处理
        vector_index = DocumentVectorIndex.query.filter_by(document_id=document_id).first()
        status["vector"] = vector_index is not None
        
        # 检查智能摘要
        summary = DocumentSummary.query.filter_by(document_id=document_id).first()
        status["summary"] = summary is not None
        
        return status
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"检查文档处理状态失败: {str(e)}")
        return {
            "markitdown": False,
            "segment": False,
            "vector": False,
            "summary": False
        }


def get_uncompleted_document_processing_steps(document_id: int) -> List[str]:
    """
    获取文档未完成的处理步骤
    
    Args:
        document_id: 文档ID
        
    Returns:
        list: 未完成的步骤列表，例如 ["markitdown", "segment"]
    """
    try:
        status = check_document_processing_steps_status(document_id)
        uncompleted_steps = []
        
        # 按照处理顺序添加未完成的步骤
        step_order = ["markitdown", "segment", "vector", "summary"]
        for step in step_order:
            if not status.get(step, False):
                uncompleted_steps.append(step)
                
        return uncompleted_steps
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"获取文档未完成处理步骤失败: {str(e)}")
        # 如果出错，返回所有步骤
        return ["markitdown", "segment", "vector", "summary"]


def get_all_document_processing_steps() -> List[str]:
    """
    获取所有文档处理步骤的列表
    
    Returns:
        list: 所有处理步骤列表
    """
    return ["markitdown", "segment", "vector", "summary"]