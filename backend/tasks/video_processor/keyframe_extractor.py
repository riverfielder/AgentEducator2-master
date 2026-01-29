"""
关键帧提取模块
负责从视频中提取关键帧
"""

import os
import cv2
import subprocess
import shutil
import imagehash
from PIL import Image
from skimage.metrics import structural_similarity as ssim
from flask import current_app

def is_significant_change(frame1, frame2, threshold=0.90):
    """计算结构相似性（SSIM），判断当前帧与前一帧是否有较大变化"""
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    score, _ = ssim(gray1, gray2, full=True)
    return score < threshold  # 低于阈值，说明变化明显

def extract_keyframes(video_path, output_folder, similarity_threshold=0.9):
    """
    从视频中提取相似度去重的 I 帧关键帧
    """
    os.makedirs(output_folder, exist_ok=True)
    
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    temp_iframe_dir = os.path.join(output_folder, "iframes_temp")
    os.makedirs(temp_iframe_dir, exist_ok=True)

    # 用 ffmpeg 提取所有 I 帧（关键帧）
    ffmpeg_cmd = f'ffmpeg -i "{video_path}" -vf "select=\'eq(pict_type\\,I)\'" -vsync vfr -frame_pts 1 -q:v 2 "{temp_iframe_dir}/iframe_%08d.jpg"'
    try:
        subprocess.run(ffmpeg_cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        current_app.logger.error(f"ffmpeg 提取 I 帧失败: {str(e)}")
        return [], 0, 0

    # 获取视频基本信息
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    # 加载 I 帧图像
    iframe_files = sorted([f for f in os.listdir(temp_iframe_dir) if f.endswith('.jpg')])
    if not iframe_files:
        current_app.logger.warning("未提取到 I 帧")
        return [], fps, total_frames

    keyframes_data = []
    previous_hash = None
    keyframe_index = 1

    for i, filename in enumerate(iframe_files):
        filepath = os.path.join(temp_iframe_dir, filename)
        image = Image.open(filepath)
        current_hash = imagehash.phash(image)

        # 判断是否保留该帧
        should_save = False
        
        # 第一帧或与前一帧相差较大时保留
        if previous_hash is None or previous_hash - current_hash > similarity_threshold:
            if previous_hash is not None:
                print(f"保留关键帧: {filename} (哈希差异: {previous_hash - current_hash})")
            should_save = True
            previous_hash = current_hash
        
        if should_save:
            # 获取该帧的时间点和帧号
            frame_number = int(filename.split('_')[1].split('.')[0])
            time_point = frame_number / fps if fps > 0 else 0
            
            # 保存关键帧图像
            output_filename = f"keyframe_{keyframe_index:04d}.jpg"
            output_path = os.path.join(output_folder, output_filename)
            shutil.copy(filepath, output_path)
            
            # 添加到关键帧数据列表
            keyframes_data.append({
                "id": keyframe_index,
                "frame_number": frame_number,
                "time_point": time_point,
                "time_formatted": f"{int(time_point // 60):02d}:{int(time_point % 60):02d}.{int((time_point % 1) * 100):02d}",
                "file_name": output_filename
            })
            
            keyframe_index += 1

    # 清理临时目录
    shutil.rmtree(temp_iframe_dir)

    return keyframes_data, fps, total_frames