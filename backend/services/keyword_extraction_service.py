import threading
import re
import json
import jieba
from collections import Counter
from flask import current_app
from models.models import db, Question, Keyword, QuestionKeyword, Course, CourseKeyword
from services.llm_service import llm_service
from services.tokenization_cache_service import tokenization_cache_service
# from services.embeddings_service import embeddings_service  # 不再使用向量化
# from utils.video_processing_pool import video_processing_pool  # 不再需要线程池
import uuid

class KeywordExtractionService:
    def __init__(self):
        pass
    
    def _tokenize_chinese(self, text):
        """使用jieba进行中文分词（带缓存）"""
        if not text:
            return []
        return tokenization_cache_service.get_or_create_tokens(text, 'keyword_extraction')
    
    def _calculate_text_similarity(self, text1, text2):
        """计算两个文本的相似度（基于词汇重叠）"""
        # 分词
        tokens1 = self._tokenize_chinese(text1)
        tokens2 = self._tokenize_chinese(text2)
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # 计算词频
        counter1 = Counter(tokens1)
        counter2 = Counter(tokens2)
        
        # 计算交集
        intersection = sum((counter1 & counter2).values())
        
        # 计算并集
        union = sum((counter1 | counter2).values())
        
        # Jaccard相似度
        if union == 0:
            return 0.0
        
        jaccard_sim = intersection / union
        
        # 额外考虑关键词在题目中的出现情况
        keyword_in_question = 0
        for token in tokens2:
            if token in tokens1:
                keyword_in_question += 1
        
        keyword_coverage = keyword_in_question / len(tokens2) if tokens2 else 0
        
        # 综合相似度（Jaccard + 关键词覆盖率）
        final_similarity = 0.6 * jaccard_sim + 0.4 * keyword_coverage
        
        return final_similarity

    def extract_keywords(self, app, question_id, callback=None):
        """
        同步提取问题关键词并将其与题目关联到QuestionKeyword表
        :param app: Flask应用实例
        :param question_id: 问题ID
        :param callback: 可选，处理完成后的回调
        :return: result
        """
        with app.app_context():
            try:
                print(f"[调试] 进入extract_keywords, question_id={question_id}")
                # 1. 查询问题内容
                question = Question.query.get(question_id)
                if not question:
                    raise Exception("问题不存在")
                # 2. 获取问题关联的课程所有知识点
                course_keywords = []
                if question.course_id:
                    course_kws = CourseKeyword.query.filter_by(course_id=question.course_id).all()
                    course_keywords = [kw.keyword for kw in course_kws]
                
                # 3. 如果没有课程关联的知识点，则获取全局知识点
                if not course_keywords:
                    course_keywords = Keyword.query.all()
                
                # 4. 计算题目内容与所有知识点的文本相似度（基于分词）
                question_text = f"{question.content} {question.options if hasattr(question, 'options') and question.options else ''}"
                
                # 计算每个知识点与题目的相似度
                keyword_similarities = []
                for kw in course_keywords:
                    # 使用简单的文本相似度计算
                    similarity = self._calculate_text_similarity(question_text, kw.name)
                    keyword_similarities.append((kw, similarity))
                
                # 按相似度降序排序
                keyword_similarities.sort(key=lambda x: x[1], reverse=True)
                
                # 5. 构建包含所有知识点的上下文，让AI选择3-5个
                sorted_keywords = [kw for kw, _ in keyword_similarities]
                keyword_context = "\n".join([kw.name for kw in sorted_keywords])
                
                llm = llm_service.create_non_streaming_llm_lite_20()
                prompt = f"""请从以下知识点列表中选择3-5个与题目最相关的知识点，返回JSON格式的结果：

题目内容：
{question_text}

知识点列表：
{keyword_context}

请返回JSON格式，例如：{{"selected_keywords": ["数据结构", "算法复杂度", "排序算法"]}}"""
                
                
                # 使用正则表达式提取JSON并解析
                try:
                    response = llm.invoke(prompt)
                    # 使用正则表达式提取JSON部分
                    json_match = re.search(r'\{.*?\}', response.content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                        result_data = json.loads(json_str)
                        selected_keyword_names = result_data.get('selected_keywords', [])
                        
                        # 根据名称匹配知识点对象
                        matched_keywords = []
                        for name in selected_keyword_names:
                            for kw in sorted_keywords:
                                if kw.name == name:
                                    matched_keywords.append(kw)
                                    break
                    else:
                        raise ValueError("未找到JSON格式")
                        
                except (ValueError, json.JSONDecodeError, KeyError) as e:
                    print(f"[关键词提取调试] AI返回格式解析失败: {response.content}, 错误: {e}")
                    # 如果解析失败，则取前5个最相似的知识点
                    matched_keywords = sorted_keywords[:5]
                
                print(f"[关键词提取调试] AI选择的知识点: {[kw.name for kw in matched_keywords]}")
                # 4. 将查到的关键词与题目关联到QuestionKeyword表
                for kw in matched_keywords:
                    # 检查是否已存在关联，避免重复
                    exists = QuestionKeyword.query.filter_by(question_id=question_id, keyword_id=kw.id).first()
                    if not exists:
                        qk = QuestionKeyword(
                            question_id=question_id,
                            keyword_id=kw.id
                        )
                        db.session.add(qk)
                        print(f"[关键词创建] 题目ID: {question_id}, 关键词ID: {kw.id}, 关键词: {kw.name}")
                db.session.commit()
                # 5. 通过关键词查找可能关联的课程
                course_ids = set()
                for kw in matched_keywords:
                    for course_kw in kw.course_keywords:
                        course_ids.add(course_kw.course_id)
                # 6. 通过课程进一步查找相关知识点
                related_keywords = set()
                for course_id in course_ids:
                    course_keywords = CourseKeyword.query.filter_by(course_id=course_id).all()
                    for ck in course_keywords:
                        related_keywords.add(ck.keyword_id)
                # 7. 查询并返回 QuestionKeyword 关联数据
                question_keywords = QuestionKeyword.query.filter_by(question_id=question_id).all()
                result = {
                    "extracted_keywords": [kw.name for kw in matched_keywords],
                    "related_courses": list(map(str, course_ids)),
                    "related_keywords": list(map(str, related_keywords)),
                    "question_keywords": [qk.to_dict() for qk in question_keywords]
                }
                if callback:
                    callback(result)
                return result
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"关键词提取任务失败: {str(e)}")
                raise

# 全局实例
global_keyword_extraction_service = KeywordExtractionService()