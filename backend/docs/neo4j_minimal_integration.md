# Neo4j最小集成使用指南

## 🎯 最小化集成概述

这是一个最小化的Neo4j集成方案，只包含核心功能：
- 一次性数据迁移
- 双写同步机制（SQLite主存储 + Neo4j图查询）
- 增强的图查询API

## 📋 使用步骤

### 1. 安装Neo4j驱动
```bash
pip install neo4j
```

### 2. 配置环境变量
在`.env`文件中添加：
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

### 3. 启动Neo4j数据库
使用Docker（推荐）：
```bash
docker run -d \
  --name neo4j-wendao \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  neo4j:latest
```

### 4. 执行一次性数据迁移
```bash
cd backend
python migrate_to_neo4j_once.py
```

### 5. 使用集成的API
所有Neo4j增强功能已集成到主要的知识图谱API中，无需额外配置。

## 🔧 核心功能

### 1. 自动双写同步
现有的知识图谱服务会自动尝试同步到Neo4j：
- 如果Neo4j可用，数据会同步到图数据库
- 如果Neo4j不可用，只使用SQLite（不影响现有功能）

### 2. 增强的图查询API

#### 获取前置知识路径
```http
GET /api/knowledge-graph/prerequisite-path?keyword=面向对象编程
```

#### 获取智能推荐
```http
GET /api/knowledge-graph/recommendations?keyword=Python基础语法
```

#### 检查同步状态
```http
GET /api/knowledge-graph/sync-status
```

### 3. 降级机制
- Neo4j不可用时，自动降级到SQLite查询
- 保证现有功能完全不受影响

## 🔗 与现有代码的集成

### 在知识图谱处理器中使用
```python
# 在 tasks/knowledge_graph_processor.py 中
from services.knowledge_graph_service import get_query_service

def some_processing_method(self):
    query_service = get_query_service()
    
    # 使用增强的图查询功能
    prerequisites = query_service.find_prerequisite_knowledge("目标知识点")
    recommendations = query_service.get_smart_recommendations("当前知识点")
```

### 在其他服务中使用
```python
from services.knowledge_graph_service import get_neo4j_adapter

adapter = get_neo4j_adapter()
if adapter.is_available():
    # 使用Neo4j增强功能
    related_keywords = adapter.get_related_keywords(keyword_id)
else:
    # 降级到传统方法
    pass
```

## 📂 文件结构
```
backend/
├── services/
│   └── knowledge_graph_service.py  # 已更新：添加Neo4j适配器
├── routes/
│   └── knowledge_graph.py  # 已更新：集成Neo4j增强API
├── migrate_to_neo4j_once.py  # 一次性迁移脚本（用完删除）
└── docs/
    └── neo4j_minimal_integration.md  # 本文档
```

## ⚠️ 重要说明

1. **向后兼容**：所有现有功能保持不变
2. **可选功能**：Neo4j功能是增强性的，不是必需的
3. **零风险**：Neo4j故障不会影响主业务
4. **最小修改**：只在现有服务基础上添加功能

## 🚀 未来扩展

如果需要更多Neo4j功能，可以在此基础上添加：
- 复杂图算法（PageRank、社区发现）
- 个性化学习路径生成
- 知识点难度评估

## 🔍 调试和监控

### 检查Neo4j连接状态
```python
from services.knowledge_graph_service import get_neo4j_adapter

adapter = get_neo4j_adapter()
print(f"Neo4j可用: {adapter.is_available()}")
```

### 查看Neo4j数据
访问 http://localhost:7474 使用Neo4j浏览器查看图数据

### 日志监控
所有Neo4j操作都会记录日志，便于调试和监控
