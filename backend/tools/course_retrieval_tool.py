"""课程检索工具"""

import json
import hashlib
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from config.agent_config import AgentConfig
from services.cache_service import get_course_info, get_course_keywords
from services.redis_service import redis_service
from .base_tool import BaseTool
from .db_utils import find_entity_by_name
from .query_utils import QueryEnhancer
from .result_formatter import ResultFormatter


class CourseSearchInput(BaseModel):
    """课程搜索工具的输入参数模型"""
    course_id_or_course_name: str = Field(description="课程ID或课程名称")
    query: str = Field(description="搜索查询内容")


class CourseRetrievalTool(BaseTool):
    """课程检索工具"""
    
    name = "course_search"
    description = "在指定课程的教学内容中搜索相关信息。需要提供课程ID/模糊的课程名称和搜索查询内容。支持动态指定任何课程。\n回答的时候，优先选择带有屏幕内容和教师口述的教学片段。如果这些片段都不相关，选择其他片段。"
    
    def __init__(self, retriever_service, user_id: str = None):
        super().__init__(user_id=user_id)
        self.retriever_service = retriever_service
        self._course_context_cache = {}  # 缓存多个课程的上下文信息
        
    def get_display_info(self) -> Dict[str, Any]:
        """获取前端展示信息"""
        return {
            "tool_name": "课程内容检索",
            "tool_icon": "mdi-book-search",
            "tool_color": "info",
            "description": "在指定课程的教学内容中搜索相关信息，必须通过ID或名称指定课程",
            "context": {
                "supports_dynamic_course": True,
                "supports_query": True,
                "requires_course_specification": True
            },
            "status_message": "准备检索指定课程中的相关内容..."
        }
    
    def _find_course_by_name(self, name: str) -> Optional[str]:
        """通过名称查找课程ID"""
        try:
            from models.models import Course
            return find_entity_by_name(Course, name, lambda c: c.name)
        except Exception as e:
            print(f"[ERROR] 通过名称查找课程失败: {e}")
            return None
    
    def _resolve_course_id(self, course_id_or_course_name: Optional[str]) -> Optional[str]:
        """解析课程标识符，返回课程ID"""
        # 必须提供课程标识符
        if not course_id_or_course_name:
            return None
            
        # 先尝试作为课程ID直接查询
        course_name = get_course_info(course_id_or_course_name)
        if course_name:
            return course_id_or_course_name
            
        # 如果不是有效ID，尝试作为名称查找
        course_id = self._find_course_by_name(course_id_or_course_name)
        return course_id
        
    def _get_course_context(self, course_id: str):
        """获取课程上下文信息"""
        if course_id not in self._course_context_cache:
            course_name = get_course_info(course_id)
            course_keywords = get_course_keywords(course_id, limit=15)
            
            context = {'name': course_name, 'keywords': {}}
            if course_keywords:
                # 按类别分组知识点
                for kw in course_keywords:
                    category = kw.get('category', 'other')
                    if category not in context['keywords']:
                        context['keywords'][category] = []
                    context['keywords'][category].append(kw['name'])
                    
            self._course_context_cache[course_id] = context
        return self._course_context_cache[course_id]
    
    def _get_course_index(self, course_id: str):
        """获取课程索引 - 包含视频和文档索引"""
        try:
            from services.index_service import index_service
            
            def get_index():
                # 获取视频索引
                video_index, video_error = index_service.get_course_video_index(course_id)
                # 获取文档索引
                document_index, document_error = index_service.get_course_document_index(course_id)
                
                # 如果两个索引都不存在，返回错误
                if video_index is None and document_index is None:
                    return None, f"课程 {course_id} 没有可用的视频或文档索引"
                
                # 如果只有一个索引存在，直接返回
                if video_index is None:
                    return document_index, None
                if document_index is None:
                    return video_index, None
                
                # 如果两个索引都存在，合并它们
                try:
                    video_index.merge_from(document_index)
                    return video_index, None
                except Exception as merge_error:
                    print(f"[WARNING] 合并视频和文档索引失败: {merge_error}，使用视频索引")
                    return video_index, None
            
            course_index, error = self._execute_with_app_context(get_index)
            if error:
                print(f"[ERROR] 获取课程索引失败: {error}")
                return None
            return course_index
        except Exception as e:
            print(f"[ERROR] 获取课程索引时出现异常: {e}")
            return None
        
    def _generate_cache_key(self, user_id: str, course_id: str, query: str) -> str:
        """生成缓存键"""
        # 使用用户ID+课程ID+查询内容生成缓存键
        cache_content = f"{user_id}_{course_id}_{query}_1"
        # 使用MD5哈希避免键过长
        cache_hash = hashlib.md5(cache_content.encode('utf-8')).hexdigest()
        return f"course_search:{cache_hash}"
    
    def _get_cached_result(self, cache_key: str) -> Optional[list]:
        """获取缓存的搜索结果"""
        try:
            cached_data = redis_service.get_with_metadata(cache_key)
            if cached_data:
                print(f"[CACHE] 课程检索缓存命中: {cache_key}")
                return cached_data['value']
            return None
        except Exception as e:
            print(f"[CACHE] 获取课程检索缓存失败: {e}")
            return None
    
    def _set_cached_result(self, cache_key: str, docs_with_indices: list, course_name: str, query: str) -> bool:
        """设置缓存的搜索结果"""
        try:
            metadata = {
                'user_id': self.user_id,
                'course_name': course_name,
                'query': query[:100],  # 限制查询长度
                'cache_type': 'course_search_docs_beta'
            }
            # 缓存1小时 = 3600秒
            success = redis_service.set_with_metadata(cache_key, docs_with_indices, 3600, metadata)
            if success:
                print(f"[CACHE] 课程检索文档已缓存: {cache_key}")
            return success
        except Exception as e:
            print(f"[CACHE] 设置课程检索缓存失败: {e}")
            return False

    def search(self, course_id_or_course_name: str, query: str) -> str:
        """高级课程搜索，支持多参数"""
        try:
            max_docs = AgentConfig.get_tool_config("course_search").get("max_docs", 6)
            print(f"[FLOW] CourseRetrievalTool.search 开始执行")
            print(f"[FLOW] 接收到的参数 - course_id_or_course_name: {course_id_or_course_name}, query: {query}")
            print(f"[FLOW] 用户ID: {self.user_id}")
            display_info = self.get_display_info()
            self._notify_tool_start(display_info)
            # 解析课程ID
            target_course_id = self._resolve_course_id(course_id_or_course_name)
            if not target_course_id:
                error_msg = f"请提供有效的课程ID或课程名称。当前输入: {course_id_or_course_name or '空'}"
                print(f"[FLOW] {error_msg}")
                self._notify_tool_result({
                    "success": False,
                    "message": error_msg,
                    "documents_count": 0
                })
                return error_msg
            
            # 检查用户权限
            if not self.has_course_access(target_course_id):
                error_msg = f"您没有访问课程 '{course_id_or_course_name}' 的权限"
                print(f"[FLOW] 权限检查失败: {error_msg}")
                self._notify_tool_result({
                    "success": False,
                    "message": error_msg,
                    "documents_count": 0
                })
                return error_msg
            
            # 生成缓存键并检查缓存
            query_cache_key = self._generate_cache_key(self.user_id, target_course_id, query)
            cached_docs = self._get_cached_result(query_cache_key)
            if cached_docs:
                print(f"[FLOW] 返回缓存的课程检索结果")
                # 获取课程上下文用于格式化
                context = self._get_course_context(target_course_id)
                core_concepts = context['keywords'].get('core_concept', [])
                docs_with_indices = self.store_docs(cached_docs, max_docs)
                result_text = ResultFormatter.format_course_result(
                    docs_with_indices, 
                    context['name'], 
                    query,
                    core_concepts
                )
                # 通知前端缓存命中
                self._notify_tool_result({
                    "success": True,
                    "message": f"在课程《{context['name']}》中找到 {len(cached_docs)} 个相关片段",
                    "documents_count": len(cached_docs),
                    "course_name": context['name'],
                    "core_concepts": context['keywords'].get('core_concept', [])[:3]
                })
                return result_text
            
            print(f"[FLOW] 解析到的课程ID: {target_course_id}")
            print(f"[FLOW] 当前retrieved_docs数量: {len(self.retrieved_docs)}")
            
            # 获取课程上下文
            context = self._get_course_context(target_course_id)
            
            # 更新展示信息
            display_info = self.get_display_info()
            display_info["status_message"] = f"正在检索课程《{context.get('name', '未知课程')}》中的相关内容..."

            
            # 获取课程索引 - 工具层自己获取索引
            course_index = self._get_course_index(target_course_id)
            if not course_index:
                error_msg = f"无法获取课程《{context['name']}》的索引"
                print(f"[FLOW] {error_msg}")
                self._notify_tool_result({
                    "success": False,
                    "message": error_msg,
                    "documents_count": 0
                })
                return error_msg
            
            from services.cache_service import cache_service
            # 使用检索器搜索
            cache_key=cache_service.get_course_cache_key(target_course_id)
            retriever = self.retriever_service.create_ensemble_retriever(course_index,cache_key)
            docs = retriever.get_relevant_documents(query)
            
            print(f"[FLOW] 检索器返回了 {len(docs)} 个文档")
            
            if not docs:
                print(f"[FLOW] CourseRetrievalTool: 未找到相关文档，返回空结果")
                self._notify_tool_result({
                    "success": False,
                    "message": f"在课程《{context['name']}》中未找到相关内容",
                    "documents_count": 0
                })
                return f"在课程《{context['name']}》中未找到相关内容。"
            
            # 存储检索到的文档并分配全局序号
            
            docs_with_indices = self.store_docs(docs, max_docs)
                
            # 格式化检索结果
            core_concepts = context['keywords'].get('core_concept', [])
            result_text = ResultFormatter.format_course_result(
                docs_with_indices, 
                context['name'], 
                query,
                core_concepts
            )
            
            # 通知前端检索成功
            self._notify_tool_result({
                "success": True,
                "message": f"在课程《{context['name']}》中找到 {len(docs_with_indices)} 个相关片段",
                "documents_count": len(docs_with_indices),
                "course_name": context['name'],
                "core_concepts": context['keywords'].get('core_concept', [])[:3]
            })
            
            # 缓存搜索结果
            self._set_cached_result(query_cache_key, docs, context['name'], query)
                
            print(f"[FLOW] CourseRetrievalTool 执行完成，返回结果长度: {len(result_text)}")
            return result_text
            
        except Exception as e:
            print(f"[FLOW] CourseRetrievalTool 执行出错: {str(e)}")
            import traceback
            traceback.print_exc()
            self._notify_tool_result({
                "success": False,
                "message": f"检索过程中出现错误: {str(e)}",
                "documents_count": 0
            })
            return f"检索过程中出现错误: {str(e)}"
