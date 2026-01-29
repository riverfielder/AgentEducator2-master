import json
import subprocess
import os
import tempfile
import shutil
import uuid
from flask import current_app

def check_ffmpeg_installed():
    """检查系统是否安装了FFmpeg"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def get_video_duration(file_path):
    """
    获取视频时长（秒）
    
    Args:
        file_path: 视频文件路径
        
    Returns:
        int: 视频时长（秒）或None（出错时）
    """
    try:
        cmd = [
            'ffprobe', 
            '-v', 'error', 
            '-show_entries', 'format=duration', 
            '-of', 'json', 
            file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        return int(float(data['format']['duration']))
    except Exception as e:
        current_app.logger.error(f"获取视频时长出错: {str(e)}")
        return None

def generate_video_thumbnail(video_path, output_dir, width=320):
    """
    从视频生成缩略图
    
    Args:
        video_path: 视频文件路径
        output_dir: 输出目录
        width: 缩略图宽度
        
    Returns:
        str: 缩略图文件名或None（出错时）
    """
    try:
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # 生成唯一文件名
        thumbnail_filename = f"{os.path.splitext(os.path.basename(video_path))[0]}_{uuid.uuid4().hex[:8]}_thumb.jpg"
        thumbnail_path = os.path.join(output_dir, thumbnail_filename)
        
        # 抓取视频第5秒的帧作为封面
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-ss', '00:00:05',  # 5秒处的帧
            '-vframes', '1',    # 只取一帧
            '-vf', f'scale={width}:-1',  # 设置宽度，高度自适应
            '-y',    # 覆盖已存在的文件
            thumbnail_path
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        
        return thumbnail_filename
    except Exception as e:
        current_app.logger.error(f"生成视频缩略图出错: {str(e)}")
        return None
