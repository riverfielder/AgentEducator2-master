from services.llm_service import llm_service
import json
import re
import numpy as np
from collections import Counter
import jieba
from services.tokenization_cache_service import tokenization_cache_service

class AssignmentGradingService:
    """
    作业自动批改服务
    """

    @staticmethod
    def auto_grade_choice_question(question_type, options, student_answer, max_score=5):
        """
        自动批改选择题
        :param question_type: 题目类型 ('single' 或 'multiple')
        :param options: 选项列表，每个选项包含 content 和 isCorrect 字段
        :param student_answer: 学生答案（单选题为数字索引，多选题为数字索引数组）
        :param max_score: 满分
        :return: dict, 包含分数、是否正确、评语
        """
        try:
            if not options:
                return {
                    "score": 0,
                    "is_correct": False,
                    "comment": "题目选项不存在"
                }

            # 获取正确答案索引
            correct_indices = []
            for i, option in enumerate(options):
                if isinstance(option, dict) and option.get('isCorrect'):
                    correct_indices.append(i)
                elif isinstance(option, str):
                    # 处理简单字符串选项格式，这种情况下需要其他方式确定正确答案
                    pass

            if not correct_indices:
                return {
                    "score": 0,
                    "is_correct": False,
                    "comment": "未找到正确答案"
                }

            if question_type == 'single':
                # 单选题批改
                if student_answer is None:
                    return {
                        "score": 0,
                        "is_correct": False,
                        "comment": "未作答"
                    }

                # 处理学生答案格式
                try:
                    if isinstance(student_answer, str):
                        student_index = int(student_answer)
                    else:
                        student_index = int(student_answer)
                except (ValueError, TypeError):
                    return {
                        "score": 0,
                        "is_correct": False,
                        "comment": "答案格式错误"
                    }

                # 检查答案是否正确
                is_correct = student_index in correct_indices
                score = max_score if is_correct else 0

                return {
                    "score": score,
                    "is_correct": is_correct,
                    "comment": "正确" if is_correct else f"错误，正确答案是{chr(65 + correct_indices[0])}"
                }

            elif question_type == 'multiple':
                # 多选题批改
                if student_answer is None:
                    return {
                        "score": 0,
                        "is_correct": False,
                        "comment": "未作答"
                    }

                # 处理学生答案格式
                try:
                    if isinstance(student_answer, str):
                        student_indices = json.loads(student_answer) if student_answer.startswith('[') else [int(student_answer)]
                    elif isinstance(student_answer, list):
                        student_indices = [int(x) for x in student_answer]
                    else:
                        student_indices = [int(student_answer)]
                except (ValueError, TypeError, json.JSONDecodeError):
                    return {
                        "score": 0,
                        "is_correct": False,
                        "comment": "答案格式错误"
                    }

                # 检查答案是否完全正确
                student_set = set(student_indices)
                correct_set = set(correct_indices)
                
                if student_set == correct_set:
                    # 完全正确
                    return {
                        "score": max_score,
                        "is_correct": True,
                        "comment": "正确"
                    }
                elif student_set.intersection(correct_set):
                    # 部分正确，按比例给分
                    correct_count = len(student_set.intersection(correct_set))
                    wrong_count = len(student_set - correct_set)
                    missing_count = len(correct_set - student_set)
                    
                    # 部分分数计算：正确选项得分，错误选项扣分
                    partial_score = max(0, (correct_count - wrong_count) / len(correct_set) * max_score)
                    
                    correct_options = [chr(65 + i) for i in correct_indices]
                    return {
                        "score": round(partial_score, 1),
                        "is_correct": False,
                        "comment": f"部分正确，正确答案是{''.join(correct_options)}"
                    }
                else:
                    # 完全错误
                    correct_options = [chr(65 + i) for i in correct_indices]
                    return {
                        "score": 0,
                        "is_correct": False,
                        "comment": f"错误，正确答案是{''.join(correct_options)}"
                    }

        except Exception as e:
            return {
                "score": 0,
                "is_correct": False,
                "comment": f"批改过程出错: {str(e)}"
            }

    @staticmethod
    def auto_grade_fill_blank_question(question, standard_answer, student_answer, max_score=5, grading_criteria=None):
        """
        自动批改填空题
        :param question: 题目内容
        :param standard_answer: 标准答案
        :param student_answer: 学生答案
        :param max_score: 满分
        :param grading_criteria: 评分标准（可选）
        :return: dict, 包含分数、是否正确、评语
        """
        try:
            if not student_answer or student_answer.strip() == "":
                return {
                    "score": 0,
                    "is_correct": False,
                    "comment": "未作答"
                }
            
            # 调用大模型进行填空题批改
            result = AssignmentGradingService.grade_answer(
                question=question,
                standard_answer=standard_answer,
                student_answer=student_answer,
                score_full=max_score,
                grading_criteria=grading_criteria or "准确性、完整性、表达清晰度"
            )
            
            return result
            
        except Exception as e:
            return {
                "score": 0,
                "is_correct": False,
                "comment": f"批改过程出错: {str(e)}"
            }

    @staticmethod
    def grade_answer(question, standard_answer, student_answer, score_full=5, grading_criteria=None):
        """
        调用大模型对学生答案进行自动评分
        :param question: 题目内容
        :param standard_answer: 标准答案
        :param student_answer: 学生答案
        :param score_full: 满分
        :param grading_criteria: 评分标准（可选）
        :return: dict, 包含分数、评语、批注等
        """
        # 构造 prompt
        prompt = f"""
你是一名公平、公正的教师，请根据以下信息对学生作答进行评分和点评。
题目：{question}
标准答案：{standard_answer}
学生答案：{student_answer}
评分标准：{grading_criteria or '准确性、完整性、表达清晰度'}

评分要求：
1. 请详细分析学生答案的优点和不足
2. 对于有一定道理或部分正确的答案，应给予相应分数
3. 即使答案不够完美，但能看出学生有思考和努力，可酌情给予"辛苦分"
4. 鼓励学生的学习态度和思考过程

请按照满分{score_full}分进行评分，返回如下JSON格式：
{{
  \"score\": int, // 得分
  \"is_correct\": bool, // 是否答对
  \"comment\": str // 教师评语
}}
        """

        try:
            llm = llm_service.create_non_streaming_llm_lite_20()
            result = llm.invoke(prompt)
            # 兼容 BaseMessage 类型，取 content 属性，否则转为字符串
            if hasattr(result, 'content'):
                result_str = result.content
            else:
                result_str = result
            # 如果 result_str 是 list，转为字符串
            if isinstance(result_str, list):
                result_str = '\n'.join([str(item) for item in result_str])
            else:
                result_str = str(result_str)
            # 用正则提取第一个JSON对象
            json_match = re.search(r'\{[\s\S]*?\}', result_str)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = result_str
            try:
                data = json.loads(json_str)
                return data
            except Exception:
                # JSON解析失败，使用兜底的余弦相似度计算
                print(f"LLM返回内容JSON解析失败，使用余弦相似度兜底计算。原始内容：{result_str}")
                return AssignmentGradingService.fallback_cosine_similarity_grading(
                    question, standard_answer, student_answer, score_full, grading_criteria
                )
        except Exception as e:
            # LLM调用失败，使用兜底的余弦相似度计算
            print(f"LLM调用失败，使用余弦相似度兜底计算。错误信息：{str(e)}")
            return AssignmentGradingService.fallback_cosine_similarity_grading(
                question, standard_answer, student_answer, score_full, grading_criteria
            )

    @staticmethod
    def fallback_cosine_similarity_grading(question, standard_answer, student_answer, score_full=5, grading_criteria=None):
        """
        兜底的余弦相似度计算函数，用于在LLM服务不可用时进行评分
        :param question: 题目内容
        :param standard_answer: 标准答案
        :param student_answer: 学生答案
        :param score_full: 满分
        :param grading_criteria: 评分标准（可选）
        :return: dict, 包含分数、评语、批注等
        """
        try:
            if not student_answer or student_answer.strip() == "":
                return {
                    "score": 0,
                    "is_correct": False,
                    "comment": "未作答"
                }
            
            # 计算余弦相似度
            similarity = AssignmentGradingService._calculate_cosine_similarity(
                standard_answer, student_answer
            )
            
            # 基于相似度计算分数
            if similarity >= 0.9:
                score = score_full
                is_correct = True
                comment = f"答案非常准确，与标准答案相似度为{similarity:.2f}"
            elif similarity >= 0.7:
                score = score_full * 0.8
                is_correct = False
                comment = f"答案基本正确，与标准答案相似度为{similarity:.2f}，建议进一步完善表达"
            elif similarity >= 0.5:
                score = score_full * 0.6
                is_correct = False
                comment = f"答案部分正确，与标准答案相似度为{similarity:.2f}，需要补充关键内容"
            elif similarity >= 0.3:
                score = score_full * 0.4
                is_correct = False
                comment = f"答案有一定相关性，与标准答案相似度为{similarity:.2f}，但缺少重要内容"
            else:
                score = score_full * 0.2
                is_correct = False
                comment = f"答案与标准答案差异较大，相似度为{similarity:.2f}，建议重新思考"
            
            return {
                "score": round(score, 1),
                "is_correct": is_correct,
                "comment": comment
            }
            
        except Exception as e:
            return {
                "score": 0,
                "is_correct": False,
                "comment": f"兜底评分过程出错: {str(e)}"
            }
    
    @staticmethod
    def _calculate_cosine_similarity(text1, text2):
        """
        计算两个文本的余弦相似度
        :param text1: 文本1（标准答案）
        :param text2: 文本2（学生答案）
        :return: float, 余弦相似度值 (0-1)
        """
        try:
            # 使用jieba进行中文分词
            tokens1 = AssignmentGradingService._tokenize_text(text1)
            tokens2 = AssignmentGradingService._tokenize_text(text2)
            
            if not tokens1 or not tokens2:
                return 0.0
            
            # 构建词汇表
            vocabulary = list(set(tokens1 + tokens2))
            
            if not vocabulary:
                return 0.0
            
            # 构建词频向量
            vector1 = AssignmentGradingService._build_frequency_vector(tokens1, vocabulary)
            vector2 = AssignmentGradingService._build_frequency_vector(tokens2, vocabulary)
            
            # 计算余弦相似度
            dot_product = np.dot(vector1, vector2)
            norm1 = np.linalg.norm(vector1)
            norm2 = np.linalg.norm(vector2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            cosine_similarity = dot_product / (norm1 * norm2)
            return max(0.0, min(1.0, cosine_similarity))  # 确保结果在[0,1]范围内
            
        except Exception as e:
            print(f"计算余弦相似度时出错: {str(e)}")
            return 0.0
    
    @staticmethod
    def _tokenize_text(text):
        """
        对文本进行分词处理
        :param text: 输入文本
        :return: list, 分词结果
        """
        if not text:
            return []
        
        try:
            # 使用缓存的分词服务
            tokens = tokenization_cache_service.get_or_create_tokens(text, 'assignment_grading')
            # 过滤掉停用词和标点符号
            filtered_tokens = [token for token in tokens if len(token.strip()) > 1 and token.isalnum()]
            return filtered_tokens
        except Exception:
            # 如果缓存服务不可用，直接使用jieba
            tokens = list(jieba.cut(text))
            filtered_tokens = [token for token in tokens if len(token.strip()) > 1 and token.isalnum()]
            return filtered_tokens
    
    @staticmethod
    def _build_frequency_vector(tokens, vocabulary):
        """
        构建词频向量
        :param tokens: 分词结果
        :param vocabulary: 词汇表
        :return: numpy array, 词频向量
        """
        token_counts = Counter(tokens)
        vector = np.zeros(len(vocabulary))
        
        for i, word in enumerate(vocabulary):
            vector[i] = token_counts.get(word, 0)
        
        return vector