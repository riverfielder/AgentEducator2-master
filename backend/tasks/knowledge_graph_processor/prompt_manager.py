"""知识图谱处理器提示词管理器"""

class PromptManager:
    """提示词管理器"""
    
    @staticmethod
    def get_keyword_classification_prompt():
        """获取知识点分类提示词"""
        return """
你是一个专业的教育内容分析师。请将以下知识点按照重要性和层次进行分类。

分类标准：
      1. 一级知识点 (core_concept): 领域或课程最核心、最顶层的概念。通常是高度概括性的术语，构成了整个知识体系的基础。
         - 例如: "软件工程", "计算机网络", "机器学习","软件", "软件工程",
      2. 二级知识点 (main_module): 构成一级知识点的关键组成部分或主要分支。通常是课程中的主要章节或核心模块。
         - 例如:       "需求工程", "软件设计", "软件测试", "软件部署", "软件维护", 
              "软件项目管理", "软件过程", "软件开发方法", "用例建模", "需求建模",
              "软件体系结构设计", "用户界面设计", "软件详细设计", "编码实现",
              "敏捷开发", "瀑布模型", "面向对象设计", "单元测试","UML建模",
      3. 三级知识点 (specific_point): 对二级知识点的具体展开，包括具体的技术、方法、工具、算法或实例。
         - 例如: "面向对象设计", "HTTP协议", "支持向量机"
          "Scrum方法", "用例图设计", "白盒测试技术", "代码审查流程",
          "需求获取", "内聚性", "耦合性"
            
请严格按照以下JSON格式返回结果：
{{
  "classifications": [
    {{
      "keyword": "知识点名称",
      "category": "core_concept/main_module/specific_point",
      "reason": "分类理由"
    }}
  ]
}}

需要分类的知识点：
{keywords}

请确保：
1. 每个知识点都必须分类
2. 分类要合理，符合教育层次
3. 返回有效的JSON格式
"""
    
    @staticmethod
    def get_relation_analysis_prompt():
        """获取关系分析提示词"""
        return """
你是一个专业的知识图谱分析师。请你确定以下知识点是否有关系，并分析它们之间的具体关系。

关系类型定义：
1. prerequisite：前置关系，A是B的前提条件
2. related：相关关系，A和B在概念上相关但无明确依赖
3. contains：包含关系，A包含B作为其组成部分

分析规则：
- 只建立有意义的关系，避免过度连接。只保留**最明显、最显著、最直接**的前5个关系。
- 优先建立prerequisite关系
- 同级别知识点主要建立related关系
- 上级概念对下级概念建立contains关系

请严格按照以下JSON格式返回：
{{
  "relations": [
    {{
      "source": "源知识点",
      "target": "目标知识点", 
      "relation_type": "prerequisite/related/contains",
      "strength": 0.8,
      "reason": "关系建立理由"
    }}
  ]
}}

课程信息：{course_info}

待分析的知识点：
{keywords}

请分析这些知识点之间的关系。
"""
    
    @staticmethod
    def get_cross_level_relation_prompt():
        """获取跨级别关系分析提示词"""
        return """
你是一个专业的知识图谱分析师。请你确定以下知识点是否有关系，并分析它们之间的具体关系。

当前分析：{level1_name} 与 {level2_name} 之间的关系

关系类型：
1. prerequisite：前置关系
2. related：相关关系  
3. contains：包含关系

分析重点：
- {level1_name}通常是更高层次的概念
- 重点关注contains和prerequisite关系
- 避免建立过多的related关系
- 只保留**最明显、最显著、最直接**的前3个关系
- 如果输入中有重复的知识点，请去重后再分析

请严格按照JSON格式返回：
{{
  "relations": [
    {{
      "source": "源知识点",
      "target": "目标知识点",
      "relation_type": "prerequisite/related/contains", 
      "strength": 0.8,
      "reason": "关系理由"
    }}
  ]
}}

{level1_name}知识点：
{level1_keywords}

{level2_name}知识点：
{level2_keywords}
"""
    
    @staticmethod
    def get_cluster_relation_prompt():
        """获取聚类关系分析提示词"""
        return """
你是一个专业的知识图谱分析师。请分析聚类内知识点之间的关系。

这些知识点因为相似性被聚类在一起，请分析它们之间的具体关系。

关系类型：
1. prerequisite：前置关系
2. related：相关关系
3. contains：包含关系
4. similar：相似关系

分析要点：
- 聚类内的知识点通常有较强的相关性
- 重点识别prerequisite和contains关系
- 适当建立similar关系表示概念相似

请严格按照JSON格式返回：
{{
  "relations": [
    {{
      "source": "源知识点",
      "target": "目标知识点",
      "relation_type": "prerequisite/related/contains/similar",
      "strength": 0.8,
      "reason": "关系理由"
    }}
  ]
}}

课程信息：{course_info}
聚类相似度：{similarity:.3f}

聚类内知识点：
{keywords}
"""
    
    @staticmethod
    def get_orphaned_keywords_prompt():
        """获取孤立知识点连接提示词"""
        return """
你是一个专业的知识图谱分析师。请为孤立的知识点建立与已有知识点的关系。

孤立知识点是指在知识图谱中没有任何关系连接的知识点。
请分析这些孤立知识点与已连接知识点之间可能的关系。

关系类型：
1. prerequisite：前置关系
2. related：相关关系
3. contains：包含关系

分析原则：
- 每个孤立知识点至少建立1-2个关系
- 优先与相关度高的知识点建立关系
- 避免建立过于牵强的关系

请严格按照JSON格式返回：
{{
  "relations": [
    {{
      "source": "源知识点",
      "target": "目标知识点",
      "relation_type": "prerequisite/related/contains",
      "strength": 0.8,
      "reason": "关系理由"
    }}
  ]
}}

孤立知识点：
{orphaned_keywords}

可连接的知识点：
{connected_keywords}

请为孤立知识点建立合适的关系。
"""
    
    @staticmethod
    def get_incremental_relation_prompt():
        """获取增量关系分析提示词"""
        return """
你是一个专业的知识图谱分析师。请分析新知识点与现有知识点之间的关系。

这是增量处理模式，需要将新提取的知识点与已有的知识图谱进行整合。

关系类型：
1. prerequisite：前置关系
2. related：相关关系  
3. contains：包含关系

分析重点：
- 新知识点与现有知识点的关系
- 保持知识图谱的一致性
- 避免重复建立已存在的关系

请严格按照JSON格式返回：
{{
  "relations": [
    {{
      "source": "源知识点",
      "target": "目标知识点",
      "relation_type": "prerequisite/related/contains",
      "strength": 0.8,
      "reason": "关系理由"
    }}
  ]
}}

新知识点：
{new_keywords}

现有知识点：
{existing_keywords}

请分析新旧知识点之间的关系。
"""