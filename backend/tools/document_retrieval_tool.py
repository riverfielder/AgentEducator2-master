"""
文档检索工具
基于现有的文档向量索引进行检索
"""

from typing import Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from .base_tool import BaseTool as CustomBaseTool
from .query_utils import QueryEnhancer
from .result_formatter import ResultFormatter
from services.retriever_service import RetrieverService
from services.index_service import IndexService
from config.agent_config import AgentConfig


class DocumentSearchInput(BaseModel):
    """文档搜索输入Schema"""
    document_identifier: str = Field(description="文档ID或文档标题")
    query: str = Field(description="搜索查询内容")


class DocumentRetrievalTool(CustomBaseTool):
    """文档检索工具"""
    
    name = "document_search"
    description = """在指定教学文档的内容中搜索相关信息。需要提供文档ID/标题和搜索查询内容。
    使用场景：
    - 用户询问关于特定文档的问题
    - 需要从文档中查找特定信息
    - 理解文档中的概念和知识点
    """
    args_schema: Type[BaseModel] = DocumentSearchInput
    
    def __init__(self, retriever_service: RetrieverService = None, user_id: str = None):
        super().__init__(user_id=user_id)
        self.retriever_service = retriever_service
        self.index_service = IndexService()
        
    def get_display_info(self) -> dict:
        """获取前端展示信息"""
        return {
            "tool_name": "文档内容检索",
            "tool_icon": "mdi-file-document",  # 使用真实存在的文档图标
            "tool_color": "info",
            "description": "在指定文档的内容中搜索相关信息，必须通过ID或标题指定文档",
            "context": {
            "supports_dynamic_document": True,
            "supports_query": True,
            "requires_document_specification": True
            },
            "status_message": "准备检索指定文档中的相关内容..."
        }
        
    def _run(self, document_identifier: str, query: str) -> str:
        """
        LangChain工具接口方法
        
        Args:
            document_identifier: 文档ID或标题
            query: 搜索查询
            
        Returns:
            str: 格式化的搜索结果
        """
        return self.search_document(document_identifier, query)
    
    def search(self, document_identifier: str, query: str) -> str:
        """
        BaseTool抽象方法实现
        
        Args:
            query: 搜索查询（应包含文档标识和查询内容）
            
        Returns:
            str: 格式化的搜索结果
        """
        """
        在文档中搜索相关内容
        
        Args:
            document_identifier: 文档ID或标题
            query: 搜索查询
            
        Returns:
            str: 格式化的搜索结果
        """
        try:
            print(f"[FLOW] DocumentRetrievalTool 开始执行")
            print(f"[FLOW] 文档标识: {document_identifier}")
            print(f"[FLOW] 查询: {query}")
            print(f"[FLOW] 用户ID: {self.user_id}")
            
            # 确定文档ID
            document_id = self._resolve_document_id(document_identifier)
            if not document_id:
                error_msg = f"请提供有效的文档ID或文档标题。当前输入: {document_identifier or '空'}"
                print(f"[FLOW] {error_msg}")
                self._notify_tool_result({
                    "success": False,
                    "message": error_msg,
                    "documents_count": 0
                })
                return error_msg
            
            # 检查用户权限 - 通过文档所属课程验证
            def get_document_course():
                from models.models import Document
                document = Document.query.filter_by(id=document_id, is_deleted=False).first()
                return str(document.course_id) if document else None
            
            document_course_id = self._execute_with_app_context(get_document_course)
            if not document_course_id or not self.has_course_access(document_course_id):
                error_msg = f"您没有访问文档 '{document_identifier}' 的权限"
                print(f"[FLOW] 权限检查失败: {error_msg}")
                self._notify_tool_result({
                    "success": False,
                    "message": error_msg,
                    "documents_count": 0
                })
                return error_msg
            
            # 获取文档信息
            context = self._get_document_context(document_id)
            if not context:
                error_msg = f"无法获取文档《{document_identifier}》的信息"
                print(f"[FLOW] {error_msg}")
                self._notify_tool_result({
                    "success": False,
                    "message": error_msg,
                    "documents_count": 0
                })
                return error_msg
            
            # 更新展示信息
            display_info = self.get_display_info()
            display_info["status_message"] = f"正在检索文档《{context.get('title', '未知文档')}》中的相关内容..."
            self._notify_tool_start(display_info)
            
            # 获取文档向量索引
            def get_index():
                return self.index_service.get_document_index(document_id)
            
            try:
                result = self._execute_with_app_context(get_index)
                # index_service.get_document_index 返回 (index, error) 元组
                if isinstance(result, tuple) and len(result) == 2:
                    document_index, error = result
                else:
                    document_index = result
                    error = None
            except Exception as e:
                document_index = None
                error = str(e)
            
            if error or not document_index:
                error_msg = f"无法获取文档《{context['title']}》的索引: {error or '索引不存在'}"
                print(f"[FLOW] {error_msg}")
                self._notify_tool_result({
                    "success": False,
                    "message": error_msg,
                    "documents_count": 0
                })
                return error_msg
            
            # 构建增强查询（基于文档关键词）
            #enhanced_query = QueryEnhancer.build_context_query(
            #    query,
            #    context.get('keywords', []),
            #    max_keywords=5
            #)
            
            # 使用检索器搜索
            retriever = self.retriever_service.create_ensemble_retriever(document_index)
            docs = retriever.get_relevant_documents(query)
            
            print(f"[FLOW] 检索器返回了 {len(docs)} 个文档片段")
            
            if not docs:
                print(f"[FLOW] DocumentRetrievalTool: 未找到相关文档，返回空结果")
                self._notify_tool_result({
                    "success": False,
                    "message": f"在文档《{context['title']}》中未找到相关内容",
                    "documents_count": 0
                })
                return f"在文档《{context['title']}》中未找到相关内容。"
            
            # 存储检索到的文档并分配全局序号
            max_docs = AgentConfig.get_tool_config("document_search").get("max_docs", 5)
            docs_with_indices = self.store_docs(docs, max_docs)
            
            # 格式化检索结果
            result_text = ResultFormatter.format_document_result(
                docs_with_indices,
                context['title'],
                query
            )
            
            # 通知前端检索成功
            self._notify_tool_result({
                "success": True,
                "message": f"在文档《{context['title']}》中找到 {len(docs_with_indices)} 个相关片段",
                "documents_count": len(docs_with_indices),
                "document_title": context['title'],
                "document_id": document_id,
                "query_used": query or ""
            })
            
            print(f"[FLOW] DocumentRetrievalTool 执行完成，返回结果长度: {len(result_text)}")
            return result_text
            
        except Exception as e:
            error_msg = f"文档检索过程中发生错误: {str(e)}"
            print(f"[FLOW] {error_msg}")
            import traceback
            traceback.print_exc()
            
            self._notify_tool_result({
                "success": False,
                "message": error_msg,
                "documents_count": 0
            })
            
            return error_msg
    

    def _resolve_document_id(self, document_identifier: str) -> str:
        """
        解析文档标识符，返回实际的文档ID
        
        Args:
            document_identifier: 文档ID或标题
            
        Returns:
            str: 文档ID，如果找不到返回None
        """
        # 如果没有提供标识符，返回None
        if not document_identifier:
            return None
            
        # 如果标识符看起来像UUID，直接作为ID使用
        if len(document_identifier) == 36 and '-' in document_identifier:
            return document_identifier
        
        # 否则根据标题查找文档ID - 使用应用程序上下文
        def find_document():
            from models.models import Document
            document = Document.query.filter(
                Document.title.like(f'%{document_identifier}%'),
                Document.is_deleted == False
            ).first()
            return str(document.id) if document else None
        
        try:
            result = self._execute_with_app_context(find_document)
            return result
        except Exception as e:
            print(f"[ERROR] 查找文档失败: {e}")
            return None
    
    def _get_document_context(self, document_id: str) -> dict:
        """
        获取文档上下文信息
        
        Args:
            document_id: 文档ID
            
        Returns:
            dict: 文档上下文信息
        """
        def get_context():
            from models.models import Document, DocumentSummary
            
            # 获取文档基本信息
            document = Document.query.get(document_id)
            if not document or document.is_deleted:
                return None
            
            context = {
                'id': document_id,
                'title': document.title,
                'description': document.description or '',
                'file_type': document.file_type
            }
            
            # 获取文档摘要中的关键词
            summary = DocumentSummary.query.filter_by(document_id=document_id).first()
            if summary and summary.keywords:
                keywords = [kw.strip() for kw in summary.keywords.split(',') if kw.strip()]
                context['keywords'] = keywords
            else:
                context['keywords'] = []
            
            return context
        
        try:
            result = self._execute_with_app_context(get_context)
            return result
        except Exception as e:
            print(f"[FLOW] 获取文档上下文失败: {e}")
            return None