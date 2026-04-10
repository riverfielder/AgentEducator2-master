import pathlib
import sys

ch5_path = pathlib.Path(r'D:\hxjbs\AgentEducator2-master\thesis\pages\chapter5.tex')
ch6_path = pathlib.Path(r'D:\hxjbs\AgentEducator2-master\thesis\pages\chapter6.tex')

# ---- Patch Chapter 5 ----
ch5_text = ch5_path.read_text(encoding='utf-8')

old_ch5 = r'''\subsection{基于标签隐语意的个性化课程推荐引擎实现}

虽然 AST 和 RAG 解决了微观层面的“题目辅导”和“视频解惑”，但系统要扣紧“基于大模型辅助个性化学习系统”的主题，必须在宏观教学路径上实现个性化。为此，系统整合了隐语义模型（Latent Factor Model, LFM）计算学生的能力图谱字典。

在数据流层面，后端通过 \texttt{Redis} 读取该学生近期 \texttt{CodeTaskRecord} 中的高频试错标签及其所属课程类型因子属性，并计算相似度。若冷启动数据不足时，则通过大预言模型提取用户初始自我描述中的需求特征作为初始化降维因子。部分核心计算实现如下：

\begin{lstlisting}[language=Python, caption=个性化推荐之学生近程试错降维推荐矩阵构建]
import numpy as np

def recommend_courses(user_id, learning_factors, all_courses):
    user_feature = learning_factors.get(user_id, np.random.rand(1, 10))
    scores = []
    # 抽取近期所有代码实训题目背后的 AST 重灾区标签特征矩阵
    for course in all_courses:
        course_vec = extract_course_vector(course.tags)
        # 用点积还原计算隐语义偏好度
        scores.append({
            "course": course,
            "match_score": np.dot(user_feature, course_vec)
        })
    # 根据掌握盲区实现个性化高优先推荐
    scores.sort(key=lambda x: x["match_score"], reverse=True)
    return [s["course"] for s in scores[:5]]
\end{lstlisting}'''

new_ch5 = r'''\subsection{基于微观 AST 掌握度与宏观知识图谱联动的大模型个性化引擎}

虽然 AST 和 RAG 解决了微观层面的“题目辅导”和“视频解惑”，但系统要扣紧“基于大模型辅助个性化学习系统”的主题，必须在教学路径与专项训练上实现双端个性化。通过对后端代码真实实现的剖析，本系统摒弃了传统的协同过滤等可能面临“冷启动”问题的查表算法，创新性地提出了【微观掌握度实时量化】结合【宏观知识图谱推演】的计算链路。

在微观训练路由（/generate-personalized）中，当学生的底层知识点（如“Python类的继承”）被判定为薄弱时，系统动态调度大模型针对性出题（涵盖单选、多选与主观代码题），以强迫学生进行补短板复练，主观题提交后再次辅以底层 AST 词法检测进行多维度判分；在宏观学习路径演进流中，系统查表获取用户当前的最高掌握度知识节点（KnowledgePointMastery），随后利用知识点间的上下游依赖（prerequisite、extends 等关联关系）计算出其紧前与紧后的前置或衍生知识域，最终交由统一的大语言模型决策中枢（UnifiedLLMService）作为 Prompt 动态预判其最合理的进阶学习曲线。其核心决策拼接思路的抽象部分实现如下：

\begin{lstlisting}[language=Python, caption=结合图谱游走与大语言模型的定制化推荐提示词推理拼接引擎]
def _build_ai_recommendation_prompt(self, knowledge_context, mastery_overview, limit):
    prompt = f"""
    你是一个智能学习路径推荐专家。请基于以下用户学习情况和知识图谱信息...
    ## 用户学习概览
    - 总学习知识点: {mastery_overview.get('total_keywords', 0)}
    - 平均掌握度: {mastery_overview.get('average_mastery', 0):.1%}
    ## 用户掌握较好的知识点（源知识点）
    """
    for keyword in knowledge_context['mastered_keywords']:
        prompt += f"- {keyword['name']} (掌握度: {keyword['mastery_level']:.1%})\n"

    prompt += "## 与以上知识点相关联的前置与衍生知识点（等待被推荐的知识点）\n"
    for option in knowledge_context['available_next_steps'][:20]:
         # 基于知识图谱的（extends/prerequisite）等关系注入
         prompt += f"- {option['name']} (分类: {option['category']})\n"
         
    return prompt
\end{lstlisting}
由上述代码可知，算法在保留纯图推理的严谨性的同时，利用大语言模型的自然语言理解能力替代了传统硬编码的推荐算分逻辑，能够给出含有“推荐语”的精准柔性引导，具有较强的教学应用价值。'''

ch5_text = ch5_text.replace(old_ch5, new_ch5)
ch5_path.write_text(ch5_text, encoding='utf-8')


# ---- Patch Chapter 6 ----
ch6_text = ch6_path.read_text(encoding='utf-8')

old_ch6 = r'''协同过滤（User-Based CF）算法，结合学习者近期的代码题标签掌握度动态生成'''
new_ch6 = r'''知识领域能力图谱量化并联动大模型（LLM+KnowledgeGraph）动态推理生成'''

ch6_text = ch6_text.replace(old_ch6, new_ch6)
ch6_path.write_text(ch6_text, encoding='utf-8')

print("Patch applied.")
