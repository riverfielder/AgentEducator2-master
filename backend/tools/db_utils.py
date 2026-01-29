"""数据库查询工具"""

from typing import Optional, Callable, TypeVar, List
from flask import has_app_context

T = TypeVar('T')


def execute_with_app_context(query_func: Callable[[], T]) -> T:
    """
    确保在应用上下文中执行数据库查询
    
    Args:
        query_func: 执行查询的函数
        
    Returns:
        查询结果
    """
    if not has_app_context():
        from app import create_app
        app = create_app()
        with app.app_context():
            return query_func()
    else:
        return query_func()


def find_entity_by_name(entity_class, name: str, get_name_func: Callable = lambda x: x.name) -> Optional[str]:
    """
    通过名称查找实体ID
    
    Args:
        entity_class: 实体类（如Video, Course）
        name: 要查找的名称
        get_name_func: 从实体中获取名称的函数，默认是 lambda x: x.name
        
    Returns:
        找到的实体ID（字符串），如果没找到返回None
    """
    try:
        from .similarity_utils import find_best_match_by_similarity
        
        def query_entities():
            entities = entity_class.query.all()
            return entities
        
        entities = execute_with_app_context(query_entities)
        
        if not entities:
            return None
        
        best_match = find_best_match_by_similarity(
            name, 
            entities, 
            get_name_func,
            min_similarity=0.0
        )
        
        return str(best_match.id) if best_match else None
        
    except Exception as e:
        print(f"[ERROR] 通过名称查找实体失败: {e}")
        return None
