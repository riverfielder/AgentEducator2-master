"""
缓存管理模块
负责处理视频区间摘要的缓存
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from flask import current_app

# 默认缓存目录
SECTION_CACHE_DIR = "section_cache"
os.makedirs(SECTION_CACHE_DIR, exist_ok=True)

def get_section_cache_key(video_id, section_start, section_end, keyframes):
    """
    生成区间缓存的唯一键
    
    参数:
        video_id: 视频ID
        section_start: 区间起始时间点
        section_end: 区间结束时间点
        keyframes: 区间关键帧列表
        
    返回:
        cache_key: 缓存键（字符串）
    """
    # 提取关键帧的文本内容
    text_content = []
    for keyframe in keyframes:
        ocr_text = " ".join(keyframe.get("ocr_result", []))
        asr_text = keyframe.get("asr_texts", "")
        if ocr_text or asr_text:
            text_content.append(f"{ocr_text} {asr_text}")
    
    # 组合内容生成哈希值
    content_str = f"{video_id}_{section_start}_{section_end}_{'|'.join(text_content)}"
    return hashlib.md5(content_str.encode('utf-8')).hexdigest()

def check_section_cache(video_id, section_data):
    """
    检查区间摘要缓存是否存在
    
    参数:
        video_id: 视频ID
        section_data: 区间数据（包含start_time, end_time和keyframes字段）
        
    返回:
        (exists, cache_content): 是否存在及缓存内容
    """
    try:
        # 生成缓存键
        cache_key = get_section_cache_key(
            video_id, 
            section_data["start_time"], 
            section_data["end_time"], 
            section_data["keyframes"]
        )
        
        # 构建缓存文件路径
        cache_file = os.path.join(SECTION_CACHE_DIR, f"{video_id}_{cache_key}.json")
        
        # 检查文件是否存在
        if not os.path.exists(cache_file):
            return False, None
        
        # 读取缓存文件
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # 检查缓存是否过期（默认缓存有效期为30天）
        cache_time = datetime.fromisoformat(cache_data["timestamp"])
        if datetime.now() - cache_time < timedelta(days=30):
            return True, cache_data["summary"]
                
        return False, None
    except Exception as e:
        current_app.logger.error(f"检查区间缓存失败: {str(e)}")
        return False, None

def save_section_cache(video_id, section_data, section_summary):
    """
    保存区间摘要到缓存
    
    参数:
        video_id: 视频ID
        section_data: 区间数据（包含start_time, end_time和keyframes字段）
        section_summary: 区间摘要内容
        
    返回:
        success: 是否保存成功
    """
    try:
        # 生成缓存键
        cache_key = get_section_cache_key(
            video_id, 
            section_data["start_time"], 
            section_data["end_time"], 
            section_data["keyframes"]
        )
        
        # 构建缓存文件路径
        cache_file = os.path.join(SECTION_CACHE_DIR, f"{video_id}_{cache_key}.json")
        
        # 构建缓存数据
        cache_data = {
            "video_id": str(video_id),
            "section_start": section_data["start_time"],
            "section_end": section_data["end_time"],
            "keyframe_count": len(section_data["keyframes"]),
            "summary": section_summary,
            "timestamp": datetime.now().isoformat()
        }
        
        # 写入缓存文件
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
        return True
    except Exception as e:
        current_app.logger.error(f"保存区间缓存失败: {str(e)}")
        return False