"""知识点信息获取工具类"""

from typing import Dict, List, Any
from sqlalchemy import desc
from pydantic import BaseModel, Field
from models.models import (
    db, Keyword, KeywordRelation, KnowledgePointMastery,
    VideoKeyword, DocumentKeyword, QuestionKeyword,
    UserVideoProgress, DocumentProgress, StudentAnswer,
    Video, Document, Question, Assignment, Course
)
from services.mastery_calculator import MasteryCalculator
from .base_tool import BaseTool


class KnowledgePointSearchInput(BaseModel):
    """知识点信息查询的输入参数模型"""
    query: str = Field(description="**单个**知识点名称，支持模糊检索，但只能为一个词语或短语")


class KnowledgePointInfoTool(BaseTool):
    """知识点信息获取工具类，用于获取知识点的相关资源和关联信息，仅当用户明确指出要了解**某一个**特定“知识点”时使用。"""
    
    def __init__(self, user_id: str = None):
        super().__init__(user_id=user_id)
        self.mastery_calculator = MasteryCalculator()
    
    def get_related_videos(self, keyword_id: str, user_id: str) -> List[Dict[str, Any]]:
        """获取知识点相关的视频资源"""
        video_keywords = db.session.query(
            VideoKeyword, Video, Course
        ).join(
            Video, VideoKeyword.video_id == Video.id
        ).join(
            Course, Video.course_id == Course.id
        ).filter(
            VideoKeyword.keyword_id == keyword_id,
            Video.is_deleted == False,
            Course.is_deleted == False
        )
        
        # 根据权限过滤课程
        if self.accessible_courses:
            video_keywords = video_keywords.filter(
                Course.id.in_(self.accessible_courses)
            )
        
        video_keywords = video_keywords.all()
        
        related_videos = []
        for vk, video, course in video_keywords:
            progress = UserVideoProgress.query.filter_by(
                user_id=user_id, video_id=video.id
            ).first()
            
            related_videos.append({
                'id': str(video.id),
                'title': video.title,
                'description': video.description,
                'duration': video.duration,
                'cover_url': video.cover_url,
                'course_id': str(course.id),
                'course_name': course.name,
                'weight': vk.weight,
                'user_progress': progress.progress if progress else 0.0,
                'completed': progress.completed if progress else False,
                'last_position': progress.last_position if progress else 0
            })
        
        return related_videos
    
    def get_related_documents(self, keyword_id: str, user_id: str) -> List[Dict[str, Any]]:
        """获取知识点相关的文档资源"""
        document_keywords = db.session.query(
            DocumentKeyword, Document, Course
        ).join(
            Document, DocumentKeyword.document_id == Document.id
        ).join(
            Course, Document.course_id == Course.id
        ).filter(
            DocumentKeyword.keyword_id == keyword_id,
            Document.is_deleted == False,
            Course.is_deleted == False
        )
        
        # 根据权限过滤课程
        if self.accessible_courses:
            document_keywords = document_keywords.filter(
                Course.id.in_(self.accessible_courses)
            )
        
        document_keywords = document_keywords.all()
        
        related_documents = []
        for dk, document, course in document_keywords:
            progress = DocumentProgress.query.filter_by(
                user_id=user_id, document_id=document.id
            ).first()
            
            related_documents.append({
                'id': str(document.id),
                'title': document.title,
                'file_type': document.file_type,
                'file_size': document.file_size,
                'course_id': str(course.id),
                'course_name': course.name,
                'weight': dk.weight,
                'upload_time': document.upload_time.isoformat() if document.upload_time else None,
                'course_id': str(course.id),
                'course_name': course.name,
                'weight': dk.weight,
                'user_progress': progress.progress if progress else 0.0,
                'completed': progress.completed if progress else False,
                'reading_time': progress.reading_time if progress else 0
            })
        
        return related_documents
    
    def get_related_questions(self, keyword_id: str, user_id: str) -> List[Dict[str, Any]]:
        """获取知识点相关的练习题"""
        question_keywords = db.session.query(
            QuestionKeyword, Question, Assignment, Course
        ).join(
            Question, QuestionKeyword.question_id == Question.id
        ).join(
            Assignment, Question.assignment_id == Assignment.id
        ).join(
            Course, Assignment.course_id == Course.id
        ).filter(
            QuestionKeyword.keyword_id == keyword_id
        ).all()
        
        related_questions = []
        for qk, question, assignment, course in question_keywords:
            student_answer = StudentAnswer.query.filter_by(
                student_id=user_id, question_id=question.id
            ).order_by(desc(StudentAnswer.submit_time)).first()
            
            related_questions.append({
                'id': str(question.id),
                'content': question.content,
                'type': question.type,
                'difficulty_level': qk.difficulty_level,
                'weight': qk.weight,
                'assignment_id': str(assignment.id),
                'assignment_title': assignment.title,
                'course_id': str(course.id),
                'course_name': course.name,
                'user_answer': {
                    'answered': student_answer is not None,
                    'is_correct': student_answer.is_correct if student_answer else None,
                    'score': student_answer.score if student_answer else None,
                    'submit_time': student_answer.submit_time.isoformat() if student_answer and student_answer.submit_time else None
                } if student_answer else {'answered': False}
            })
        return related_questions
    
    def get_related_keywords(self, keyword_id: str, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """获取知识点的父子知识点，并批量计算掌握程度"""
        # 获取子知识点
        child_relations = KeywordRelation.query.filter_by(
            source_keyword_id=keyword_id
        ).all()
        
        child_keywords = []
        child_keyword_ids = []
        for relation in child_relations:
            child_keyword = Keyword.query.get(relation.target_keyword_id)
            if child_keyword:
                child_keyword_ids.append(str(child_keyword.id))
                child_keywords.append({
                    'id': str(child_keyword.id),
                    'name': child_keyword.name,
                    'category': child_keyword.category,
                    'description': child_keyword.description,
                    'relation_type': relation.relation_type,
                    'relation_strength': relation.strength,
                    'mastery_level': 0.0  # 将被批量更新
                })
        
        # 获取父知识点
        parent_relations = KeywordRelation.query.filter_by(
            target_keyword_id=keyword_id
        ).all()
        
        parent_keywords = []
        parent_keyword_ids = []
        for relation in parent_relations:
            parent_keyword = Keyword.query.get(relation.source_keyword_id)
            if parent_keyword:
                parent_keyword_ids.append(str(parent_keyword.id))
                parent_keywords.append({
                    'id': str(parent_keyword.id),
                    'name': parent_keyword.name,
                    'category': parent_keyword.category,
                    'description': parent_keyword.description,
                    'relation_type': relation.relation_type,
                    'relation_strength': relation.strength,
                    'mastery_level': 0.0  # 将被批量更新
                })
        
        # 批量计算所有相关知识点的掌握程度
        all_keyword_ids = child_keyword_ids + parent_keyword_ids
        if all_keyword_ids:
            mastery_results = self.mastery_calculator.batch_calculate_mastery(
                user_id=user_id, 
                keyword_ids=all_keyword_ids,
                force_recalculate=False,
                use_extended_cache=True
            )
            
            # 更新子知识点的掌握程度
            for child in child_keywords:
                if child['id'] in mastery_results:
                    mastery_info = mastery_results[child['id']]
                    child.update({
                        'mastery_level': mastery_info.get('mastery_level', 0.0),
                        'mastery_details': mastery_info.get('calculation_details', {}),
                        'material_score': mastery_info.get('material_progress', 0.0),
                        'exercise_score': mastery_info.get('exercise_score', 0.0),
                        'child_contribution': mastery_info.get('sub_knowledge_contribution', 0.0)
                    })
            
            # 更新父知识点的掌握程度
            for parent in parent_keywords:
                if parent['id'] in mastery_results:
                    mastery_info = mastery_results[parent['id']]
                    parent.update({
                        'mastery_level': mastery_info.get('mastery_level', 0.0),
                        'mastery_details': mastery_info.get('calculation_details', {}),
                        'material_score': mastery_info.get('material_progress', 0.0),
                        'exercise_score': mastery_info.get('exercise_score', 0.0),
                        'child_contribution': mastery_info.get('sub_knowledge_contribution', 0.0)
                    })
        
        return {
            'child_keywords': child_keywords,
            'parent_keywords': parent_keywords
        }
    
    def get_knowledge_point_info(self, keyword_id: str, user_id: str) -> Dict[str, Any]:
        """获取知识点的完整信息，包含当前知识点和所有相关子/父知识点的掌握程度"""
        def query_keyword_info():
            keyword = Keyword.query.get_or_404(keyword_id)
            mastery_info = self.mastery_calculator.calculate_mastery_level(user_id, keyword_id,force_recalculate=True)
            
            # 获取相关知识点信息（包含完整掌握程度）
            related_keywords = self.get_related_keywords(keyword_id, user_id)
            
            return {
                'keyword': {
                    'id': str(keyword.id),
                    'name': keyword.name,
                    'category': keyword.category,
                    'description': keyword.description,
                    'mastery_level': mastery_info.get('mastery_level', 0.0),
                    'mastery_details': mastery_info.get('calculation_details', {}),
                    'material_score': mastery_info.get('material_progress', 0.0),
                    'exercise_score': mastery_info.get('exercise_score', 0.0),
                    'child_contribution': mastery_info.get('sub_knowledge_contribution', 0.0)
                },
                'related_videos': self.get_related_videos(keyword_id, user_id),
                'related_documents': self.get_related_documents(keyword_id, user_id),
                'related_questions': self.get_related_questions(keyword_id, user_id),
                **related_keywords
            }
        
        result = self._execute_with_app_context(query_keyword_info)
        return result
    
    def search(self, query: str) -> str:
        """根据查询获取知识点信息"""
        try:
            print(f"[FLOW] KnowledgePointInfoTool.search 开始执行")
            print(f"[FLOW] 查询内容: {query}")
            print(f"[FLOW] 用户ID: {self.user_id}")
            
            # 查找匹配的知识点
            def find_keywords():
                keywords = Keyword.query.filter(
                    Keyword.name.ilike(f"%{query}%")
                ).all()
                return keywords
            
            keywords = self._execute_with_app_context(find_keywords)
            
            if not keywords:
                error_msg = f"未找到与'{query}'相关的知识点"
                self._notify_tool_result({
                    "success": False,
                    "message": error_msg,
                    "keywords_found": 0
                })
                return error_msg
            
            result_text = f"找到 {len(keywords)} 个相关知识点:\n\n"
            
            for keyword in keywords[:3]:  # 只显示前3个最相关的
                keyword_info = self.get_knowledge_point_info(str(keyword.id), self.user_id or "")
                keyword_data = keyword_info['keyword']
                
                result_text += f"**{keyword.name}**\n"
                if keyword.description:
                    result_text += f"描述: {keyword.description}\n"
                
                # 掌握程度信息
                mastery_level = keyword_data.get('mastery_level', 0.0)
                mastery_details = keyword_data.get('mastery_details', {})
                
                if mastery_level >= 0.8:
                    mastery_status = "优秀"
                elif mastery_level >= 0.6:
                    mastery_status = "良好"
                elif mastery_level >= 0.4:
                    mastery_status = "一般"
                elif mastery_level > 0:
                    mastery_status = "需要提高"
                else:
                    mastery_status = "未开始学习"
                
                result_text += f"掌握程度: {mastery_level:.1%} ({mastery_status})\n"
                
                # 如果有详细的掌握信息，显示关键指标
                if mastery_details:
                    video_mastery = mastery_details.get('video_mastery', 0)
                    doc_mastery = mastery_details.get('document_mastery', 0)
                    question_mastery = mastery_details.get('question_mastery', 0)
                    
                    if any([video_mastery, doc_mastery, question_mastery]):
                        result_text += f"- 视频学习: {video_mastery:.1%}, 文档阅读: {doc_mastery:.1%}, 练习正确率: {question_mastery:.1%}\n"
                
                # 相关视频
                if keyword_info['related_videos']:
                    result_text += f"相关视频 ({len(keyword_info['related_videos'])} 个):\n"
                    for video in keyword_info['related_videos'][:2]:
                        result_text += f"- {video['title']} (进度: {video['user_progress']:.1%})\n"
                
                # 相关文档
                if keyword_info['related_documents']:
                    result_text += f"相关文档 ({len(keyword_info['related_documents'])} 个):\n"
                    for doc in keyword_info['related_documents'][:2]:
                        result_text += f"- {doc['title']}\n"
                
                # 相关练习题（如果有的话）
                if keyword_info['related_questions']:
                    correct_count = sum(1 for q in keyword_info['related_questions'] 
                                      if q['user_answer']['answered'] and q['user_answer']['is_correct'])
                    total_count = len(keyword_info['related_questions'])
                    answered_count = sum(1 for q in keyword_info['related_questions'] 
                                       if q['user_answer']['answered'])
                    result_text += f"相关练习题: {total_count} 题 (已答: {answered_count}, 正确: {correct_count})\n"
                
                result_text += "\n"
            
            # 计算平均掌握程度用于通知
            total_mastery = 0.0
            mastery_count = 0
            
            for keyword in keywords[:3]:
                keyword_info = self.get_knowledge_point_info(str(keyword.id), self.user_id or "")
                mastery_level = keyword_info['keyword'].get('mastery_level', 0.0)
                total_mastery += mastery_level
                mastery_count += 1
            
            avg_mastery = total_mastery / mastery_count if mastery_count > 0 else 0.0
            
            self._notify_tool_result({
                "success": True,
                "message": f"找到 {len(keywords)} 个相关知识点，平均掌握程度: {avg_mastery:.1%}",
                "keywords_found": len(keywords),
                "average_mastery": avg_mastery
            })
            
            print(f"[FLOW] KnowledgePointInfoTool.search 执行完成")
            return result_text
            
        except Exception as e:
            error_msg = f"查询知识点信息失败: {str(e)}"
            print(f"[ERROR] {error_msg}")
            self._notify_tool_result({
                "success": False,
                "message": error_msg,
                "keywords_found": 0
            })
            return error_msg
    
    def get_display_info(self) -> Dict[str, Any]:
        """实现BaseTool的抽象方法"""
        return {
            'tool_name': '知识点信息工具',
            'tool_icon': 'mdi-lightbulb',
            'description': '用于获取知识点的相关资源和关联信息'
        }