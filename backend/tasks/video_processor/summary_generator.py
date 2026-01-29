"""
摘要生成模块
负责生成视频摘要、知识点和区间摘要
"""

import json
import re
from datetime import datetime
from flask import current_app

# 导入自定义模块
from .task_logger import add_task_log
from .cache_manager import check_section_cache, save_section_cache
from services.unified_llm_service import get_llm_instance

# 导入数据库模型
from models.models import db, Video, VideoSummary

def group_keyframes_into_sections(keyframes_data, min_section_duration=40, max_section_duration=180, min_keyframes_per_section=3, max_keyframes_per_section=15, content_similarity_threshold=0.5, max_sections=6):
    """
    将关键帧分组成视频区间，考虑时间间隔、关键帧数量和内容相关性
    针对slides演讲视频优化的参数设置
    
    参数:
        keyframes_data: 关键帧数据列表
        min_section_duration: 每个区间的最小时长（秒），默认40秒（适合短视频）
        max_section_duration: 每个区间的最大时长（秒），默认180秒（3分钟，适合一个主题讲解）
        min_keyframes_per_section: 每个区间的最小关键帧数，默认3个（保证内容完整性）
        max_keyframes_per_section: 每个区间的最大关键帧数，默认15个（避免区间过大）
        content_similarity_threshold: 内容相关性阈值，默认0.5（slides切换时相似度较低）
        max_sections: 区间上限，默认为6（适合短视频摘要）
        
    返回:
        sections: 区间列表，每个区间包含时间范围和对应的关键帧数据
    """
    if not keyframes_data:
        return []
    
    # 按时间点排序关键帧
    sorted_keyframes = sorted(keyframes_data, key=lambda x: x["time_point"])
    
    # 计算总视频时长，用于动态调整参数
    total_duration = sorted_keyframes[-1]["time_point"] - sorted_keyframes[0]["time_point"]
    target_section_duration = total_duration / max_sections  # 目标区间时长
    
    # 计算内容相关性辅助函数
    def calculate_content_similarity(kf1, kf2):
        """计算两个关键帧之间的内容相似性（基于OCR和ASR文本）"""
        # 提取OCR文本
        ocr_text1 = " ".join(kf1.get("ocr_result", []))
        ocr_text2 = " ".join(kf2.get("ocr_result", []))

        # 合并文本
        text1 = (ocr_text1).lower()
        text2 = (ocr_text2).lower()
        
        # 对于slides演讲，如果两者都没有文本，相关性中等
        if not text1.strip() and not text2.strip():
            return 0.6
        
        # 如果只有一个有文本，则相关性较低
        if not text1.strip() or not text2.strip():
            return 0.2
        
        # 使用改进的Jaccard相似度，考虑slides的特点
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.2
            
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        # 对于slides，如果有相同的知识点，给予更高的权重
        jaccard = intersection / union if union > 0 else 0
            
        return min(jaccard, 1.0)
    
    sections = []
    current_section = {
        "start_time": sorted_keyframes[0]["time_point"],
        "end_time": sorted_keyframes[0]["time_point"],
        "keyframes": [sorted_keyframes[0]]
    }
    
    for i in range(1, len(sorted_keyframes)):
        kf = sorted_keyframes[i]
        time_point = kf["time_point"]
        
        # 计算当前关键帧与当前区间最后一个关键帧的相似性
        last_keyframe = current_section["keyframes"][-1]
        content_similarity = calculate_content_similarity(last_keyframe, kf)
        
        # 判断是否应该开始新区间
        should_split = False
        
        # 条件1: 时间间隔过大（slides演讲中长时间静默可能表示主题转换）
        time_gap = time_point - last_keyframe["time_point"]
        if time_gap > 45:  # 超过45秒的间隔，可能是主题转换
            should_split = True
            
        # 条件2: 区间总时长接近目标时长
        current_duration = time_point - current_section["start_time"]
        if current_duration > max_section_duration:
            should_split = True
        elif current_duration > target_section_duration * 0.8:  # 达到目标时长的80%时考虑分割
            # 如果内容相关性低，则提前分割
            if content_similarity < content_similarity_threshold:
                should_split = True
            
        # 条件3: 关键帧数量过多
        if len(current_section["keyframes"]) >= max_keyframes_per_section:
            should_split = True
            
        # 条件4: 内容相关性低且满足最小条件
        if (content_similarity < content_similarity_threshold and 
            len(current_section["keyframes"]) >= min_keyframes_per_section and
            current_duration >= min_section_duration):
            should_split = True
        
        # 条件5: 强制均匀分布（避免前面的区间过短而后面的区间过长）
        remaining_keyframes = len(sorted_keyframes) - i
        remaining_sections = max_sections - len(sections) - 1  # 减去当前正在构建的区间
        if remaining_sections > 0:
            avg_remaining_keyframes = remaining_keyframes / remaining_sections
            if len(current_section["keyframes"]) > avg_remaining_keyframes * 1.5:
                should_split = True
        
        # 检查当前区间是否满足最小时长要求
        if should_split and current_duration < min_section_duration:
            should_split = False
        
        if should_split:
            # 结束当前区间
            current_section["end_time"] = last_keyframe["time_point"]
            sections.append(current_section)
            
            # 如果已经达到最大区间数-1，则将剩余关键帧都放入最后一个区间
            if len(sections) >= max_sections - 1:
                final_section = {
                    "start_time": time_point,
                    "end_time": sorted_keyframes[-1]["time_point"],
                    "keyframes": sorted_keyframes[i:]
                }
                sections.append(final_section)
                break
            
            # 开始新区间
            current_section = {
                "start_time": time_point,
                "end_time": time_point,
                "keyframes": [kf]
            }
        else:
            # 将当前关键帧添加到当前区间
            current_section["keyframes"].append(kf)
            current_section["end_time"] = time_point
    
    # 添加最后一个区间（如果没有在循环中添加）
    if current_section["keyframes"] and len(sections) < max_sections:
        sections.append(current_section)
    
    # 后处理：合并过小的区间
    if len(sections) > 1:
        merged_sections = []
        for section in sections:
            section_duration = section["end_time"] - section["start_time"]
            keyframe_count = len(section["keyframes"])
            
            # 如果区间太小且可以合并
            if (section_duration < min_section_duration or keyframe_count < min_keyframes_per_section) and merged_sections:
                # 合并到前一个区间
                last_section = merged_sections[-1]
                last_section["end_time"] = section["end_time"]
                last_section["keyframes"].extend(section["keyframes"])
            else:
                merged_sections.append(section)
        
        sections = merged_sections
    
    # 确保至少有一个区间
    if not sections and sorted_keyframes:
        sections = [{
            "start_time": sorted_keyframes[0]["time_point"],
            "end_time": sorted_keyframes[-1]["time_point"],
            "keyframes": sorted_keyframes
        }]
    
    return sections

def generate_section_summary(section_data, video_title, video_description, task_id, video_id, api_key=None, base_url=None):
    """
    为视频的某个区间生成摘要，支持缓存机制
    
    参数:
        section_data: 区间数据，包含开始时间、结束时间和关键帧列表
        video_title: 视频标题
        video_description: 视频描述
        task_id: 任务ID
        video_id: 视频ID
        api_key: API密钥，默认为None，将使用环境变量中的API_KEY
        base_url: API基础URL，默认为None，将使用环境变量中的SILICON_API_BASE
        
    返回:
        section_summary: 区间摘要数据
    """
    try:
        # 首先检查缓存中是否已有该区间的摘要
        cache_exists, cached_summary = check_section_cache(video_id, section_data)
        if cache_exists:
            add_task_log(task_id, video_id, 'info', f"使用缓存的区间摘要 [时间点: {section_data['start_time']}-{section_data['end_time']}]")
            return cached_summary
              # 缓存不存在，需要生成新的摘要
        add_task_log(task_id, video_id, 'info', f"生成新的区间摘要 [时间点: {section_data['start_time']}-{section_data['end_time']}]")
        
        # 获取API配置
        if api_key is None:
            from config.config import Config
            api_key = Config.get_openai_api_key()
        if base_url is None:
            from config.config import Config
            base_url = Config.get_silicon_api_base()
        
        # 准备区间的文本内容
        text_content = []
        
        # 添加基本信息
        text_content.append(f"视频标题: {video_title}")
        if video_description:
            text_content.append(f"视频描述: {video_description}")
        
        # 区间时间信息
        start_time = section_data["start_time"]
        end_time = section_data["end_time"]
        start_formatted = f"{int(start_time // 60):02d}:{int(start_time % 60):02d}"
        end_formatted = f"{int(end_time // 60):02d}:{int(end_time % 60):02d}"
        text_content.append(f"区间时间: {start_formatted} - {end_formatted}")
        
        # 遍历区间内的关键帧
        for keyframe in section_data["keyframes"]:
            time_point = keyframe.get("time_formatted", "")
            ocr_text = " ".join(keyframe.get("ocr_result", []))
            asr_text = keyframe.get("asr_texts", "")
            
            if ocr_text or asr_text:
                frame_text = f"时间点 {time_point}:"
                if ocr_text:
                    frame_text += f" 屏幕文字: {ocr_text}."
                if asr_text:
                    frame_text += f" 语音内容: {asr_text}."
                text_content.append(frame_text)
        
        # 将文本内容合并
        prompt_text = "\n".join(text_content)
        
        # 使用统一的LLM服务
        llm = get_llm_instance("video_processor")
        
        # 构建提示词
        system_prompt = """
你是一个专业的教育视频分析AI助手。现在需要你根据提供的视频区间内容信息，提供一个简短的区间摘要（100字左右），概括这个时间段内的主要内容和知识点。

请按照以下JSON格式返回结果：
{
  "section_summary": "这里是区间内容的摘要..."
}

请确保输出是有效的JSON格式，不要添加任何其他文本。
        """
        
        # 调用模型API生成摘要
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请基于以下视频区间内容信息生成摘要:\n\n{prompt_text}"}
        ]
        response = llm.invoke(messages)
        
        # 解析API响应
        result_text = response.content
        
        # 提取JSON部分
        try:
            # 尝试直接解析整个响应
            summary_data = json.loads(result_text)
            section_summary = summary_data.get("section_summary", "")
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试从文本中提取JSON部分
            json_pattern = r'(\{[\s\S]*\})'
            match = re.search(json_pattern, result_text)
            if match:
                try:
                    summary_data = json.loads(match.group(1))
                    section_summary = summary_data.get("section_summary", "")
                except:
                    add_task_log(task_id, video_id, 'warning', f"无法解析区间摘要JSON: {result_text}")
                    section_summary = result_text[:100] + "..."  # 返回原始文本的前100个字符作为备用
            else:
                add_task_log(task_id, video_id, 'warning', f"在区间摘要响应中找不到有效的JSON: {result_text}")
                section_summary = result_text[:100] + "..."
        
        # 将生成的摘要保存到缓存中
        save_section_cache(video_id, section_data, section_summary)
        
        return section_summary
    except Exception as e:
        add_task_log(task_id, video_id, 'error', f"生成区间摘要失败: {str(e)}")
        return ""

def generate_video_summary(video_id, keyframes_data, task_id, api_key=None, base_url=None):
    """
    使用DeepseekR1模型生成视频摘要和知识点
    
    参数:
        video_id: 视频ID
        keyframes_data: 关键帧数据列表
        task_id: 任务ID
        api_key: API密钥，默认为None，将使用环境变量中的API_KEY
        base_url: API基础URL，默认为None，将使用环境变量中的SILICON_API_BASE
        
    返回:
        summary_data: 摘要数据，包含摘要内容和知识点
    """
    try:
        # 获取视频信息
        video = Video.query.get(video_id)
        if not video:
            current_app.logger.error(f"视频不存在: {video_id}")
            return None
            
        # 获取课程信息
        from models.models import Course
        course = Course.query.get(video.course_id)
        course_name = course.name if course else "未知课程"
        
        # 获取课程已有的知识点
        existing_course_keywords = []
        if course:
            from models.models import CourseKeyword, Keyword
            course_keywords = CourseKeyword.query.filter_by(course_id=course.id).all()
            for ck in course_keywords:
                keyword = Keyword.query.get(ck.keyword_id)
                if keyword:
                    existing_course_keywords.append({
                        'name': keyword.name,
                        'description': keyword.description or ''
                    })
            
        add_task_log(task_id, video_id, 'info', "开始生成视频摘要和知识点...")
          # 获取API配置
        if api_key is None:
            from config.config import Config
            api_key = Config.get_openai_api_key()
        if base_url is None:
            from config.config import Config
            base_url = Config.get_silicon_api_base()
        
        # 准备用于摘要生成的文本内容
        text_content = []
        
        # 从课程和视频信息开始
        text_content.append(f"课程名称: {course_name}")
        text_content.append(f"视频标题: {video.title}")
        if video.description:
            text_content.append(f"视频描述: {video.description}")
        
        # 收集关键帧的OCR和ASR内容
        for idx, keyframe in enumerate(keyframes_data):
            time_point = keyframe.get("time_formatted", "")
            ocr_text = " ".join(keyframe.get("ocr_result", []))
            asr_text = keyframe.get("asr_texts", "")
            
            if ocr_text or asr_text:
                frame_text = f"时间点 {time_point}:"
                if ocr_text:
                    frame_text += f" 屏幕文字: {ocr_text}."
                if asr_text:
                    frame_text += f" 语音内容: {asr_text}."
                text_content.append(frame_text)
        
        # 将文本内容合并
        prompt_text = "\n".join(text_content)
        
        # 常见的教育领域知识点作为启发
        # 常见的教育领域知识点作为启发，以软件工程课程为例
        common_edu_keywords = [
            # 一级知识点
            "软件", "软件开发生命周期", "软件工程",
            # 二级知识点
            "需求工程", "软件设计", "软件测试", "软件部署", "软件维护", 
            "软件项目管理", "软件过程", "软件开发方法", "用例建模", "需求建模",
            "软件体系结构设计", "用户界面设计", "软件详细设计", "编码实现",
            "敏捷开发", "瀑布模型", "面向对象设计", "单元测试",
            # 三级知识点
            "Scrum方法", "用例图设计", "白盒测试技术", "代码审查流程",
            "需求获取", "内聚性", "耦合性", "UML建模",
            # 其他学科知识点
            "数据结构", "算法", "编程语言", "计算机科学", "数学", "物理", 
            "化学", "生物", "历史", "地理", "政治", "经济", "文学",
            "英语", "语文", "编程", "人工智能", "机器学习", "深度学习",
            "前端开发", "后端开发", "数据库", "操作系统", "计算机网络"
        ]
        
        # 使用统一的LLM服务
        llm = get_llm_instance("video_processor")
        
        # 构建已有知识点的提示文本
        existing_keywords_text = ""
        if existing_course_keywords:
            existing_keywords_text = "\n\n课程已有的知识点（请优先考虑复用这些知识点，避免创建重复或过于相似的知识点）：\n"
            for kw in existing_course_keywords:
                desc = f" - {kw['description']}" if kw['description'] else ""
                existing_keywords_text += f"• {kw['name']}{desc}\n"
        
        # 构建提示词
        system_prompt = f"""
你是一个专业的教育视频分析AI助手。现在需要你根据提供的视频内容信息，完成以下任务：

当前处理的课程：{course_name}
当前处理的视频：{video.title}

任务要求：
1. 提供一段200-300字的视频内容摘要，概括视频的主要内容、知识点和教学目标。
2. 提取5-8个知识点标签，这些标签应该能准确反映视频的**主题**和**概念**。它们由较少的主要知识点和较多的具体知识点组成，使得你总结的知识点有**层次**。知识点名称应该简短准确，只能使用一种语言，一般为中文。
3. 为每个提取的知识点提供一句话介绍（20-30字），说明该知识点的核心内容或重要性。

重要提示：在提取知识点时，请优先考虑复用课程中已有的知识点。如果视频内容与已有知识点相关，请直接使用已有知识点的名称，避免创建过于相似但实际不同的知识点。{existing_keywords_text}

请参考以下可能的教育知识点，但不要局限于此列表，应根据实际视频内容提取最相关的知识点：
{', '.join(common_edu_keywords)}
{existing_keywords_text}
请按照以下JSON格式返回结果：
{{
  "summary": "这里是视频内容的摘要...",
  "keywords": [
    {{
      "name": "知识点1",
      "description": "对知识点1的一句话介绍"
    }},
    {{
      "name": "知识点2",
      "description": "对知识点2的一句话介绍"
    }}
  ]
}}

请确保输出是有效的JSON格式，不要添加任何其他文本。
        """
        
        # 调用模型API生成摘要
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请基于以下视频内容信息生成摘要和知识点:\n\n{prompt_text}"}
        ]
        response = llm.invoke(messages)
        
        # 解析API响应
        result_text = response.content
        
        # 提取JSON部分
        try:
            # 尝试直接解析整个响应
            summary_data = json.loads(result_text)
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试从文本中提取JSON部分
            json_pattern = r'(\{[\s\S]*\})'
            match = re.search(json_pattern, result_text)
            if match:
                try:
                    summary_data = json.loads(match.group(1))
                except:
                    add_task_log(task_id, video_id, 'error', f"无法解析AI生成的摘要JSON: {result_text}")
                    return None
            else:
                add_task_log(task_id, video_id, 'error', f"在AI响应中找不到有效的JSON: {result_text}")
                return None
        
        # 验证输出格式
        if "summary" not in summary_data or "keywords" not in summary_data:
            add_task_log(task_id, video_id, 'error', f"AI生成的摘要缺少必要字段: {summary_data}")
            return None
            
        add_task_log(task_id, video_id, 'info', "成功生成视频摘要和知识点")
        return summary_data
        
    except Exception as e:
        add_task_log(task_id, video_id, 'error', f"生成视频摘要失败: {str(e)}")
        return None
