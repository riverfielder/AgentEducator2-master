# 🎓 闻道智能学习平台
*AgentEducator - Next-Generation AI-Powered Intelligent Learning Platform*

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.5-green.svg)](https://vuejs.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1-orange.svg)](https://flask.palletsprojects.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-purple.svg)](https://langchain.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8-blue.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**基于大语言模型的下一代智能教育平台，重新定义数字化教学体验**

[快速开始](#🚀-快速开始) • [技术架构](#🏗️-技术架构) • [核心特性](#✨-核心特性) • [部署指南](#📦-部署指南) • [API文档](#📖-api文档)

</div>

---

## 📖 项目概述

闻道智能学习平台是武汉大学计算机学院2023届软件过程课程小组开发的新一代AI驱动的在线教育平台。平台基于**大语言模型Agent架构**、**知识图谱技术**和**多模态内容理解**，为教育场景提供智能化、个性化的教学与学习解决方案。

### 🎯 设计理念

- **AI原生**: 以大语言模型为核心的智能化架构，提供自然语言交互体验
- **多模态融合**: 支持文本、视频、音频等多种内容形式的智能处理与理解
- **知识驱动**: 基于知识图谱的智能推荐与关联分析
- **体验至上**: 现代化设计语言，流畅的用户交互体验

## 🏗️ 技术架构

### Agent智能问答架构

```mermaid
graph TB
    A[用户输入] --> B[Agent调度器]
    B --> C{上下文分析}
    C -->|视频问题| D[VideoSearchTool]
    C -->|课程问题| E[CourseSearchTool]
    C -->|文档问题| F[DocumentSearchTool]
    C -->|通用问题| G[GeneralKnowledgeTool]
    
    D --> H[RAG检索]
    E --> H
    F --> H
    G --> H
    
    H --> I[LLM推理]
    I --> J[流式响应]
    J --> K[用户界面]
```

### 核心技术栈

#### 🤖 AI与机器学习
```
LangChain 0.3.26      # LLM应用开发框架
LangGraph 0.2.74      # Agent工作流编排
OpenAI GPT-4/3.5      # 大语言模型
LangSmith             # LLM应用监控与调试
Tiktoken              # Token计算与管理
RAG (检索增强生成)     # 知识检索与生成
```

#### 📊 数据处理与存储
```
MySQL 8.0+            # 关系型数据库
Neo4j                 # 图数据库 (知识图谱)
FAISS/ChromaDB        # 向量数据库
SQLAlchemy 2.0        # Python ORM
pandas 2.2.3          # 数据分析
```

#### 🎥 多媒体处理
```
FFmpeg 4.0+           # 视频处理引擎
Whisper ASR           # 语音识别
PaddleOCR             # 光学字符识别
OpenCV 4.9            # 计算机视觉
CNocr 2.3.1           # 中文OCR识别
ImageHash 4.3.2       # 图像去重与相似度
```

#### 🖥️ 前端技术
```
Vue 3.5.17            # 渐进式前端框架
TypeScript 5.8        # 静态类型检查
Vuetify 3.7           # Material Design组件库
ECharts 5.6           # 数据可视化
Vite 6.2              # 现代化构建工具
Pinia 3.0             # 状态管理
```

#### ⚙️ 后端服务
```
Flask 3.1.1           # Web应用框架
Flask-CORS 5.0        # 跨域资源共享
PyJWT 2.10            # JWT认证
Werkzeug 3.1          # WSGI工具库
python-dotenv 1.1     # 环境变量管理
```

## ✨ 核心特性

### 🤖 智能Agent问答系统

#### 多模式RAG架构
- **通用模式**: 基于大语言模型的通用知识问答
- **视频模式**: 针对视频内容的精准检索与问答
- **课程模式**: 基于课程资料的专业知识问答
- **文档模式**: 支持多格式文档的智能解析与问答

#### Agent工具链
```python
# 核心工具集
tools = [
    VideoSearchTool(),      # 视频内容检索
    CourseSearchTool(),     # 课程资料检索  
    DocumentSearchTool(),   # 文档内容检索
    GeneralKnowledgeTool(), # 通用知识问答
    AssignmentTool(),       # 作业相关工具
    LearningAnalyticsTool() # 学习分析工具
]
```

#### 流式对话体验
- **SSE流式传输**: 实时响应用户输入
- **上下文记忆**: 支持多轮对话上下文
- **工具调用追踪**: 透明的推理过程展示
- **错误恢复**: 智能错误处理与重试机制

### 📚 智能文档处理系统

#### 多步骤处理流水线
```python
processing_steps = [
    'markitdown',  # 文档格式转换
    'segment',     # 智能文档分段
    'vector',      # 向量化索引
    'summary'      # 智能摘要生成
]
```

#### 支持格式
- **Office文档**: Word、Excel、PowerPoint
- **PDF文档**: 学术论文、教材、报告
- **图像文件**: JPG、PNG、WebP等
- **网页内容**: HTML、Markdown

#### 处理能力
- **Markitdown转换**: 智能格式标准化
- **语义分段**: 基于内容结构的智能分割
- **向量化索引**: 支持语义检索的向量化处理
- **自动摘要**: AI生成的文档摘要与关键词

### 🕸️ 知识图谱系统

#### 图数据库架构
```cypher
// 知识点节点
(k:Keyword {id, name, category, description})

// 知识点关系
(k1:Keyword)-[r:RELATES {type, strength}]->(k2:Keyword)

// 内容关联
(v:Video)-[r:CONTAINS_KEYWORD {weight}]->(k:Keyword)
(c:Course)-[r:INCLUDES_KEYWORD {video_count}]->(k:Keyword)
```

#### 智能分析功能
- **前置知识路径**: 自动构建学习路径推荐
- **知识点关联**: 基于内容相似度的关联分析
- **学习序列推荐**: 个性化的学习顺序建议
- **知识缺口分析**: 识别学习薄弱环节

### 🎥 多模态视频处理

#### 视频内容理解
```python
video_processing_pipeline = [
    KeyframeExtraction(),   # 关键帧提取
    OCRProcessor(),         # 文字识别
    ASRProcessor(),         # 语音识别  
    VectorIndexer(),        # 向量化索引
    SummaryGenerator()      # 摘要生成
]
```

#### 技术特性
- **智能关键帧**: 基于视觉特征的关键帧提取
- **高精度OCR**: 支持中英文混合识别
- **语音转文字**: Whisper驱动的高质量转录
- **自动字幕**: AI生成的时间轴字幕
- **内容摘要**: 视频内容的智能摘要与标签

### 📝 智能作业系统

#### 多题型支持
- **单选题**: 自动批改，即时反馈
- **多选题**: 支持部分分数计算
- **填空题**: AI智能批改与评分
- **问答题**: 基于语义理解的智能评估

#### 批改特性
```python
grading_features = {
    "auto_grading": True,        # 自动批改
    "ai_scoring": True,          # AI评分
    "batch_processing": True,    # 批量处理
    "progress_tracking": True,   # 进度跟踪
    "export_results": True       # 结果导出
}
```

#### 教师工具
- **可视化界面**: 直观的批改操作界面
- **批量操作**: 一键批改所有选择题
- **智能评语**: AI生成的详细反馈
- **统计分析**: 班级成绩分析与趋势

### 📊 学习分析仪表板

#### 数据可视化
- **实时统计**: 学习行为实时监控
- **趋势分析**: 基于历史数据的趋势预测
- **个性化报告**: 个性化学习报告生成
- **多维度分析**: 时间、课程、知识点等多维度分析

#### 分析模型
```python
analytics_models = {
    "engagement_analysis": "参与度分析",
    "progress_tracking": "学习进度跟踪", 
    "knowledge_mastery": "知识掌握度评估",
    "learning_path": "学习路径优化"
}
```

## 🚀 快速开始

### 系统要求

```bash
# 基础环境
Python 3.8+          # 后端运行环境
Node.js 18+          # 前端构建环境
MySQL 8.0+           # 关系型数据库
Redis 6.0+           # 缓存数据库
FFmpeg 4.0+          # 视频处理工具

# 可选组件
Neo4j 5.0+           # 知识图谱数据库
Elasticsearch 8.0+   # 全文搜索引擎
```

### 快速安装

#### 1. 克隆项目
```bash
git clone https://github.com/your-org/AgentEducator.git
cd AgentEducator
```

#### 2. 后端安装
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
cd backend
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等
```

#### 3. 前端安装
```bash
cd frontend
npm install

# 配置环境
cp .env.example .env.local
# 编辑环境变量
```

#### 4. 数据库初始化
```bash
# 创建MySQL数据库
mysql -u root -p
CREATE DATABASE wendao_platform DEFAULT CHARACTER SET utf8mb4;

# 执行数据库迁移
cd backend
python run_migration.py
```

#### 5. 启动服务
```bash
# 启动后端服务
cd backend
python app.py

# 启动前端服务 (新终端)
cd frontend  
npm run dev
```

访问 `http://localhost:5173` 即可使用平台。

### Docker部署

```bash
# 使用Docker Compose快速部署
docker-compose up -d

# 查看服务状态
docker-compose ps
```

## 📖 API文档

### Agent问答API

```bash
# 创建问答会话
POST /api/qa/chat
{
  "message": "什么是机器学习？",
  "mode": "general",
  "context": {
    "course_id": "uuid",
    "video_id": "uuid"
  }
}

# 流式响应
GET /api/qa/stream/{session_id}
```

### 文档处理API

```bash
# 上传文档
POST /api/documents/upload

# 处理文档
POST /api/documents/{id}/process
{
  "steps": ["markitdown", "segment", "vector", "summary"]
}

# 查询处理状态
GET /api/documents/{id}/status
```

### 知识图谱API

```bash
# 获取课程知识图谱
GET /api/knowledge-graph/course/{course_id}

# 查询知识点关联
GET /api/knowledge-graph/related/{keyword_id}

# 获取学习路径
GET /api/knowledge-graph/learning-path/{target_keyword}
```

## 🔧 配置指南

### 环境变量配置

```bash
# 数据库配置
DATABASE_URL=mysql://user:password@localhost/wendao_platform
REDIS_URL=redis://localhost:6379/0
NEO4J_URI=bolt://localhost:7687

# AI模型配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4o-mini

# LangSmith配置 (可选)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=AgentEducator-QA

# 文件存储配置
UPLOAD_FOLDER=./uploads
MAX_CONTENT_LENGTH=100MB

# 视频处理配置
FFMPEG_PATH=/usr/bin/ffmpeg
TEMP_FOLDER=./temp

# 安全配置
JWT_SECRET_KEY=your_secret_key
CORS_ORIGINS=http://localhost:5173
```

### Agent配置

```python
# config/agent_config.py
AGENT_CONFIG = {
    "max_iterations": 10,
    "verbose": True,
    "handle_parsing_errors": True,
    "tools": {
        "video_search": {"enabled": True, "max_docs": 5},
        "course_search": {"enabled": True, "max_docs": 6},
        "document_search": {"enabled": True, "max_docs": 5}
    }
}
```

## 🤝 贡献指南

我们欢迎社区贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细的贡献指南。

### 开发工作流

```bash
# 1. Fork项目
# 2. 创建特性分支
git checkout -b feature/amazing-feature

# 3. 提交更改
git commit -m 'Add some amazing feature'

# 4. 推送到分支
git push origin feature/amazing-feature

# 5. 创建Pull Request
```

### 代码规范

- **Python**: 遵循 PEP 8 规范
- **TypeScript**: 使用 ESLint 与 Prettier
- **Commit**: 遵循 Conventional Commits 规范

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🏫 团队介绍

**武汉大学计算机学院软件工程2023级一组**
- 项目负责人：XX
- 技术架构：XX
- 产品设计：XX

## 📞 联系我们

- 📧 Email: contact@wendao.edu.cn
- 🐛 Issues: [GitHub Issues](https://github.com/your-org/AgentEducator/issues)
- 📖 Wiki: [项目文档](https://github.com/your-org/AgentEducator/wiki)

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给我们一个Star！**

*让AI重新定义教育，让学习变得更智能*

</div>

