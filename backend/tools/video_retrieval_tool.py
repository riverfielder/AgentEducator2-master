"""视频检索工具"""

import json
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from config.agent_config import AgentConfig
from services.cache_service import get_video_info, get_video_keywords, get_video_summary
from .base_tool import BaseTool
from .db_utils import find_entity_by_name
from .query_utils import QueryEnhancer
from .result_formatter import ResultFormatter


class VideoSearchInput(BaseModel):
    """视频搜索工具的输入参数模型"""
    video_identifier: str = Field(description="视频ID或视频标题")
    query: str = Field(description="搜索查询内容")


class VideoRetrievalTool(BaseTool):
    """视频检索工具"""
    
    name = "video_search"
    description = "在指定视频的教学内容中搜索相关信息。需要提供视频ID/标题和搜索查询内容。支持动态指定任何视频。"
    
    def __init__(self, retriever_service, user_id: str = None):
        super().__init__(user_id=user_id)
        self.retriever_service = retriever_service
        self._video_context_cache = {}  # 缓存多个视频的上下文信息
        
    def get_display_info(self) -> Dict[str, Any]:
        """获取前端展示信息"""
        return {
            "tool_name": "视频内容检索",
            "tool_icon": "mdi-video-box",
            "tool_color": "primary",
            "description": "在指定视频的教学内容中搜索相关信息，必须通过ID或标题指定视频",
            "context": {
                "supports_dynamic_video": True,
                "supports_query": True,
                "requires_video_specification": True
            },
            "status_message": "准备检索指定视频中的相关内容..."
        }
    
    def _find_video_by_title(self, title: str) -> Optional[str]:
        """通过标题查找视频ID"""
        try:
            from models.models import Video
            return find_entity_by_name(Video, title, lambda v: v.title)
        except Exception as e:
            print(f"[ERROR] 通过标题查找视频失败: {e}")
            return None
    
    def _resolve_video_id(self, video_identifier: Optional[str]) -> Optional[str]:
        """解析视频标识符，返回视频ID"""
        # 必须提供视频标识符
        if not video_identifier:
            return None
            
        # 先尝试作为视频ID直接查询
        video_title, _ = get_video_info(video_identifier)
        if video_title:
            return video_identifier
            
        # 如果不是有效ID，尝试作为标题查找
        video_id = self._find_video_by_title(video_identifier)
        return video_id
        
    def _get_video_context(self, video_id: str):
        """获取视频上下文信息"""
        if video_id not in self._video_context_cache:
            video_title, video_course_id = get_video_info(video_id)
            video_keywords = get_video_keywords(video_id, limit=10)
            video_summary = get_video_summary(video_id)
            
            self._video_context_cache[video_id] = {
                'title': video_title,
                'course_id': video_course_id,
                'keywords': [kw['name'] for kw in video_keywords] if video_keywords else [],
                'summary': video_summary
            }
        return self._video_context_cache[video_id]

    def _get_video_index(self, video_id: str):
        """获取视频索引 - 移植自原来的index_service逻辑"""
        try:
            from services.index_service import index_service
            
            def get_index():
                return index_service.get_video_index(video_id)
            
            video_index, error = self._execute_with_app_context(get_index)
            if error:
                print(f"[ERROR] 获取视频索引失败: {error}")
                return None
            return video_index
        except Exception as e:
            print(f"[ERROR] 获取视频索引时出现异常: {e}")
            return None

    def search(self, video_identifier: str, query: str) -> str:
        """高级视频搜索，支持多参数"""
        try:
            print(f"[FLOW] VideoRetrievalTool.search 开始执行")
            print(f"[FLOW] 接收到的参数 - video_identifier: {video_identifier}, query: {query}")
            print(f"[FLOW] 用户ID: {self.user_id}")
            
            # 解析视频ID
            target_video_id = self._resolve_video_id(video_identifier)
            if not target_video_id:
                error_msg = f"请提供有效的视频ID或视频标题。当前输入: {video_identifier or '空'}"
                print(f"[FLOW] {error_msg}")
                self._notify_tool_result({
                    "success": False,
                    "message": error_msg,
                    "documents_count": 0
                })
                return error_msg
            
            # 检查用户权限 - 通过视频所属课程验证
            def get_video_course():
                from models.models import Video
                video = Video.query.filter_by(id=target_video_id, is_deleted=False).first()
                return str(video.course_id) if video else None
            
            video_course_id = self._execute_with_app_context(get_video_course)
            if not video_course_id or not self.has_course_access(video_course_id):
                error_msg = f"您没有访问视频 '{video_identifier}' 的权限"
                print(f"[FLOW] 权限检查失败: {error_msg}")
                self._notify_tool_result({
                    "success": False,
                    "message": error_msg,
                    "documents_count": 0
                })
                return error_msg
            
            print(f"[FLOW] 解析到的视频ID: {target_video_id}")
            print(f"[FLOW] 当前retrieved_docs数量: {len(self.retrieved_docs)}")
            
            # 获取视频上下文
            context = self._get_video_context(target_video_id)
            
            # 更新展示信息
            display_info = self.get_display_info()
            display_info["status_message"] = f"正在检索视频《{context.get('title', '未知视频')}》中的相关内容..."
            self._notify_tool_start(display_info)
            
            # 获取视频索引 - 工具层自己获取索引
            video_index = self._get_video_index(target_video_id)
            if not video_index:
                error_msg = f"无法获取视频《{context['title']}》的索引"
                print(f"[FLOW] {error_msg}")
                self._notify_tool_result({
                    "success": False,
                    "message": error_msg,
                    "documents_count": 0
                })
                return error_msg
            
            # 构建增强查询
            #enhanced_query = QueryEnhancer.build_context_query(
            #    query, 
            #    context['keywords'], 
            #    max_keywords=5
            #)
                
            # 使用检索器搜索
            retriever = self.retriever_service.create_ensemble_retriever(video_index)
            docs = retriever.get_relevant_documents(query)
            
            print(f"[FLOW] 检索器返回了 {len(docs)} 个文档")
            
            if not docs:
                print(f"[FLOW] VideoRetrievalTool: 未找到相关文档，返回空结果")
                self._notify_tool_result({
                    "success": False,
                    "message": f"在视频《{context['title']}》中未找到相关内容",
                    "documents_count": 0
                })
                return f"在视频《{context['title']}》中未找到相关内容。"
            
            # 存储检索到的文档并分配全局序号
            max_docs = AgentConfig.get_tool_config("video_search").get("max_docs", 5)
            docs_with_indices = self.store_docs(docs, max_docs)
                
            # 格式化检索结果
            result_text = ResultFormatter.format_video_result(
                docs_with_indices, 
                context['title'], 
                query
            )
            
            # 通知前端检索成功
            self._notify_tool_result({
                "success": True,
                "message": f"在视频《{context['title']}》中找到 {len(docs_with_indices)} 个相关片段",
                "documents_count": len(docs_with_indices),
                "video_title": context['title'],
                "video_id": target_video_id,
                "query_used": query or ""
            })
                
            print(f"[FLOW] VideoRetrievalTool.search 执行完成，返回结果长度: {len(result_text)}")
            return result_text
            
        except Exception as e:
            print(f"[FLOW] VideoRetrievalTool.search 执行出错: {str(e)}")
            import traceback
            traceback.print_exc()
            self._notify_tool_result({
                "success": False,
                "message": f"检索过程中出现错误: {str(e)}",
                "documents_count": 0
            })
            return f"检索过程中出现错误: {str(e)}"
