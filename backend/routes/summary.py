from flask import Blueprint, request, jsonify
from models.models import db, Video, VideoSummary
from utils.result import Result
from datetime import datetime
import uuid

# 创建总结相关的蓝图
summary_bp = Blueprint("summary", __name__)

@summary_bp.route('/video/<video_id>', methods=['GET'])
def get_video_summary(video_id):
    """
    获取视频总结接口
    """
    try:
        # 检查视频是否存在
        video = Video.query.get(video_id)
        if not video:
            return jsonify(Result.error(404, "视频不存在"))
        
        # 查询视频总结
        summary = VideoSummary.query.filter_by(video_id=video_id).first()
        if not summary:
            return jsonify(Result.error(404, "该视频尚未生成总结"))
        from models.models import VideoKeyword, Keyword
        # 获取视频知识点及其详细信息
        video_keywords = VideoKeyword.query.filter_by(video_id=video_id).all()
        #查询每个知识点的名称
        keywords = []
        for vk in video_keywords:
            keyword = Keyword.query.get(vk.keyword_id)
            if keyword:
                keywords.append(keyword.to_dict())

        # 构建响应数据
        summary_data = {
            "videoId": video_id,
            "title": video.title,
            "keywordsList":keywords,
            "sections": summary.sections,  
            "generateTime": summary.generate_time.isoformat(),
            "summary": summary.whole_summary if summary.whole_summary else "",
        }
        
        return jsonify(Result.success(summary_data, "获取总结成功"))
        
    except Exception as e:
        return jsonify(Result.error(400, f"获取总结失败: {str(e)}"))

