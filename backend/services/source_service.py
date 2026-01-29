"""源文档处理服务模块"""
from flask import current_app
from .cache_service import get_video_info


class SourceService:
    """源文档处理服务"""
    
    @staticmethod
    def process_source_documents(source_docs, app):
        """处理检索到的源文档，生成引用信息"""
        sources = []
        
        for idx, doc in enumerate(source_docs):
            if hasattr(doc, "metadata"):
                # 检查是否为视频源
                if "video_id" in doc.metadata:
                    source_item = SourceService._process_video_source(doc, idx, app)
                # 检查是否为文档源
                elif "document_id" in doc.metadata:
                    source_item = SourceService._process_document_source(doc, idx, app)
                else:
                    # 兼容旧格式或未知类型
                    source_item = SourceService._process_legacy_source(doc, idx, app)
                
                if source_item:
                    sources.append(source_item)
        
        return sources
    
    @staticmethod
    def _process_video_source(doc, idx, app):
        """处理视频类型的源文档"""
        time_point = doc.metadata.get("time_point", 0)
        doc_video_id = doc.metadata.get("video_id")
        
        with app.app_context():
            video_title, this_course_id = get_video_info(doc_video_id)
        
        return {
            "index": idx + 1,
            "type": "video",
            "video_id": str(doc_video_id),
            "video_title": video_title,
            "course_id": str(this_course_id) if this_course_id else None,
            "course_title": doc.metadata.get("course_title", ""),
            "time_point": time_point,
            "time_formatted": f"{int(time_point // 60):02d}:{int(time_point % 60):02d}",
            "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
        }
    
    @staticmethod
    def _process_document_source(doc, idx, app):
        """处理文档类型的源文档"""
        document_id = doc.metadata.get("document_id")
        segment_id = doc.metadata.get("segment_id")
        segment_number = doc.metadata.get("segment_number", 0)
        segment_type = doc.metadata.get("segment_type", "paragraph")
        segment_title = doc.metadata.get("title", "")
        page_number = doc.metadata.get("page_number", 0)
        
        with app.app_context():
            document_info = SourceService._get_document_info(document_id)
        
        return {
            "index": idx + 1,
            "type": "document",
            "document_id": str(document_id),
            "document_title": document_info.get("title", "未知文档"),
            "course_id": document_info.get("course_id"),
            "course_title": document_info.get("course_title", ""),
            "segment_id": str(segment_id) if segment_id else None,
            "segment_number": segment_number,
            "segment_type": segment_type,
            "segment_title": segment_title,
            "page_number": page_number,
            "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
        }
    
    @staticmethod
    def _process_legacy_source(doc, idx, app):
        """处理旧格式或未知类型的源文档"""
        # 兼容旧的视频格式
        time_point = doc.metadata.get("time_point", 0)
        doc_video_id = doc.metadata.get("video_id")
        
        if doc_video_id:
            with app.app_context():
                video_title, this_course_id = get_video_info(doc_video_id)
            
            return {
                "index": idx + 1,
                "type": "video",
                "video_id": str(doc_video_id),
                "video_title": video_title,
                "course_id": str(this_course_id) if this_course_id else None,
                "course_title": doc.metadata.get("course_title", ""),
                "time_point": time_point,
                "time_formatted": f"{int(time_point // 60):02d}:{int(time_point % 60):02d}",
                "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            }
        
        return None
    
    @staticmethod
    def _get_document_info(document_id):
        """获取文档基本信息"""
        try:
            from models.models import Document
            
            document = Document.query.get(document_id)
            if not document or document.is_deleted:
                return {"title": "未知文档"}
            
            # 获取课程信息
            course_title = ""
            if document.course:
                course_title = document.course.name
            
            return {
                "title": document.title,
                "course_id": str(document.course_id) if document.course_id else None,
                "course_title": course_title,
                "description": document.description or ""
            }
        except Exception as e:
            current_app.logger.error(f"获取文档信息失败: {e}")
            return {"title": "未知文档"}


# 全局源文档服务实例
source_service = SourceService()
