"""
数据库处理模块
负责与数据库交互，保存和加载视频处理相关数据
"""

from flask import current_app
from models.models import db, VideoKeyframe, VideoVectorIndex, VideoSummary

def save_keyframes_to_db(video_id, keyframes_data):
    """
    将关键帧数据保存到数据库
    
    参数:
        video_id: 视频ID
        keyframes_data: 关键帧数据列表
        
    返回:
        success: 是否保存成功
    """
    try:
        for keyframe in keyframes_data:
            # 创建关键帧记录
            db_keyframe = VideoKeyframe(
                video_id=video_id,
                frame_number=keyframe["frame_number"],
                time_point=keyframe["time_point"],
                time_formatted=keyframe["time_formatted"],
                file_name=keyframe["file_name"],
                asr_texts=keyframe.get("asr_texts", "")
            )
            
            # 设置OCR结果
            if "ocr_result" in keyframe:
                db_keyframe.set_ocr_result(keyframe["ocr_result"])
            
            db.session.add(db_keyframe)
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"保存关键帧数据到数据库失败: {str(e)}")
        return False

def load_keyframes_from_db(video_id, include_ocr=True, include_asr=True):
    """
    从数据库加载视频关键帧数据
    
    参数:
        video_id: 视频ID
        include_ocr: 是否包含OCR结果
        include_asr: 是否包含ASR结果
        
    返回:
        keyframes_data: 关键帧数据列表，格式与提取函数返回的格式一致
        若没有数据则返回空列表
    """
    try:
        # 查询数据库中的所有关键帧
        keyframes = VideoKeyframe.query.filter_by(video_id=video_id).order_by(VideoKeyframe.time_point).all()
        
        if not keyframes or len(keyframes) == 0:
            return []
            
        # 转换为提取函数返回的格式
        keyframes_data = []
        for idx, kf in enumerate(keyframes):
            keyframe_data = {
                "id": idx + 1,
                "frame_number": kf.frame_number,
                "time_point": kf.time_point,
                "time_formatted": kf.time_formatted,
                "file_name": kf.file_name
            }
            
            # 加载OCR结果
            if include_ocr:
                try:
                    keyframe_data["ocr_result"] = kf.get_ocr_result()
                except:
                    keyframe_data["ocr_result"] = []
            
            # 加载ASR结果
            if include_asr:
                keyframe_data["asr_texts"] = kf.asr_texts if kf.asr_texts else ""
            
            keyframes_data.append(keyframe_data)
            
        return keyframes_data
    except Exception as e:
        current_app.logger.error(f"从数据库加载关键帧数据失败: {str(e)}")
        return []

def check_video_summary_exists(video_id):
    """
    检查视频摘要是否存在
    
    参数:
        video_id: 视频ID
        
    返回:
        (exists, summary_data): 布尔值表示是否存在，若存在则返回摘要数据
    """
    try:
        # 查询数据库中的摘要记录
        summary = VideoSummary.query.filter_by(video_id=video_id).first()
        
        if not summary:
            return False, None
            
        # 转换为函数返回的格式
        sections = summary.get_sections()
        
        # 如果有whole_summary字段，优先使用它
        if summary.whole_summary:
            summary_content = summary.whole_summary
        # 否则从sections中提取摘要内容
        elif sections and len(sections) > 0:
            summary_content = sections[0]["content"]
        else:
            summary_content = ""
        from models.models import VideoKeyword,Keyword 
        video_keywords = VideoKeyword.query.filter_by(video_id=video_id).all()
        keywords = []
        for vk in video_keywords:
            keyword = Keyword.query.get(vk.keyword_id)
            if keyword:
                keywords.append(keyword.name)
        keywords = ",".join(keywords)
        
        summary_data = {
            "summary": summary_content,
            "keywords": keywords,
            "sections": sections  # 返回原始sections数据
        }
        
        return True, summary_data
    except Exception as e:
        current_app.logger.error(f"检查视频摘要失败: {str(e)}")
        return False, None

def check_video_processing_steps_status(video_id):
    """
    检查视频各个处理步骤的完成状态
    
    参数:
        video_id: 视频ID
        
    返回:
        dict: 各步骤的完成状态
        {
            "keyframes": bool,  # 关键帧提取是否完成
            "ocr": bool,        # OCR识别是否完成
            "asr": bool,        # ASR语音识别是否完成
            "vector": bool,     # 向量索引构建是否完成
            "summary": bool     # 视频摘要生成是否完成
        }
    """
    try:
        status = {
            "keyframes": False,
            "ocr": False,
            "asr": False,
            "vector": False,
            "summary": False
        }
        
        # 检查关键帧提取
        keyframes_count = VideoKeyframe.query.filter_by(video_id=video_id).count()
        if keyframes_count > 0:
            status["keyframes"] = True
            
            # 检查OCR处理 - 随机检查几个关键帧是否有OCR结果
            sample_keyframes = VideoKeyframe.query.filter_by(video_id=video_id).limit(3).all()
            ocr_completed = False
            for kf in sample_keyframes:
                try:
                    ocr_result = kf.get_ocr_result()
                    if ocr_result and len(ocr_result) > 0:
                        ocr_completed = True
                        break
                except:
                    pass
            status["ocr"] = ocr_completed
            
            # 检查ASR处理 - 检查是否有关键帧包含ASR文本
            asr_count = VideoKeyframe.query.filter_by(video_id=video_id).filter(
                VideoKeyframe.asr_texts != None,
                VideoKeyframe.asr_texts != ""
            ).count()
            status["asr"] = asr_count > 0
        
        # 检查向量索引
        vector_index = VideoVectorIndex.query.filter_by(video_id=video_id).first()
        status["vector"] = vector_index is not None
        
        # 检查视频摘要
        summary = VideoSummary.query.filter_by(video_id=video_id).first()
        status["summary"] = summary is not None
        
        return status
    except Exception as e:
        current_app.logger.error(f"检查视频处理状态失败: {str(e)}")
        return {
            "keyframes": False,
            "ocr": False, 
            "asr": False,
            "vector": False,
            "summary": False
        }

def get_uncompleted_processing_steps(video_id):
    """
    获取视频未完成的处理步骤
    
    参数:
        video_id: 视频ID
        
    返回:
        list: 未完成的步骤列表，例如 ["keyframes", "ocr"]
    """
    try:
        status = check_video_processing_steps_status(video_id)
        uncompleted_steps = []
        
        # 按照处理顺序添加未完成的步骤
        step_order = ["keyframes", "ocr", "asr", "vector", "summary"]
        for step in step_order:
            if not status.get(step, False):
                uncompleted_steps.append(step)
                
        return uncompleted_steps
    except Exception as e:
        current_app.logger.error(f"获取未完成处理步骤失败: {str(e)}")
        # 如果出错，返回所有步骤
        return ["keyframes", "ocr", "asr", "vector", "summary"]

def get_all_processing_steps():
    """
    获取所有处理步骤的列表
    
    返回:
        list: 所有处理步骤列表
    """
    return ["keyframes", "ocr", "asr", "vector", "summary"]
