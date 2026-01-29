"""教学安排指导工具"""

import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from .base_tool import BaseTool


class TeachingGuidanceInput(BaseModel):
    """教学安排指导工具的输入参数模型"""
    scope: str = Field(default="comprehensive", description="分析范围：comprehensive(综合分析)、specific_course(特定课程)、content_structure(内容结构)")


class TeachingGuidanceTool(BaseTool):
    """教学安排指导工具"""
    
    name = "teaching_guidance"
    description = "基于当前课程内容和课件组成，为教师提供教学安排和规划建议。当用户询问'请给我一些教学建议'、'教学安排'、'教学规划'、'如何安排课程'等问题时，必须使用此工具。"
    
    def __init__(self, user_id: str = None):
        super().__init__(user_id=user_id)
        
    def get_display_info(self) -> Dict[str, Any]:
        """获取前端展示信息"""
        return {
            "tool_name": "教学安排指导",
            "tool_icon": "mdi-clipboard-text-clock",
            "tool_color": "success",
            "description": "分析课程内容，提供教学规划建议",
            "context": {
                "supports_content_analysis": True,
                "supports_teaching_advice": True,
                "supports_course_planning": True
            },
            "status_message": "正在分析您的课程内容..."
        }
    
    def search(self, scope: str = "comprehensive") -> str:
        """Implement search method required by BaseTool"""
        return self.generate_teaching_guidance(scope)
    
    def generate_teaching_guidance(self, scope: str = "comprehensive") -> str:
        """Generate teaching arrangement guidance suggestions"""
        try:
            print(f"[FLOW] TeachingGuidanceTool.generate_teaching_guidance starting")
            print(f"[FLOW] Parameters - scope: {scope}, user_id: {self.user_id}")
            
            # Update display information
            display_info = self.get_display_info()
            self._notify_tool_start(display_info)
            
            # Analyze teacher's course content composition
            courses_analysis = self._analyze_teacher_courses()
            
            if not courses_analysis["courses"]:
                result_msg = "您目前没有分配任何课程，无法提供教学建议。请先创建或分配课程后再使用此功能。"
                print(f"[FLOW] {result_msg}")
                self._notify_tool_result({
                    "success": False,
                    "message": result_msg,
                    "analysis_type": scope
                })
                return result_msg
            
            # 生成教学指导建议
            guidance_result = self._generate_guidance_recommendations(courses_analysis, scope)
            
            print(f"[FLOW] 成功生成教学指导建议，涉及 {len(courses_analysis['courses'])} 个课程")
            self._notify_tool_result({
                "success": True,
                "message": f"成功生成教学指导建议",
                "courses_analyzed": len(courses_analysis["courses"]),
                "analysis_type": scope
            })
            
            return guidance_result
            
        except Exception as e:
            error_msg = f"生成教学指导建议失败: {str(e)}"
            print(f"[FLOW] {error_msg}")
            self._notify_tool_result({
                "success": False,
                "message": error_msg,
                "analysis_type": scope
            })
            return error_msg
    
    def _analyze_teacher_courses(self) -> Dict[str, Any]:
        """分析教师的课程内容组成"""
        try:
            from models.models import Course, Video, Document, db, Keyword, VideoKeyword, DocumentKeyword
            from sqlalchemy import func
            
            def analyze_courses():
                # Get all teacher's courses
                courses = db.session.query(Course).filter(
                    Course.teacher_id == self.user_id,
                    Course.is_deleted == False
                ).all()
                
                print(f"[DEBUG] Analyzing {len(courses)} courses content composition")
                
                analysis_result = {
                    "courses": [],
                    "total_videos": 0,
                    "total_documents": 0,
                    "content_topics": set(),
                    "knowledge_coverage": {}
                }
                
                for course in courses:
                    # Get course videos and documents
                    videos = db.session.query(Video).filter(
                        Video.course_id == course.id,
                        Video.is_deleted == False
                    ).all()
                    
                    documents = db.session.query(Document).filter(
                        Document.course_id == course.id,
                        Document.is_deleted == False
                    ).all()
                    
                    # Analyze course keywords coverage
                    course_keywords = self._analyze_course_keywords(course.id)
                    
                    course_info = {
                        "id": course.id,
                        "name": course.name,
                        "description": course.description or "",
                        "videos_count": len(videos),
                        "documents_count": len(documents),
                        "keywords": course_keywords,
                        "videos": [{"id": v.id, "title": v.title, "duration": getattr(v, 'duration', 0)} for v in videos],
                        "documents": [{"id": d.id, "title": d.title, "type": getattr(d, 'type', 'unknown')} for d in documents]
                    }
                    
                    analysis_result["courses"].append(course_info)
                    analysis_result["total_videos"] += len(videos)
                    analysis_result["total_documents"] += len(documents)
                    analysis_result["content_topics"].update(course_keywords)
                
                # Convert set to list for JSON serialization
                analysis_result["content_topics"] = list(analysis_result["content_topics"])
                
                return analysis_result
            
            # Execute query in application context
            from flask import current_app, has_app_context
            if not has_app_context():
                from app import create_app
                app = create_app()
                with app.app_context():
                    return analyze_courses()
            else:
                return analyze_courses()
            
        except Exception as e:
            print(f"[ERROR] Failed to analyze course content: {str(e)}")
            return {"courses": [], "total_videos": 0, "total_documents": 0, "content_topics": [], "knowledge_coverage": {}}
    
    def _analyze_course_keywords(self, course_id: str) -> List[str]:
        """Analyze keywords/knowledge points for specific course"""
        try:
            from models.models import db, Keyword, VideoKeyword, DocumentKeyword, Video, Document
            
            # Get course video keywords
            video_keywords = db.session.query(Keyword).join(
                VideoKeyword, Keyword.id == VideoKeyword.keyword_id
            ).join(
                Video, VideoKeyword.video_id == Video.id
            ).filter(
                Video.course_id == course_id,
                Video.is_deleted == False
            ).distinct().all()
            
            # Get course document keywords
            doc_keywords = db.session.query(Keyword).join(
                DocumentKeyword, Keyword.id == DocumentKeyword.keyword_id
            ).join(
                Document, DocumentKeyword.document_id == Document.id
            ).filter(
                Document.course_id == course_id,
                Document.is_deleted == False
            ).distinct().all()
            
            # Merge and deduplicate
            all_keywords = set()
            for kw in video_keywords:
                all_keywords.add(kw.name)
            for kw in doc_keywords:
                all_keywords.add(kw.name)
            
            return list(all_keywords)
            
        except Exception as e:
            print(f"[ERROR] Failed to analyze course keywords: {str(e)}")
            return []
    
    def _generate_guidance_recommendations(self, courses_analysis: Dict[str, Any], scope: str) -> str:
        """Generate intelligent teaching guidance recommendations using LLM"""
        
        try:
            from services.llm_service import llm_service
            
            # Build detailed course analysis data
            courses_data = self._format_courses_data_for_llm(courses_analysis)
            
            # Build LLM prompt
            prompt = self._build_teaching_guidance_prompt(courses_data, scope)
            
            print(f"[FLOW] Calling LLM to generate teaching guidance...")
            
            # Call LLM to generate suggestions
            if hasattr(self, 'streaming_callback') and self.streaming_callback:
                # Use streaming generation if callback available
                llm_response = llm_service.generate_streaming_response(
                    prompt, 
                    callback=self.streaming_callback
                )
            else:
                # Otherwise use regular generation
                llm_response = llm_service.generate_response(prompt)
            
            print(f"[FLOW] LLM teaching guidance generation completed")
            print(f"[DEBUG_LLM_OUTPUT] 原始LLM输出前200字符: {llm_response[:200]}")
            print(f"[DEBUG_LLM_OUTPUT] 检查数字: {[char for char in llm_response[:100] if char.isdigit()]}")
            
            return llm_response
            
        except Exception as e:
            print(f"[ERROR] LLM teaching guidance generation failed: {str(e)}")
            # Fallback to basic template suggestions
            return self._generate_fallback_recommendations(courses_analysis)
    
    def _format_courses_data_for_llm(self, courses_analysis: Dict[str, Any]) -> str:
        """为LLM分析格式化课程数据"""
        
        courses = courses_analysis["courses"]
        total_videos = courses_analysis["total_videos"] 
        total_documents = courses_analysis["total_documents"]
        content_topics = courses_analysis["content_topics"]
        
        formatted_data = []
        formatted_data.append(f"教师共管理 {len(courses)} 门课程，包含 {total_videos} 个教学视频和 {total_documents} 个课程文档。")
        
        if content_topics:
            top_topics = content_topics[:15]
            formatted_data.append(f"主要知识点涵盖：{', '.join(top_topics)}")
        
        formatted_data.append("\n课程详细信息：")
        
        for i, course in enumerate(courses, 1):
            course_info = [
                f"{i}. 课程名称：{course['name']}",
                f"   课程描述：{course['description'] or '暂无描述'}",
                f"   视频数量：{course['videos_count']} 个",
                f"   文档数量：{course['documents_count']} 个",
            ]
            
            if course['keywords']:
                course_info.append(f"   知识点：{', '.join(course['keywords'][:10])}")
            
            if course['videos']:
                video_titles = [v['title'] for v in course['videos'][:5]]
                course_info.append(f"   主要视频：{', '.join(video_titles)}")
            
            if course['documents']:
                doc_titles = [d['title'] for d in course['documents'][:5]]
                course_info.append(f"   主要文档：{', '.join(doc_titles)}")
            
            formatted_data.append("\n".join(course_info))
            formatted_data.append("")
        
        return "\n".join(formatted_data)
    
    def _build_teaching_guidance_prompt(self, courses_data: str, scope: str) -> str:
        """构建LLM提示词用于教学指导"""
        
        base_prompt = f"""您是一位资深的教育专家和教学顾问。请根据以下教师的课程情况，提供专业的教学安排指导建议。

## 教师当前课程状况:
{courses_data}

## 分析要求:
请从以下维度进行深入分析并提供具体建议：

1. **课程结构分析**: 评估当前课程内容组成和资源配置的合理性
2. **教学安排建议**: 基于课程内容提供具体的教学计划和进度安排
3. **资源优化建议**: 针对视频、文档等教学资源的改进建议
4. **知识点规划**: 基于现有知识点，建议教学重点和难点处理方式
5. **教学方法建议**: 根据课程特点推荐合适的教学策略
6. **评估与反馈**: 建议如何评估教学效果和收集学生反馈
7. **实践活动设计**: 建议具体的课堂活动和实践环节
8. **学习路径优化**: 为学生设计清晰的学习路径和里程碑

## 输出要求:
- 请以专业但友好的语调回应
- 提供具体可执行的建议，避免泛泛而谈
- 针对不同课程特点给出个性化建议
- 兼顾教学的科学性和实用性
- 使用Markdown格式，结构清晰
- 字数控制在1000-1500字之间
- 必须用中文回复以便理解
- 每个建议都要具体到可操作的步骤
- 给出时间安排和优先级建议
- 提供具体的评估标准和指标

## 特别要求:
- 针对每门课程的具体情况给出差异化建议
- 考虑学生的学习特点和能力水平
- 结合现代教育技术和方法
- 提供可量化的教学目标和成果指标

"""

        # 根据scope调整关注重点
        if scope == "specific_course":
            base_prompt += "\n\n请特别关注针对单个课程的深入教学安排。"
        elif scope == "content_structure": 
            base_prompt += "\n\n请重点分析内容结构的合理性和改进方案。"
        else:  # comprehensive
            base_prompt += "\n\n请提供全面的教学指导建议。"
        
        return base_prompt
    
    def _generate_fallback_recommendations(self, courses_analysis: Dict[str, Any]) -> str:
        """生成备用基础建议（当LLM调用失败时使用）"""
        
        courses = courses_analysis["courses"]
        total_videos = courses_analysis["total_videos"]
        total_documents = courses_analysis["total_documents"]
        content_topics = courses_analysis["content_topics"]
        
        # 构建基础分析报告
        guidance_sections = []
        
        # 1. 课程概况分析
        guidance_sections.append("## 📊 课程概况分析")
        guidance_sections.append(f"您目前共管理 **{len(courses)}** 门课程，包含 **{total_videos}** 个教学视频和 **{total_documents}** 个课程文档。")
        
        if content_topics:
            top_topics = content_topics[:10]  # 显示前10个主要知识点
            guidance_sections.append(f"主要知识点涵盖：{', '.join(top_topics)}")
        
        guidance_sections.append("")
        
        # 2. 课程详细分析
        guidance_sections.append("## 📚 各课程详细分析")
        
        for course in courses:
            guidance_sections.append(f"### {course['name']}")
            
            # 资源统计
            guidance_sections.append(f"- **资源组成**: {course['videos_count']} 个视频，{course['documents_count']} 个文档")
            
            # 知识点覆盖
            if course['keywords']:
                guidance_sections.append(f"- **知识点覆盖**: {', '.join(course['keywords'][:8])}" + 
                                       (f" 等 {len(course['keywords'])} 个知识点" if len(course['keywords']) > 8 else ""))
            
            # 内容建议
            guidance_sections.append(f"- **教学建议**: ")
            
            if course['videos_count'] == 0:
                guidance_sections.append("  - ⚠️ 缺少教学视频，建议录制核心概念讲解视频")
            elif course['videos_count'] < 5:
                guidance_sections.append("  - 📹 可考虑增加更多教学视频，丰富教学内容")
            
            if course['documents_count'] == 0:
                guidance_sections.append("  - ⚠️ 缺少课程文档，建议添加课件、习题或参考资料")
            elif course['documents_count'] < 3:
                guidance_sections.append("  - 📄 建议补充更多辅助文档，如练习题、参考资料等")
            
            if not course['keywords']:
                guidance_sections.append("  - 🏷️ 建议为课程内容添加关键词标签，便于知识点管理")
            
            guidance_sections.append("")
        
        # 3. 教学安排建议
        guidance_sections.append("## 🎯 教学安排建议")
        
        # 根据课程数量给出不同建议
        if len(courses) == 1:
            guidance_sections.extend([
                "### 单课程深化策略",
                "- **内容规划**: 将课程内容分解为清晰的学习模块，每个模块包含核心视频+配套文档",
                "- **进度安排**: 建议按周次安排教学进度，确保学生有充分时间消化内容",
                "- **互动设计**: 每个模块后设置讨论或练习环节，提高学生参与度"
            ])
        elif len(courses) <= 3:
            guidance_sections.extend([
                "### 多课程协调策略", 
                "- **课程关联**: 分析课程间的知识点关联，建立前置和进阶关系",
                "- **时间分配**: 合理分配各课程的教学时间，避免学习负担过重",
                "- **资源复用**: 识别可跨课程使用的教学资源，提高教学效率"
            ])
        else:
            guidance_sections.extend([
                "### 课程体系管理策略",
                "- **体系化建设**: 构建完整的课程知识体系，明确各课程定位和目标",
                "- **分层教学**: 根据课程难度和学生基础，设计分层次的教学路径",
                "- **质量监控**: 定期评估各课程教学效果，及时调整教学策略"
            ])
        
        guidance_sections.append("")
        
        # 4. 个性化改进建议
        guidance_sections.append("## 💡 个性化改进建议")
        
        # 基于实际数据的建议
        avg_videos_per_course = total_videos / len(courses) if courses else 0
        avg_docs_per_course = total_documents / len(courses) if courses else 0
        
        if avg_videos_per_course < 3:
            guidance_sections.append("- 📹 **增加视频内容**: 平均每门课程视频较少，建议增加核心知识点讲解视频")
        
        if avg_docs_per_course < 2:
            guidance_sections.append("- 📚 **丰富文档资源**: 建议为每门课程准备更多配套资料，如PPT、练习题、参考资料等")
        
        if len(content_topics) < 10:
            guidance_sections.append("- 🏷️ **完善知识点标签**: 建议为课程内容添加更详细的知识点标签，便于知识图谱构建")
        
        # 5. 下一步行动计划
        guidance_sections.append("## 📋 下一步行动计划")
        guidance_sections.extend([
            "1. **短期目标（1-2周）**:",
            "   - 检查并补充缺失的基础教学资源",
            "   - 为现有内容添加知识点标签",
            "   - 制定详细的教学时间安排",
            "",
            "2. **中期目标（1个月）**:",
            "   - 录制或收集更多优质教学视频",
            "   - 建立课程间的知识关联图",
            "   - 设计学生学习评估方案",
            "",
            "3. **长期目标（一学期）**:",
            "   - 构建完整的课程体系",
            "   - 收集学生反馈并持续优化",
            "   - 探索新的教学方法和技术工具"
        ])
        
        return "\n".join(guidance_sections)
