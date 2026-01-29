"""
主处理器模块
负责协调所有视频处理模块，执行完整的视频处理流程
"""

import os
import uuid
from datetime import datetime
from flask import current_app
import cv2

# 导入数据库模型
from models.models import db, Video, VideoProcessingTask, VideoSummary
from models.models import VideoKeyframe, VideoVectorIndex, VideoKeyword, Keyword, CourseKeyword, KeywordRelation
from sqlalchemy.exc import IntegrityError

# 导入处理模块
from .keyframe_extractor import extract_keyframes
from .ocr_processor import OCRProcessor
from .asr_processor import ASRProcessor
from .vector_indexer import build_vector_index, check_vector_index_exists
from .summary_generator import generate_video_summary, generate_section_summary, group_keyframes_into_sections
from .db_handler import save_keyframes_to_db, load_keyframes_from_db, check_video_summary_exists, check_video_processing_steps_status
from .task_logger import add_task_log

# 配置信息
KEYFRAMES_OUTPUT_DIR = "temp_keyframes"
VECTOR_INDEX_DIR = "vector_indices"

def process_video_task(video_id, stop_flag=None, processing_steps=None, preview_mode=False):  # 保留参数但不再使用
    """
    处理视频任务的主函数
    
    参数:
        video_id: 视频ID
        stop_flag: 停止标志(threading.Event)，如果设置则中断处理
        processing_steps: 要执行的步骤列表，可包含：
            - "keyframes": 关键帧提取
            - "ocr": OCR文字识别
            - "asr": 语音识别
            - "vector": 向量索引构建
            - "summary": 视频摘要生成
        preview_mode: 参数保留但不再使用(已弃用)
    """
    try:
        # 获取视频信息
        video = Video.query.get(video_id)
        if not video:
            current_app.logger.error(f"视频不存在: {video_id}")
            return False
        
        # 如果未指定处理步骤，则执行所有步骤
        if processing_steps is None:
            processing_steps = ["keyframes", "ocr", "asr", "vector", "summary"]
          # 1. 查找现有任务并更新状态为进行中
        task = VideoProcessingTask.query.filter_by(video_id=video_id, status="pending").first()
        if task:
            task_id = task.task_id
            if not preview_mode:
                task.status = "processing"
                # 在真正开始处理时更新开始时间
                task.start_time = datetime.now()
        else:            # 如果没有找到待处理的任务，创建一个新任务
            task_id = f"task-{uuid.uuid4().hex[:8]}"
            if not preview_mode:
                task = VideoProcessingTask(
                    video_id=video_id,
                    task_id=task_id,
                    status="processing",
                    processing_type="full_reprocess",  # 更新为full_reprocess
                    start_time=datetime.now()  # 真正开始处理时的时间
                )
                db.session.add(task)
            else:                # 预览模式创建一个临时任务对象，不保存到数据库
                task = type('obj', (object,), {
                    'task_id': task_id,
                    'status': 'preview',
                    'progress': 0.0
                })()
                
        if not preview_mode:
            db.session.commit()
            
        add_task_log(task_id, video_id, 'debug', f"进程ID:{os.getpid()}")
        
        if preview_mode:
            add_task_log(task_id, video_id, 'info', f"开始预览处理视频: {video.title} (步骤: {', '.join(processing_steps)})")
        else:
            add_task_log(task_id, video_id, 'info', f"开始处理视频: {video.title} (步骤: {', '.join(processing_steps)})")
            # 2. 确保视频文件在本地可用
        video_path = video.get_local_path()
        if not video.is_local_file_exists():
            add_task_log(task_id, video_id, 'error', f"视频文件不存在: {video_path}")
            if not preview_mode:
                task.status = 'failed'
                task.error_message = f"视频文件不存在: {video_path}"
                task.end_time = datetime.now()
                db.session.commit()
            return False
        
        add_task_log(task_id, video_id, 'info', f"视频文件已找到: {video_path}")
        
        # 检查是否请求停止
        if stop_flag and stop_flag.is_set():
            add_task_log(task_id, video_id, 'warning', "收到停止请求，任务被中断")
            if not preview_mode:
                task.status = 'cancelled'
                task.error_message = '任务被手动停止'
                task.end_time = datetime.now()
                db.session.commit()
            return False
        
        # 3. 创建输出目录
        output_folder = os.path.join(KEYFRAMES_OUTPUT_DIR, f"video_{video_id}")
        os.makedirs(output_folder, exist_ok=True)
        add_task_log(task_id, video_id, 'info', f"创建输出目录: {output_folder}")
        
        # 初始化变量
        keyframes_data = []
        fps = 0
        total_frames = 0
        total_steps = len(processing_steps)
        completed_steps = 0          # 4. 关键帧提取
        if "keyframes" in processing_steps:
            add_task_log(task_id, video_id, 'info', "步骤：关键帧提取")
            
            # 包含关键帧步骤，清空并重新提取
            add_task_log(task_id, video_id, 'info', "开始提取关键帧...")
            keyframes_data, fps, total_frames = extract_keyframes(video_path, output_folder, similarity_threshold=10)
            add_task_log(task_id, video_id, 'info', f"提取了 {len(keyframes_data)} 个关键帧, FPS: {fps}, 总帧数: {total_frames}")
            
            # 保存关键帧数据到数据库（非预览模式）
            if not preview_mode:
                # 清除旧的关键帧数据
                VideoKeyframe.query.filter_by(video_id=video_id).delete()
                db.session.commit()
                
                success = save_keyframes_to_db(video_id, keyframes_data)
                if not success:
                    add_task_log(task_id, video_id, 'error', "保存关键帧数据到数据库失败")
                    raise Exception("保存关键帧数据到数据库失败")
                add_task_log(task_id, video_id, 'info', "关键帧数据已保存到数据库")
            else:
                add_task_log(task_id, video_id, 'info', "预览模式：关键帧数据不保存到数据库")
            
            completed_steps += 1
            if not preview_mode:
                task.progress = completed_steps / total_steps * 0.8  # 80%为处理进度，20%为后期整理
                db.session.commit()        
        else:
            # 如果不执行关键帧提取，需要从数据库加载现有数据
            keyframes_data = load_keyframes_from_db(video_id)
            if keyframes_data:
                cap = cv2.VideoCapture(video_path)
                fps = cap.get(cv2.CAP_PROP_FPS)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                cap.release()
                add_task_log(task_id, video_id, 'info', f"从数据库加载了 {len(keyframes_data)} 个关键帧数据")
            
        # 如果没有关键帧数据，无法继续后续处理
        if not keyframes_data and any(step in processing_steps for step in ["ocr", "asr", "vector", "summary"]):
            add_task_log(task_id, video_id, 'error', "没有关键帧数据，无法进行OCR、ASR、向量索引或摘要处理")
            raise Exception("没有关键帧数据，无法进行后续处理")
        
        # 检查是否请求停止
        if stop_flag and stop_flag.is_set():
            add_task_log(task_id, video_id, 'warning', "收到停止请求，任务被中断")
            if not preview_mode:
                task.status = 'cancelled'
                task.error_message = '任务被手动停止'
                task.end_time = datetime.now()
                db.session.commit()
            return False          # 5. OCR处理
        if "ocr" in processing_steps:
            add_task_log(task_id, video_id, 'info', "步骤：OCR文字识别")
            
            # 包含OCR步骤，清空并重新处理
            add_task_log(task_id, video_id, 'info', "开始OCR文字识别...")
            ocr_processor = OCRProcessor()
            keyframes_data = ocr_processor.perform_ocr(keyframes_data, output_folder)
            add_task_log(task_id, video_id, 'info', "OCR处理完成")
            
            # 更新数据库中的关键帧数据（非预览模式）
            if not preview_mode:
                # 清除旧的关键帧数据并重新保存
                VideoKeyframe.query.filter_by(video_id=video_id).delete()
                db.session.commit()
                
                success = save_keyframes_to_db(video_id, keyframes_data)
                if not success:
                    add_task_log(task_id, video_id, 'error', "更新关键帧OCR数据到数据库失败")
                    raise Exception("更新关键帧OCR数据到数据库失败")
                add_task_log(task_id, video_id, 'info', "关键帧OCR数据已更新到数据库")
            else:
                add_task_log(task_id, video_id, 'info', "预览模式：OCR数据不保存到数据库")
            
            completed_steps += 1
            if not preview_mode:
                task.progress = completed_steps / total_steps * 0.8
                db.session.commit()
        else:
            # 如果不执行OCR步骤，但后续步骤需要OCR数据，则从数据库加载
            if any(step in processing_steps for step in ["vector", "summary"]) and not keyframes_data:
                keyframes_data = load_keyframes_from_db(video_id)
                add_task_log(task_id, video_id, 'info', f"为后续步骤从数据库加载了关键帧数据（包含OCR）")
        
        # 检查是否请求停止
        if stop_flag and stop_flag.is_set():
            add_task_log(task_id, video_id, 'warning', "收到停止请求，任务被中断")
            if not preview_mode:
                task.status = 'cancelled'
                task.error_message = '任务被手动停止'
                task.end_time = datetime.now()
                db.session.commit()
            return False          # 6. ASR处理
        if "asr" in processing_steps:
            add_task_log(task_id, video_id, 'info', "步骤：语音识别")
            
            # 包含ASR步骤，清空并重新处理
            add_task_log(task_id, video_id, 'info', "开始语音识别...")
            asr_processor = ASRProcessor()
            asr_result = asr_processor.perform_asr(video_path)
            if asr_result:
                add_task_log(task_id, video_id, 'info', f"语音识别成功，识别了 {len(asr_result)} 个语音片段")
                keyframes_data = asr_processor.assign_asr_to_keyframes(keyframes_data, asr_result)
            else:
                add_task_log(task_id, video_id, 'warning', "语音识别失败或没有可识别的语音")
            
            # 更新数据库中的关键帧数据（非预览模式）
            if not preview_mode:
                # 清除旧的关键帧数据并重新保存
                VideoKeyframe.query.filter_by(video_id=video_id).delete()
                db.session.commit()
                
                success = save_keyframes_to_db(video_id, keyframes_data)
                if not success:
                    add_task_log(task_id, video_id, 'error', "更新关键帧ASR数据到数据库失败")
                    raise Exception("更新关键帧ASR数据到数据库失败")
                add_task_log(task_id, video_id, 'info', "关键帧ASR数据已更新到数据库")
            else:
                add_task_log(task_id, video_id, 'info', "预览模式：ASR数据不保存到数据库")
            
            completed_steps += 1
            if not preview_mode:
                task.progress = completed_steps / total_steps * 0.8
                db.session.commit()
        else:
            # 如果不执行ASR步骤，但后续步骤需要ASR数据，则从数据库加载
            if any(step in processing_steps for step in ["vector", "summary"]) and not keyframes_data:
                keyframes_data = load_keyframes_from_db(video_id)
                add_task_log(task_id, video_id, 'info', f"为后续步骤从数据库加载了关键帧数据（包含ASR）")
        
        # 检查是否请求停止
        if stop_flag and stop_flag.is_set():
            add_task_log(task_id, video_id, 'warning', "收到停止请求，任务被中断")
            if not preview_mode:
                task.status = 'cancelled'
                task.error_message = '任务被手动停止'
                task.end_time = datetime.now()
                db.session.commit()
            return False              # 7. 构建向量索引
        if "vector" in processing_steps:
            add_task_log(task_id, video_id, 'info', "步骤：构建向量索引")
            
            # 包含向量索引步骤，清空并重新构建
            add_task_log(task_id, video_id, 'info', "开始构建向量索引...")
            
            index_path = f"{VECTOR_INDEX_DIR}/video_{video_id}"
            success = build_vector_index(video_id, keyframes_data, index_path)
            if success:
                add_task_log(task_id, video_id, 'info', f"向量索引构建成功，保存到 {index_path}")
                
                # 保存索引信息到数据库（非预览模式）
                if not preview_mode:
                    # 清除旧的向量索引记录
                    VideoVectorIndex.query.filter_by(video_id=video_id).delete()
                    db.session.commit()
                    
                    vector_index = VideoVectorIndex(
                        video_id=video_id,
                        index_path=index_path,
                        embedding_model="Pro/BAAI/bge-m3",
                        total_vectors=len(keyframes_data)
                    )
                    db.session.add(vector_index)
                    db.session.commit()
                else:
                    add_task_log(task_id, video_id, 'info', "预览模式：向量索引信息不保存到数据库")
            else:
                add_task_log(task_id, video_id, 'warning', "向量索引构建失败")
            
            completed_steps += 1
            if not preview_mode:
                task.progress = completed_steps / total_steps * 0.8
                db.session.commit()
        else:
            # 如果不执行向量索引步骤，检查是否存在现有索引
            if any(step in processing_steps for step in ["summary"]):
                existing_index = VideoVectorIndex.query.filter_by(video_id=video_id).first()
                if existing_index:
                    add_task_log(task_id, video_id, 'info', f"发现现有向量索引: {existing_index.index_path}")
                else:
                    add_task_log(task_id, video_id, 'warning', "后续步骤需要向量索引，但未找到现有索引")
        
        # 检查是否请求停止
        if stop_flag and stop_flag.is_set():
            add_task_log(task_id, video_id, 'warning', "收到停止请求，任务被中断")
            if not preview_mode:
                task.status = 'cancelled'
                task.error_message = '任务被手动停止'
                task.end_time = datetime.now()
                db.session.commit()
            return False        # 8. 生成视频摘要和知识点
        if "summary" in processing_steps:
            add_task_log(task_id, video_id, 'info', "步骤：生成视频摘要和知识点")
            
            # 包含摘要步骤，清空并重新生成
            add_task_log(task_id, video_id, 'info', "开始生成视频摘要和知识点...")
            summary_data = generate_video_summary(video_id, keyframes_data, task_id)
            
            if summary_data:
                if not preview_mode:
                    # 在删除之前先获取当前视频的知识点ID列表
                    current_video_keyword_ids = [vk.keyword_id for vk in VideoKeyword.query.filter_by(video_id=video_id).all()]
                    
                    # 清除旧的摘要记录
                    VideoSummary.query.filter_by(video_id=video_id).delete()
                    # 清除旧的视频知识点关系
                    VideoKeyword.query.filter_by(video_id=video_id).delete()
                    db.session.flush()

                    # 获取要删除的课程知识点 - 只存在于这个视频的知识点
                    course_keywords_to_delete_ids = []
                    if current_video_keyword_ids:
                        course_keywords_to_delete_ids = db.session.query(CourseKeyword.keyword_id).filter(
                            CourseKeyword.course_id == video.course_id,
                            CourseKeyword.keyword_id.in_(current_video_keyword_ids),
                            ~CourseKeyword.keyword_id.in_(
                                db.session.query(VideoKeyword.keyword_id).filter(
                                    VideoKeyword.video_id != video_id,
                                    VideoKeyword.video_id.in_(
                                        db.session.query(Video.id).filter(Video.course_id == video.course_id)
                                    )
                                )
                            )
                        ).all()
                        course_keywords_to_delete_ids = [ck.keyword_id for ck in course_keywords_to_delete_ids]

                    # 删除只属于这个视频的课程知识点关系
                    if course_keywords_to_delete_ids:
                        CourseKeyword.query.filter(
                            CourseKeyword.course_id == video.course_id,
                            CourseKeyword.keyword_id.in_(course_keywords_to_delete_ids)
                        ).delete(synchronize_session=False)                    # 删除不再被任何视频使用的知识点
                    orphaned_keyword_ids = []
                    if current_video_keyword_ids:
                        orphaned_keyword_ids = [kw_id for kw_id in current_video_keyword_ids 
                                              if not db.session.query(VideoKeyword.query.filter_by(keyword_id=kw_id).exists()).scalar()]
                                              
                    # 删除孤立知识点及其相关记录
                    if orphaned_keyword_ids:
                        try:
                            # 首先删除所有知识点关系记录
                            deleted_relations = KeywordRelation.query.filter(
                                (KeywordRelation.source_keyword_id.in_(orphaned_keyword_ids)) |
                                (KeywordRelation.target_keyword_id.in_(orphaned_keyword_ids))
                            ).delete(synchronize_session=False)
                            if deleted_relations > 0:
                                add_task_log(task_id, video_id, 'info', f"删除了 {deleted_relations} 个孤立知识点的相关关系")
                            
                            # 然后删除课程知识点关系（如果还有残留）
                            deleted_course_keywords = CourseKeyword.query.filter(
                                CourseKeyword.keyword_id.in_(orphaned_keyword_ids)
                            ).delete(synchronize_session=False)
                            if deleted_course_keywords > 0:
                                add_task_log(task_id, video_id, 'info', f"删除了 {deleted_course_keywords} 个孤立知识点的课程关联")
                            
                            # 最后删除知识点本身
                            deleted_keywords = Keyword.query.filter(Keyword.id.in_(orphaned_keyword_ids)).delete(synchronize_session=False)
                            add_task_log(task_id, video_id, 'info', f"删除了 {deleted_keywords} 个孤立知识点")
                        except Exception as e:
                            add_task_log(task_id, video_id, 'error', f"删除孤立知识点时出错: {str(e)}")
                            # 不要让删除错误影响整个处理流程
                            db.session.rollback()
    
                    db.session.commit()
                    
                    # 将关键帧分组成区间
                    add_task_log(task_id, video_id, 'info', "将视频关键帧分组成区间...")
                        
                    sections_data = group_keyframes_into_sections(
                        keyframes_data,
                        max_section_duration=300,  # 5分钟
                        min_keyframes_per_section=2,
                        max_keyframes_per_section=15,
                        content_similarity_threshold=0.6
                    )
                    
                    add_task_log(task_id, video_id, 'info', f"视频被分为 {len(sections_data)} 个区间")
                    
                    # 为每个区间生成摘要
                    section_summaries = []
                    for idx, section in enumerate(sections_data):
                        add_task_log(task_id, video_id, 'info', f"为区间 {idx+1}/{len(sections_data)} 生成摘要...")
                        
                        start_time = section["start_time"]
                        end_time = section["end_time"]
                        section_summary = generate_section_summary(
                            section, 
                            video.title, 
                            video.description if video.description else "", 
                            task_id, 
                            video_id
                        )
                        
                        duration = end_time - start_time
                        minutes = int(duration // 60)
                        seconds = int(duration % 60)
                        duration_text = f"{minutes}分{seconds}秒" if minutes > 0 else f"{seconds}秒"
                        
                        section_summaries.append({
                            "title": f"区间 {idx+1} ({duration_text})",
                            "content": section_summary,
                            "time_point": start_time,
                            "end_time": end_time,
                            "keyframe_count": len(section["keyframes"])
                        })
                    
                    # 保存摘要到数据库
                    video_summary = VideoSummary(
                        video_id=video_id,
                        whole_summary=summary_data['summary'],
                        generate_time=datetime.now()
                    )                      # 处理知识点
                    if summary_data['keywords']:
                        all_keyword_objects = []
                        
                        for keyword_data in summary_data['keywords']:
                            # 处理新的关键词格式（包含name和description）
                            if isinstance(keyword_data, dict):
                                keyword_name = keyword_data.get('name', '')
                                keyword_description = keyword_data.get('description', '')
                            else:
                                # 兼容旧格式（纯字符串）
                                keyword_name = keyword_data
                                keyword_description = ''
                            
                            if not keyword_name:
                                continue
                                
                            # 直接按名称查询知识点
                            existing_keyword = Keyword.query.filter_by(name=keyword_name).first()
                            
                            if existing_keyword:
                                # 更新已存在知识点的描述（如果有新描述且原来没有描述）
                                if keyword_description and not existing_keyword.description:
                                    existing_keyword.description = keyword_description
                                all_keyword_objects.append(existing_keyword)
                                add_task_log(task_id, video_id, 'debug', f"使用已存在的知识点: {keyword_name}")
                            else:
                                # 创建新知识点
                                try:
                                    new_keyword = Keyword(
                                        name=keyword_name, 
                                        category='specific_point',
                                        description=keyword_description
                                    )
                                    db.session.add(new_keyword)
                                    db.session.flush()  # 获取ID
                                    all_keyword_objects.append(new_keyword)
                                    add_task_log(task_id, video_id, 'debug', f"创建新知识点: {keyword_name}")
                                except IntegrityError:
                                    # 如果插入时发生重复错误，回滚并重新查询
                                    db.session.rollback()
                                    existing_keyword = Keyword.query.filter_by(name=keyword_name).first()
                                    if existing_keyword:
                                        # 更新描述
                                        if keyword_description and not existing_keyword.description:
                                            existing_keyword.description = keyword_description
                                        all_keyword_objects.append(existing_keyword)
                                        add_task_log(task_id, video_id, 'debug', f"并发创建冲突，使用已存在的知识点: {keyword_name}")
                                    else:
                                        add_task_log(task_id, video_id, 'error', f"无法创建或找到知识点: {keyword_name}")
                                        continue
                        
                        # 创建关系
                        video_keywords = []
                        course_keywords_to_check = []
                        
                        for keyword_obj in all_keyword_objects:
                            video_keywords.append(VideoKeyword(video_id=video_id, keyword_id=keyword_obj.id))
                            course_keywords_to_check.append(keyword_obj.id)
                        
                        db.session.add_all(video_keywords)
                        
                        # 处理课程知识点关系
                        existing_course_keywords = {ck.keyword_id for ck in CourseKeyword.query.filter(
                            CourseKeyword.course_id == video.course_id,
                            CourseKeyword.keyword_id.in_(course_keywords_to_check)
                        ).all()}
                        
                        new_course_keywords = []
                        for keyword_id in course_keywords_to_check:
                            if keyword_id not in existing_course_keywords:
                                new_course_keywords.append(CourseKeyword(course_id=video.course_id, keyword_id=keyword_id))
                        
                        if new_course_keywords:
                            db.session.add_all(new_course_keywords)
                    
                    video_summary.set_sections(section_summaries)
                    db.session.add(video_summary)
                    db.session.commit()
                    add_task_log(task_id, video_id, 'info', f"视频摘要生成成功: {len(summary_data.get('keywords', []))}个知识点")
                else:                    add_task_log(task_id, video_id, 'info', f"预览模式：生成摘要成功，包含{len(summary_data.get('keywords', []))}个知识点，但不保存到数据库")
            else:
                add_task_log(task_id, video_id, 'warning', "视频摘要生成失败")

            
            completed_steps += 1
            if not preview_mode:
                task.progress = completed_steps / total_steps * 0.8
                db.session.commit()
        else:
            # 如果不执行摘要步骤，检查是否存在现有摘要
            existing_summary = VideoSummary.query.filter_by(video_id=video_id).first()
            if existing_summary:
                add_task_log(task_id, video_id, 'info', f"发现现有视频摘要")
            else:
                add_task_log(task_id, video_id, 'info', "未执行摘要生成步骤，且未找到现有摘要")        # 9. 处理完成，所有本地文件已准备完毕
        if not preview_mode:
            add_task_log(task_id, video_id, 'info', "视频处理完成")
        
        # 10. 更新任务状态为完成
        if not preview_mode:
            task.status = "completed"
            task.progress = 1.0
            task.end_time = datetime.now()
            db.session.commit()
            add_task_log(task_id, video_id, 'info', f"视频处理完成, 总用时: {(task.end_time - task.start_time).total_seconds()} 秒")
        else:
            add_task_log(task_id, video_id, 'info', "预览模式处理完成")
        
        return True
    except Exception as e:
        # 更新任务状态为失败（非预览模式）
        if not preview_mode:
            db.session.rollback()
            task = VideoProcessingTask.query.filter_by(video_id=video_id).first()
            if task:
                task.status = "failed"
                task.error_message = str(e)
                task.end_time = datetime.now()
                db.session.commit()
        
        add_task_log(task_id if 'task_id' in locals() else f"task-{uuid.uuid4().hex[:8]}", video_id, 'error', f"处理视频任务失败: {str(e)}")
        current_app.logger.error(f"处理视频任务失败: {str(e)}")
        return False
