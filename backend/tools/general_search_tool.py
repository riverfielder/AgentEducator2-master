"""通用搜索工具"""

import hashlib
from typing import Dict, Any, Optional
from config.agent_config import AgentConfig
from services.redis_service import redis_service
from .base_tool import BaseTool
from .result_formatter import ResultFormatter


class GeneralSearchTool(BaseTool):
    """通用搜索工具 - 在所有课程的所有视频索引中搜索"""
    
    name = "general_search"
    description = "在所有课程的所有教学内容中进行全局搜索。当用户询问的问题可能涉及多个课程或需要广泛搜索时使用此工具。"
    
    def __init__(self, retriever_service, user_id: str = None):
        super().__init__(user_id=user_id)
        self.retriever_service = retriever_service
    
    def get_display_info(self) -> Dict[str, Any]:
        """获取前端展示信息"""
        return {
            "tool_name": "全局内容检索",
            "tool_icon": "mdi-magnify",
            "tool_color": "success",
            "description": "在所有课程的所有教学内容中搜索相关信息，提供最全面的搜索结果",
            "context": {
                "search_scope": "所有课程的所有视频内容"
            },
            "status_message": "正在全局搜索所有教学内容..."
        }
    
    def _get_search_index(self):
        """获取全局搜索索引 - 根据用户权限过滤课程"""
        try:
            from services.index_service import index_service
            
            # 使用权限过滤后的课程ID列表
            accessible_course_ids = list(self.accessible_courses)
            print(f"[FLOW] 用户有权限访问 {len(accessible_course_ids)} 个课程")
            
            if not accessible_course_ids:
                print("[FLOW] 没有可访问的课程，返回空索引")
                return None
            
            # 合并所有可访问课程的索引
            def merge_indices():
                return index_service.merge_course_indices(accessible_course_ids)
            
            merged_index, error = self._execute_with_app_context(merge_indices)
            if error:
                print(f"[ERROR] 合并课程索引失败: {error}")
                return None
            
            if merged_index:
                print(f"[FLOW] 成功创建全局合并索引")
                return merged_index
            else:
                print(f"[ERROR] 创建全局合并索引失败")
                return None
            
        except Exception as e:
            print(f"[ERROR] 获取全局搜索索引时出现异常: {e}")
            return None

    def _generate_cache_key(self, user_id: str, query: str) -> str:
        """生成缓存键"""
        # 使用用户ID+查询内容生成缓存键
        cache_content = f"{user_id}_global_{query}_1"
        # 使用MD5哈希避免键过长
        cache_hash = hashlib.md5(cache_content.encode('utf-8')).hexdigest()
        return f"general_search:{cache_hash}"
    
    def _get_cached_result(self, cache_key: str) -> Optional[list]:
        """获取缓存的搜索结果"""
        try:
            cached_data = redis_service.get_with_metadata(cache_key)
            if cached_data:
                print(f"[CACHE] 全局检索缓存命中: {cache_key}")
                return cached_data['value']
            return None
        except Exception as e:
            print(f"[CACHE] 获取全局检索缓存失败: {e}")
            return None
    
    def _set_cached_result(self, cache_key: str, docs_with_indices: list, query: str) -> bool:
        """设置缓存的搜索结果"""
        try:
            metadata = {
                'user_id': self.user_id,
                'query': query[:100],  # 限制查询长度
                'cache_type': 'general_search_docs_beta'
            }
            # 缓存1小时 = 3600秒
            success = redis_service.set_with_metadata(cache_key, docs_with_indices, 3600, metadata)
            if success:
                print(f"[CACHE] 全局检索文档已缓存: {cache_key}")
            return success
        except Exception as e:
            print(f"[CACHE] 设置全局检索缓存失败: {e}")
            return False

    def search(self, query: str) -> str:
        """在所有课程的所有教学内容中进行全局搜索"""
        try:
            max_docs = AgentConfig.get_tool_config("general_search").get("max_docs", 5)
            print(f"[FLOW] GeneralSearchTool.search 开始执行全局搜索")
            print(f"[FLOW] 查询内容: {query[:50]}...")
            print(f"[FLOW] 当前retrieved_docs数量: {len(self.retrieved_docs)}")
            display_info = self.get_display_info()
            self._notify_tool_start(display_info)
            # 生成缓存键并检查缓存
            query_cache_key = self._generate_cache_key(self.user_id, query)
            cached_docs = self._get_cached_result(query_cache_key)
            if cached_docs:
                docs_with_indices = self.store_docs(cached_docs, max_docs)
                print(f"[FLOW] 返回缓存的全局检索结果")
                # 格式化缓存的文档
                results = ResultFormatter.format_document_results(docs_with_indices, "教学片段")
                result_text = "\n".join(results)
                # 通知前端缓存命中
                self._notify_tool_result({
                    "success": True,
                    "message": f"在所有教学内容中找到 {len(docs_with_indices)} 个相关片段",
                    "documents_count": len(docs_with_indices)
                })
                return result_text
            
            # 获取展示信息并通知前端
            display_info = self.get_display_info()

            
            # 获取全局合并索引 - 包含所有课程的所有视频内容
            search_index = self._get_search_index()
            if not search_index:
                error_msg = "无法获取全局搜索索引"
                print(f"[FLOW] {error_msg}")
                self._notify_tool_result({
                    "success": False,
                    "message": error_msg,
                    "documents_count": 0
                })
                return error_msg
            from services.cache_service import cache_service
            cache_key=cache_service.get_general_cache_key(prefix="general_search")
            retriever = self.retriever_service.create_ensemble_retriever(search_index,cache_key)
            docs = retriever.get_relevant_documents(query)
            
            print(f"[FLOW] 全局检索器返回了 {len(docs)} 个文档")
            
            if not docs:
                print(f"[FLOW] GeneralSearchTool: 全局搜索未找到相关文档")
                self._notify_tool_result({
                    "success": False,
                    "message": "在所有教学内容中未找到相关内容",
                    "documents_count": 0
                })
                return "在所有教学内容中未找到相关内容。"
            
            # 存储检索到的文档并分配全局序号
            
            docs_with_indices = self.store_docs(docs, max_docs)
            
            # 格式化检索结果
            results = ResultFormatter.format_document_results(docs, "教学片段")
            result_text = "\n".join(results)
            
            # 通知前端检索成功
            self._notify_tool_result({
                "success": True,
                "message": f"在所有教学内容中找到 {len(docs_with_indices)} 个相关片段",
                "documents_count": len(docs_with_indices)
            })
            
            # 缓存搜索结果
            self._set_cached_result(query_cache_key, docs_with_indices, query)
            
            print(f"[FLOW] GeneralSearchTool 全局搜索完成，返回结果长度: {len(result_text)}")
            return result_text
            
        except Exception as e:
            print(f"[FLOW] GeneralSearchTool 执行出错: {str(e)}")
            self._notify_tool_result({
                "success": False,
                "message": f"检索过程中出现错误: {str(e)}",
                "documents_count": 0
            })
            return f"检索过程中出现错误: {str(e)}"
