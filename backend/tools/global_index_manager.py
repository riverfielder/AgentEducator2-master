"""全局序号管理器"""

class GlobalSourceIndexManager:
    """全局文档引用序号管理器"""
    
    def __init__(self):
        self._global_index = 0
    
    def get_next_index(self) -> int:
        """获取下一个序号"""
        self._global_index += 1
        return self._global_index
    
    def assign_indices(self, documents: list) -> list:
        """为文档列表分配全局序号"""
        for doc in documents:
            if not hasattr(doc, '_global_index'):
                doc._global_index = self.get_next_index()
        return documents
    
    def reset(self):
        """重置序号"""
        self._global_index = 0


# 全局实例
global_source_index_manager = GlobalSourceIndexManager()
