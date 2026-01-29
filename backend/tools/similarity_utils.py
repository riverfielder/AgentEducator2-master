"""相似度计算工具"""

from typing import Optional


def jaccard_similarity(str1: str, str2: str) -> float:
    """计算两个字符串的Jaccard相似度"""
    set1 = set(str1.lower().split())
    set2 = set(str2.lower().split())
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0


def find_best_match_by_similarity(query: str, candidates: list, get_name_func, min_similarity: float = 0.0):
    """
    通过相似度找到最佳匹配
    
    Args:
        query: 查询字符串
        candidates: 候选项列表
        get_name_func: 从候选项中获取名称的函数
        min_similarity: 最小相似度阈值
        
    Returns:
        最佳匹配的候选项，如果没有超过阈值的匹配则返回None
    """
    if not candidates:
        return None
    
    best_match = None
    best_similarity = min_similarity
    
    for candidate in candidates:
        name = get_name_func(candidate)
        similarity = jaccard_similarity(query, name)
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = candidate
    
    return best_match
