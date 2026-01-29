"""
智能文档摘要处理器
基于视频摘要逻辑设计，实现文档的智能摘要和知识点提取
支持多层次摘要：整体摘要、分段摘要、知识点提取、要点归纳
"""

import json
import re
from datetime import datetime
from flask import current_app
from sqlalchemy.exc import IntegrityError
from services.unified_llm_service import get_llm_instance

# 导入数据库模型
from models.models import (
    db,
    Document,
    DocumentSummary,
    DocumentKeyword,
    Keyword,
    CourseKeyword,
    VideoKeyword,
    Video,
)
from .task_logger import add_task_log

def analyze_document_structure(segments_data):
    """
    分析文档结构，识别文档类型和层次信息

    参数:
        segments_data: 文档分段数据列表

    返回:
        dict: 文档结构分析结果
    """
    try:
        structure_info = {
            "doc_type": "unknown",
            "has_titles": False,
            "title_levels": [],
            "content_types": {},
            "total_length": 0,
            "avg_segment_length": 0,
            "estimated_reading_time": 0,
        }

        title_count = 0
        content_type_count = {}
        total_content_length = 0

        for segment in segments_data:
            content = segment.get("content", "")
            segment_type = segment.get("segment_type", "paragraph")
            title = segment.get("title", "")

            total_content_length += len(content)

            # 统计内容类型
            if segment_type in content_type_count:
                content_type_count[segment_type] += 1
            else:
                content_type_count[segment_type] = 1

            # 检查标题层级
            if title:
                title_count += 1
                # 简单的标题级别判断（基于markdown格式）
                if content.startswith("# "):
                    structure_info["title_levels"].append(1)
                elif content.startswith("## "):
                    structure_info["title_levels"].append(2)
                elif content.startswith("### "):
                    structure_info["title_levels"].append(3)
                else:
                    structure_info["title_levels"].append(0)

        # 分析文档类型
        if content_type_count.get("table", 0) > 2:
            structure_info["doc_type"] = "data_report"
        elif content_type_count.get("list", 0) > content_type_count.get("paragraph", 0):
            structure_info["doc_type"] = "procedure_guide"
        elif title_count > len(segments_data) * 0.3:
            structure_info["doc_type"] = "structured_document"
        elif content_type_count.get("paragraph", 0) > len(segments_data) * 0.7:
            structure_info["doc_type"] = "essay_article"
        else:
            structure_info["doc_type"] = "mixed_content"

        structure_info["has_titles"] = title_count > 0
        structure_info["content_types"] = content_type_count
        structure_info["total_length"] = total_content_length
        structure_info["avg_segment_length"] = (
            total_content_length / len(segments_data) if segments_data else 0
        )
        structure_info["estimated_reading_time"] = (
            total_content_length / 250
        )  # 假设250字符/分钟

        return structure_info

    except Exception as e:
        current_app.logger.error(f"分析文档结构失败: {str(e)}")
        return {
            "doc_type": "unknown",
            "has_titles": False,
            "title_levels": [],
            "content_types": {},
        }


def group_segments_into_sections(
    segments_data,
    max_section_length=2000,
    min_segments_per_section=2,
    max_segments_per_section=8,
):
    """
    将文档分段组织成逻辑章节，用于生成章节摘要
    参考视频关键帧分组逻辑

    参数:
        segments_data: 分段数据列表
        max_section_length: 每个章节的最大字符长度
        min_segments_per_section: 每个章节最少分段数
        max_segments_per_section: 每个章节最多分段数

    返回:
        list: 章节列表，每个章节包含多个分段
    """
    try:
        if not segments_data:
            return []

        def calculate_content_similarity(seg1, seg2):
            """计算两个分段之间的内容相似性"""
            content1 = seg1.get("content", "").lower()
            content2 = seg2.get("content", "").lower()

            if not content1.strip() or not content2.strip():
                return 0.3

            # 简单的词汇相似度计算
            words1 = set(content1.split())
            words2 = set(content2.split())

            if not words1 or not words2:
                return 0.2

            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))

            return intersection / union if union > 0 else 0.0

        sections = []
        current_section = {
            "title": segments_data[0].get("title", f"第1章节"),
            "segments": [segments_data[0]],
            "total_length": len(segments_data[0].get("content", "")),
        }

        section_count = 1

        for i in range(1, len(segments_data)):
            segment = segments_data[i]
            content = segment.get("content", "")
            content_length = len(content)

            # 计算与当前章节最后一个分段的相似性
            last_segment = current_section["segments"][-1]
            similarity = calculate_content_similarity(last_segment, segment)

            # 判断是否应该开始新章节
            should_split = False

            # 条件1: 当前章节长度超过限制
            if current_section["total_length"] + content_length > max_section_length:
                should_split = True

            # 条件2: 分段数量超过限制
            if len(current_section["segments"]) >= max_segments_per_section:
                should_split = True

            # 条件3: 遇到明显的标题分段（内容相似性低且有标题）
            if (
                segment.get("title")
                and similarity < 0.3
                and len(current_section["segments"]) >= min_segments_per_section
            ):
                should_split = True

            # 条件4: 内容差异较大且满足最小分段要求
            if (
                similarity < 0.2
                and len(current_section["segments"]) >= min_segments_per_section
            ):
                should_split = True

            if (
                should_split
                and len(current_section["segments"]) >= min_segments_per_section
            ):
                # 结束当前章节
                sections.append(current_section)

                # 开始新章节
                section_count += 1
                section_title = segment.get("title") or f"第{section_count}章节"
                current_section = {
                    "title": section_title,
                    "segments": [segment],
                    "total_length": content_length,
                }
            else:
                # 添加到当前章节
                current_section["segments"].append(segment)
                current_section["total_length"] += content_length

        # 添加最后一个章节
        if current_section["segments"]:
            sections.append(current_section)

        # 后处理：合并过小的章节
        if len(sections) > 1:
            merged_sections = []
            for section in sections:
                if (
                    len(section["segments"]) < min_segments_per_section
                    or section["total_length"] < max_section_length * 0.3
                ) and merged_sections:
                    # 合并到前一个章节
                    last_section = merged_sections[-1]
                    last_section["segments"].extend(section["segments"])
                    last_section["total_length"] += section["total_length"]
                    last_section["title"] += f" & {section['title']}"
                else:
                    merged_sections.append(section)

            sections = merged_sections

        return sections

    except Exception as e:
        current_app.logger.error(f"分段组织失败: {str(e)}")
        return [
            {
                "title": "完整文档",
                "segments": segments_data,
                "total_length": sum(len(s.get("content", "")) for s in segments_data),
            }
        ]


def generate_section_summary(
    section_data,
    document_title,
    document_description,
    task_id,
    document_id,
    api_key=None,
    base_url=None,
):
    """
    为文档的某个章节生成摘要
    参考视频区间摘要逻辑

    参数:
        section_data: 章节数据，包含标题和分段列表
        document_title: 文档标题
        document_description: 文档描述
        task_id: 任务ID
        document_id: 文档ID
        api_key: API密钥
        base_url: API基础URL

    返回:
        str: 章节摘要
    """
    try:
        add_task_log(
            task_id,
            None,
            "info",
            f"生成章节摘要: {section_data['title']}",
            document_id=document_id,
        )

        # 获取API配置
        if api_key is None:
            from config.config import Config

            api_key = Config.get_openai_api_key()
        if base_url is None:
            from config.config import Config

            base_url = Config.get_silicon_api_base()

        # 准备章节的文本内容
        text_content = []

        # 添加基本信息
        text_content.append(f"文档标题: {document_title}")
        if document_description:
            text_content.append(f"文档描述: {document_description}")
        text_content.append(f"章节标题: {section_data['title']}")

        # 遍历章节内的分段
        for idx, segment in enumerate(section_data["segments"]):
            segment_title = segment.get("title", "")
            content = segment.get("content", "")
            segment_type = segment.get("segment_type", "paragraph")

            if content:
                segment_text = f"分段 {idx+1} ({segment_type}):"
                if segment_title:
                    segment_text += f" 标题: {segment_title}."
                segment_text += f" 内容: {content[:500]}..."  # 限制长度避免token超限
                text_content.append(segment_text)

        # 将文本内容合并
        prompt_text = "\n".join(text_content)

        # 使用统一的LLM服务
        llm = get_llm_instance("document_processor")

        # 构建提示词
        system_prompt = """
你是一个专业的教育文档分析AI助手。现在需要你根据提供的文档章节内容信息，提供一个简明的章节摘要（150字左右），概括这个章节的主要内容和关键知识点。

请按照以下JSON格式返回结果：
{
  "section_summary": "这里是章节内容的摘要..."
}

请确保输出是有效的JSON格式，不要添加任何其他文本。
        """

        # 调用AI模型生成摘要
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"请基于以下文档章节内容信息生成摘要:\n\n{prompt_text}",
            },
        ]
        response = llm.invoke(messages)

        # 解析API响应
        result_text = response.content

        # 提取JSON部分
        try:
            summary_data = json.loads(result_text)
            section_summary = summary_data.get("section_summary", "")
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试从文本中提取JSON部分
            json_pattern = r"(\{[\s\S]*\})"
            match = re.search(json_pattern, result_text)
            if match:
                try:
                    summary_data = json.loads(match.group(1))
                    section_summary = summary_data.get("section_summary", "")
                except:
                    add_task_log(
                        task_id,
                        None,
                        "warning",
                        f"无法解析章节摘要JSON: {result_text}",
                        document_id=document_id,
                    )
                    section_summary = result_text[:150] + "..."
            else:
                add_task_log(
                    task_id,
                    None,
                    "warning",
                    f"在章节摘要响应中找不到有效的JSON: {result_text}",
                    document_id=document_id,
                )
                section_summary = result_text[:150] + "..."

        return section_summary

    except Exception as e:
        add_task_log(
            task_id,
            None,
            "error",
            f"生成章节摘要失败: {str(e)}",
            document_id=document_id,
        )
        return ""


def generate_document_summary(
    document_id, segments_data, task_id, api_key=None, base_url=None
):
    """
    使用AI模型生成文档整体摘要和知识点
    参考视频摘要逻辑，支持智能分析和多层次摘要

    参数:
        document_id: 文档ID
        segments_data: 文档分段数据列表
        task_id: 任务ID
        api_key: API密钥
        base_url: API基础URL

    返回:
        dict: 摘要数据，包含整体摘要、知识点、要点和章节摘要
    """
    try:
        # 获取文档信息
        document = Document.query.get(document_id)
        if not document:
            current_app.logger.error(f"文档不存在: {document_id}")
            return None

        # 获取课程信息
        from models.models import Course
        course = Course.query.get(document.course_id)
        course_name = course.name if course else "未知课程"
        
        # 获取课程已有的知识点
        existing_course_keywords = []
        if course:
            course_keywords = CourseKeyword.query.filter_by(course_id=course.id).all()
            for ck in course_keywords:
                keyword = Keyword.query.get(ck.keyword_id)
                if keyword:
                    existing_course_keywords.append({
                        'name': keyword.name,
                        'description': keyword.description or ''
                    })

        add_task_log(
            task_id,
            None,
            "info",
            "开始生成文档摘要和知识点...",
            document_id=document_id,
        )

        # 获取API配置
        if api_key is None:
            from config.config import Config

            api_key = Config.get_openai_api_key()
        if base_url is None:
            from config.config import Config

            base_url = Config.get_silicon_api_base()

        # 分析文档结构
        structure_info = analyze_document_structure(segments_data)
        add_task_log(
            task_id,
            None,
            "info",
            f"文档结构分析: 类型={structure_info['doc_type']}, 总长度={structure_info['total_length']}字符",
            document_id=document_id,
        )

        # 准备用于摘要生成的文本内容
        text_content = []

        # 从课程和文档信息开始
        text_content.append(f"课程名称: {course_name}")
        text_content.append(f"文档标题: {document.title}")
        if document.description:
            text_content.append(f"文档描述: {document.description}")

        text_content.append(f"文档类型: {structure_info['doc_type']}")
        text_content.append(f"文档总长度: {structure_info['total_length']} 字符")
        text_content.append(
            f"预计阅读时间: {structure_info['estimated_reading_time']:.1f} 分钟"
        )

        # 收集关键分段内容（前三个+后三个+中间有标题的分段）
        key_segments = []

        # 前三个分段
        key_segments.extend(segments_data[:3])

        # 中间有标题的分段
        middle_segments = []
        for segment in segments_data[3:-3]:
            if segment.get("title") or segment.get("segment_type") in [
                "heading",
                "title",
            ]:
                middle_segments.append(segment)
        # 限制中间分段数量
        key_segments.extend(middle_segments[:5])

        # 后三个分段
        if len(segments_data) > 6:
            key_segments.extend(segments_data[-3:])

        # 去重并保持顺序
        seen_ids = set()
        unique_segments = []
        for segment in key_segments:
            segment_id = segment.get("id") or segment.get("segment_number", 0)
            if segment_id not in seen_ids:
                seen_ids.add(segment_id)
                unique_segments.append(segment)

        # 为每个关键分段添加内容
        for idx, segment in enumerate(unique_segments):
            title = segment.get("title", "")
            content = segment.get("content", "")
            segment_type = segment.get("segment_type", "paragraph")

            if content:
                segment_text = f"分段 {idx+1} ({segment_type}):"
                if title:
                    segment_text += f" 标题: {title}."
                # 限制分段内容长度，避免token超限
                segment_text += f" 内容: {content[:800]}..."
                text_content.append(segment_text)

        # 将文本内容合并
        prompt_text = "\n".join(text_content)

        # 常见的教育领域知识点作为启发
        common_edu_keywords = [
            "软件",
            "软件开发生命周期",
            "软件工程",
            # 二级知识点
            "需求工程",
            "软件设计",
            "软件测试",
            "软件部署",
            "软件维护",
            "软件项目管理",
            "软件过程",
            "软件开发方法",
            "用例建模",
            "需求建模",
            "软件体系结构设计",
            "用户界面设计",
            "软件详细设计",
            "编码实现",
            "敏捷开发",
            "瀑布模型",
            "面向对象设计",
            "单元测试",
            # 三级知识点
            "Scrum方法",
            "用例图设计",
            "白盒测试技术",
            "代码审查流程",
            "需求获取",
            "内聚性",
            "耦合性",
            "UML建模",
            # 其他学科知识点
            "数据结构",
            "算法",
            "编程语言",
            "计算机科学",
            "数学",
            "物理",
            "化学",
            "生物",
            "历史",
            "地理",
            "政治",
            "经济",
            "文学",
            "英语",
            "语文",
            "编程",
            "人工智能",
            "机器学习",
            "深度学习",
            "前端开发",
            "后端开发",
            "数据库",
            "操作系统",
            "计算机网络" "数据结构",
            "算法",
            "编程语言",
            "计算机科学",
            "数学",
            "物理",
            "化学",
            "生物",
            "历史",
            "地理",
            "政治",
            "经济",
            "文学",
            "英语",
            "语文",
            "编程",
            "人工智能",
            "机器学习",
            "深度学习",
            "前端开发",
            "后端开发",
            "数据库",
            "操作系统",
            "计算机网络",
            "软件工程",
            "项目管理",
            "需求分析",
            "系统设计",
            "测试",
            "部署",
            "运维",
            "教学方法",
            "案例分析",
            "实验设计",
            "理论基础",
            "实践应用",
            "技能培训",
        ]

        # 使用统一的LLM服务
        llm = get_llm_instance("document_processor")

        # 构建已有知识点的提示文本
        existing_keywords_text = ""
        if existing_course_keywords:
            existing_keywords_text = "\n\n课程已有的知识点（请优先考虑复用这些知识点，避免创建重复或过于相似的知识点）：\n"
            for kw in existing_course_keywords:
                desc = f" - {kw['description']}" if kw['description'] else ""
                existing_keywords_text += f"• {kw['name']}{desc}\n"
        
        # 构建提示词
        system_prompt = f"""
你是一个专业的教育文档分析AI助手。现在需要你根据提供的文档内容信息，完成以下任务：

当前处理的课程：{course_name}
当前处理的文档：{document.title}

任务要求：
1. 提供一段300-400字的文档整体摘要，概括文档的主要内容、知识点和学习目标。
2. 提取5-8个知识点标签，这些标签应该能准确反映文档的主题和概念。主题是比较大的知识点，概念是比较具体的知识点。知识点名称应该简短准确，只能使用一种语言，一般为中文。
3. 为每个提取的知识点提供一句话介绍（20-30字），说明该知识点的核心内容或重要性。
4. 归纳3-6个核心要点，每个要点用一句话概括（30-50字）。
5. 判断文档的学习难度等级（1-5级，1=入门，5=高级）。

重要提示：在提取知识点时，请优先考虑复用课程中已有的知识点。如果文档内容与已有知识点相关，请直接使用已有知识点的名称，避免创建过于相似但实际不同的知识点。{existing_keywords_text}

请参考以下可能的教育知识点，但不要局限于此列表，应根据实际文档内容提取最相关的知识点：
{', '.join(common_edu_keywords)}

请按照以下JSON格式返回结果：
{{
  "summary": "这里是文档内容的整体摘要...",
  "keywords": [
    {{
      "name": "知识点1",
      "description": "对知识点1的一句话介绍"
    }},
    {{
      "name": "知识点2",
      "description": "对知识点2的一句话介绍"
    }}
  ],
  "main_points": ["要点1", "要点2", "要点3", ...],
  "difficulty_level": 3
}}

请确保输出是有效的JSON格式，不要添加任何其他文本。
        """

        # 调用AI模型生成摘要
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"请基于以下文档内容信息生成摘要和知识点:\n\n{prompt_text}",
            },
        ]
        response = llm.invoke(messages)

        # 解析API响应
        result_text = response.content

        # 提取JSON部分
        try:
            summary_data = json.loads(result_text)
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试从文本中提取JSON部分
            json_pattern = r"(\{[\s\S]*\})"
            match = re.search(json_pattern, result_text)
            if match:
                try:
                    summary_data = json.loads(match.group(1))
                except:
                    add_task_log(
                        task_id,
                        None,
                        "error",
                        f"无法解析AI生成的摘要JSON: {result_text}",
                        document_id=document_id,
                    )
                    return None
            else:
                add_task_log(
                    task_id,
                    None,
                    "error",
                    f"在AI响应中找不到有效的JSON: {result_text}",
                    document_id=document_id,
                )
                return None

        # 验证输出格式
        required_fields = ["summary", "keywords", "main_points"]
        for field in required_fields:
            if field not in summary_data:
                add_task_log(
                    task_id,
                    None,
                    "error",
                    f"AI生成的摘要缺少必要字段 {field}: {summary_data}",
                    document_id=document_id,
                )
                return None

        # 生成章节摘要（如果文档较长）
        sections_summaries = []
        if len(segments_data) > 6:  # 只有较长的文档才生成章节摘要
            add_task_log(
                task_id,
                None,
                "info",
                "文档较长，开始生成章节摘要...",
                document_id=document_id,
            )
            sections_data = group_segments_into_sections(segments_data)

            for idx, section in enumerate(sections_data):
                add_task_log(
                    task_id,
                    None,
                    "info",
                    f"为章节 {idx+1}/{len(sections_data)} 生成摘要...",
                    document_id=document_id,
                )
                section_summary = generate_section_summary(
                    section,
                    document.title,
                    document.description or "",
                    task_id,
                    document_id,
                )

                if section_summary:
                    sections_summaries.append(
                        {
                            "title": section["title"],
                            "content": section_summary,
                            "segment_count": len(section["segments"]),
                        }
                    )

        # 添加章节摘要到结果中
        summary_data["sections"] = sections_summaries
        summary_data["structure_info"] = structure_info

        add_task_log(
            task_id, None, "info", "成功生成文档摘要和知识点", document_id=document_id
        )
        return summary_data

    except Exception as e:
        add_task_log(
            task_id,
            None,
            "error",
            f"生成文档摘要失败: {str(e)}",
            document_id=document_id,
        )
        return None


def save_document_summary_to_database(document_id, summary_data, preview_mode=False):
    """
    保存文档摘要信息到数据库
    参考视频摘要的保存逻辑，使用DocumentSummary和DocumentKeyword表

    参数:
        document_id: 文档ID
        summary_data: 摘要数据
        preview_mode: 是否为预览模式

    返回:
        bool: 保存是否成功
    """
    try:
        if preview_mode:
            current_app.logger.info("预览模式：文档摘要信息不保存到数据库")
            return True

        # 获取文档信息
        document = Document.query.get(document_id)
        if not document:
            current_app.logger.error(f"文档不存在: {document_id}")
            return False

        # 清除旧的摘要记录
        DocumentSummary.query.filter_by(document_id=document_id).delete()

        # 清除旧的文档知识点关系
        old_keyword_ids = [
            dk.keyword_id
            for dk in DocumentKeyword.query.filter_by(document_id=document_id).all()
        ]
        DocumentKeyword.query.filter_by(document_id=document_id).delete()
        db.session.flush()

        # 创建新的摘要记录
        # 处理keywords字段，提取字典格式中的name字段
        keywords_list = summary_data.get("keywords", [])
        keyword_names = [keyword.get('name', '').strip() for keyword in keywords_list if keyword.get('name', '').strip()]
        keywords_str = ",".join(keyword_names)
        
        document_summary = DocumentSummary(
            document_id=document_id,
            whole_summary=summary_data.get("summary", ""),
            main_points=json.dumps(
                summary_data.get("main_points", []), ensure_ascii=False
            ),
            keywords=keywords_str,
            generate_time=datetime.now(),
        )

        # 如果有章节摘要，保存到sections字段
        if summary_data.get("sections"):
            document_summary.set_sections(summary_data["sections"])

        db.session.add(document_summary)
        db.session.flush()

        # 处理知识点：更新全局keywords表和相关关系
        if summary_data.get("keywords"):
            current_app.logger.info(
                f"开始处理 {len(summary_data['keywords'])} 个知识点"
            )
            all_keyword_objects = []
            created_keywords_count = 0
            updated_keywords_count = 0

            for keyword_data in summary_data["keywords"]:
                # 处理新的关键词格式（包含name和description）
                if isinstance(keyword_data, dict):
                    keyword_name = keyword_data.get('name', '').strip()
                    keyword_description = keyword_data.get('description', '')
                else:
                    # 兼容旧格式（纯字符串）
                    keyword_name = keyword_data.strip() if keyword_data else ''
                    keyword_description = ''
                
                if not keyword_name:  # 跳过空知识点
                    continue

                # 查询已存在的知识点
                existing_keyword = Keyword.query.filter_by(name=keyword_name).first()

                if existing_keyword:
                    all_keyword_objects.append(existing_keyword)
                    # 更新知识点的最后更新时间
                    existing_keyword.update_time = datetime.now()
                    # 如果知识点没有描述且有新描述，更新描述
                    if keyword_description and not existing_keyword.description:
                        existing_keyword.description = keyword_description
                    elif not existing_keyword.description:
                        existing_keyword.description = f"知识点: {keyword_name}"
                    updated_keywords_count += 1
                    current_app.logger.debug(f"使用已存在的知识点: {keyword_name}")
                else:
                    # 创建新知识点
                    try:
                        # 使用提供的描述，如果没有则生成默认描述
                        description = keyword_description if keyword_description else f"从文档'{document.title}'提取的知识点"
                        
                        new_keyword = Keyword(
                            name=keyword_name,
                            category="specific_point",  # 默认类别为三级知识点
                            description=description,
                            create_time=datetime.now(),
                            update_time=datetime.now(),
                        )
                        db.session.add(new_keyword)
                        db.session.flush()
                        all_keyword_objects.append(new_keyword)
                        created_keywords_count += 1
                        # current_app.logger.debug(f"创建新知识点: {keyword_name} (类别: {category})")
                    except IntegrityError:
                        # 并发创建冲突，回滚并重新查询
                        db.session.rollback()
                        existing_keyword = Keyword.query.filter_by(
                            name=keyword_name
                        ).first()
                        if existing_keyword:
                            all_keyword_objects.append(existing_keyword)
                            existing_keyword.update_time = datetime.now()
                            # 更新描述
                            if keyword_description and not existing_keyword.description:
                                existing_keyword.description = keyword_description
                            updated_keywords_count += 1
                            current_app.logger.debug(
                                f"并发创建冲突，使用已存在的知识点: {keyword_name}"
                            )
                        else:
                            current_app.logger.error(
                                f"无法创建或找到知识点: {keyword_name}"
                            )
                            continue

            current_app.logger.info(
                f"知识点处理完成：创建 {created_keywords_count} 个，更新 {updated_keywords_count} 个"
            )

            # 创建文档知识点关系
            document_keywords_created = 0
            for idx, keyword_obj in enumerate(all_keyword_objects):
                # 计算权重：前面的知识点权重稍高
                weight = max(0.5, 1.0 - (idx * 0.1))

                document_keyword = DocumentKeyword(
                    document_id=document_id,
                    keyword_id=keyword_obj.id,
                    weight=weight,
                    create_time=datetime.now(),
                )
                db.session.add(document_keyword)
                document_keywords_created += 1

            current_app.logger.info(
                f"创建了 {document_keywords_created} 个文档-知识点关系"
            )

            # 更新课程知识点关系和统计信息
            course_keywords_created = 0
            course_keywords_updated = 0
            for keyword_obj in all_keyword_objects:
                existing_course_keyword = CourseKeyword.query.filter_by(
                    course_id=document.course_id, keyword_id=keyword_obj.id
                ).first()

                if existing_course_keyword:
                    # 更新课程知识点统计信息
                    existing_course_keyword.update_time = datetime.now()
                    # 重新计算平均权重（简化处理，可以后续优化）
                    total_weight = 0.0
                    relation_count = 0

                    # 统计该知识点在当前课程下的所有关系
                    video_relations = (
                        VideoKeyword.query.join(Video)
                        .filter(
                            Video.course_id == document.course_id,
                            VideoKeyword.keyword_id == keyword_obj.id,
                        )
                        .all()
                    )
                    for vr in video_relations:
                        total_weight += vr.weight
                        relation_count += 1

                    doc_relations = (
                        DocumentKeyword.query.join(Document)
                        .filter(
                            Document.course_id == document.course_id,
                            DocumentKeyword.keyword_id == keyword_obj.id,
                        )
                        .all()
                    )
                    for dr in doc_relations:
                        total_weight += dr.weight
                        relation_count += 1

                    if relation_count > 0:
                        existing_course_keyword.avg_weight = (
                            total_weight / relation_count
                        )

                    course_keywords_updated += 1
                else:
                    # 创建新的课程知识点关系
                    course_keyword = CourseKeyword(
                        course_id=document.course_id,
                        keyword_id=keyword_obj.id,
                        video_count=0,  # 文档不计入视频数量，但可以扩展为document_count
                        avg_weight=1.0,
                        create_time=datetime.now(),
                        update_time=datetime.now(),
                    )
                    db.session.add(course_keyword)
                    course_keywords_created += 1

            current_app.logger.info(
                f"课程知识点关系：创建 {course_keywords_created} 个，更新 {course_keywords_updated} 个"
            )

        # 删除不再被任何文档使用的孤立知识点
        if old_keyword_ids:
            orphaned_keyword_ids = []
            for kw_id in old_keyword_ids:
                # 检查是否还被其他文档或视频使用
                # 检查文档关联
                doc_used = DocumentKeyword.query.filter_by(keyword_id=kw_id).count() > 0
                
                # 检查视频关联 - 使用正确的SQL语法
                video_used = db.session.execute(
                    db.text("SELECT COUNT(*) FROM video_keywords WHERE keyword_id = :kw_id"),
                    {"kw_id": kw_id}
                ).scalar() > 0
                
                still_used = doc_used or video_used
                if not still_used:
                    orphaned_keyword_ids.append(kw_id)

            if orphaned_keyword_ids:
                # 删除孤立知识点的课程关系
                CourseKeyword.query.filter(
                    CourseKeyword.keyword_id.in_(orphaned_keyword_ids)
                ).delete(synchronize_session=False)
                # 删除孤立知识点
                Keyword.query.filter(Keyword.id.in_(orphaned_keyword_ids)).delete(
                    synchronize_session=False
                )
                current_app.logger.info(
                    f"删除了 {len(orphaned_keyword_ids)} 个孤立知识点"
                )

        db.session.commit()
        current_app.logger.info(
            f"文档摘要信息已保存到数据库: document_id={document_id}"
        )
        return True

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"保存文档摘要信息到数据库失败: {str(e)}")
        import traceback

        current_app.logger.error(f"错误详情: {traceback.format_exc()}")
        return False


def process_document_summary_step(document_id, preview_mode=False, task_id=None):  # preview_mode参数保留但不再使用
    """
    执行文档摘要处理步骤
    参考视频摘要处理逻辑

    参数:
        document_id: 文档ID
        preview_mode: 参数保留但不再使用(已弃用)
        task_id: 任务ID（可选，如果未提供将生成默认值）

    返回:
        dict: 处理结果
    """
    try:
        current_app.logger.info(f"开始处理文档 {document_id} 的摘要步骤")

        # 1. 检查是否已存在摘要
        existing_summary = DocumentSummary.query.filter_by(
            document_id=document_id
        ).first()

        if existing_summary and not preview_mode:
            current_app.logger.info(f"文档 {document_id} 的摘要已存在，将重新生成")

        # 2. 加载文档分段数据
        from .vector_processor import load_document_segments_for_vector

        segments_data = load_document_segments_for_vector(document_id)

        if not segments_data:
            error_msg = f"文档 {document_id} 没有可用的分段数据，无法生成摘要"
            current_app.logger.error(error_msg)
            return {"success": False, "message": error_msg, "action": "failed"}

        # 3. 生成智能摘要
        # 如果没有提供task_id，使用默认格式（保持向后兼容）
        if task_id is None:
            task_id = f"summary-{str(document_id)[:8]}"
        summary_data = generate_document_summary(document_id, segments_data, task_id)

        if not summary_data:
            error_msg = f"文档 {document_id} 摘要生成失败"
            current_app.logger.error(error_msg)
            return {"success": False, "message": error_msg, "action": "failed"}

        # 4. 保存摘要信息到数据库
        db_success = save_document_summary_to_database(
            document_id, summary_data, preview_mode
        )

        if not db_success and not preview_mode:
            current_app.logger.warning("文档摘要生成成功，但数据库记录保存失败")

        # 5. 返回处理结果
        result = {
            "success": True,
            "message": f"文档摘要生成{'（预览模式）' if preview_mode else ''}成功",
            "summary_length": len(summary_data.get("summary", "")),
            "keywords_count": len(summary_data.get("keywords", [])),
            "main_points_count": len(summary_data.get("main_points", [])),
            "sections_count": len(summary_data.get("sections", [])),
            "difficulty_level": summary_data.get("difficulty_level", 3),
            "action": "created",
        }

        current_app.logger.info(f"文档 {document_id} 摘要处理完成: {result}")
        return result

    except Exception as e:
        error_msg = f"文档摘要处理失败: {str(e)}"
        current_app.logger.error(error_msg)
        import traceback

        current_app.logger.error(f"错误详情: {traceback.format_exc()}")
        return {"success": False, "message": error_msg, "action": "failed"}
