# WenDao 平台数据库结构文档

## 概述

WenDao平台是一个完整的大模型智能学习平台，数据库设计围绕用户、课程、视频和AI功能展开。系统使用MySQL数据库，通过SQLAlchemy ORM框架进行数据操作。

## 基础数据表

### 1. Users（用户表）

存储所有用户信息，包括教师和学生。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | Integer | 主键 |
| username | String(50) | 用户名，唯一 |
| password | String(255) | 加密密码 |
| email | String(100) | 邮箱，唯一 |
| role | String(20) | 角色（teacher, student） |
| create_time | DateTime | 创建时间 |
| update_time | DateTime | 更新时间 |
| is_deleted | Boolean | 是否已删除 |

关系：
- 一个用户可以教授多个课程 (taught_courses)
- 一个用户可以注册多个课程 (enrolled_courses)
- 一个用户可以有一个权限记录 (permissions)
- 一个用户可以有多个视频进度记录 (video_progress)
- 一个用户可以发表多个评论 (comments)

### 2. Course（课程表）

存储课程信息。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | Integer | 主键 |
| name | String(100) | 课程名称 |
| code | String(20) | 课程代码，唯一 |
| description | Text | 课程描述 |
| image_url | String(255) | 课程图片URL |
| start_date | DateTime | 开始日期 |
| end_date | DateTime | 结束日期 |
| hours | Integer | 课时数 |
| student_count | Integer | 学生数量 |
| status | String(20) | 状态（active, inactive） |
| semester | String(20) | 学期 |
| teacher_id | Integer | 教师ID，外键 |
| create_time | DateTime | 创建时间 |
| update_time | DateTime | 更新时间 |
| is_deleted | Boolean | 是否已删除 |

关系：
- 一个课程属于一个教师 (teacher)
- 一个课程可以有多个视频 (videos)
- 一个课程可以有多个文档 (documents)
- 一个课程可以有多个选课记录 (enrollments)

### 3. Video（视频表）

存储课程视频资源。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | Integer | 主键 |
| title | String(100) | 视频标题 |
| description | Text | 视频描述 |
| cover_url | String(255) | 封面图URL |
| video_url | String(255) | 视频URL |
| duration | Integer | 视频时长（秒） |
| course_id | Integer | 课程ID，外键 |
| view_count | Integer | 观看次数 |
| comment_count | Integer | 评论数量 |
| upload_time | DateTime | 上传时间 |
| is_deleted | Boolean | 是否已删除 |
| completed_count | Integer | 完成观看的人数 |

关系：
- 一个视频属于一个课程 (course)
- 一个视频可以有多个评论 (comments)
- 一个视频可以有多个观看进度记录 (progress_records)
- 一个视频可以有一个摘要 (summary)
- 一个视频可以有多个关键帧 (keyframes)
- 一个视频可以有多个向量索引 (vector_indices)

### 4. VideoComment（视频评论表）

存储视频评论。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | Integer | 主键 |
| content | Text | 评论内容 |
| video_id | Integer | 视频ID，外键 |
| user_id | Integer | 用户ID，外键 |
| parent_id | Integer | 父评论ID，外键，回复用 |
| time_point | Integer | 视频时间点（秒） |
| create_time | DateTime | 创建时间 |
| likes | Integer | 点赞数 |
| is_deleted | Boolean | 是否已删除 |

关系：
- 一个评论属于一个视频 (video)
- 一个评论属于一个用户 (user)
- 一个评论可以有多个回复 (replies)

### 5. UserVideoProgress（用户视频进度表）

存储用户观看视频的进度。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | Integer | 主键 |
| user_id | Integer | 用户ID，外键 |
| video_id | Integer | 视频ID，外键 |
| progress | Float | 进度（0-1） |
| last_position | Integer | 上次观看位置（秒） |
| completed | Boolean | 是否完成 |
| update_time | DateTime | 更新时间 |

约束：
- 用户ID和视频ID组合唯一

### 6. Document（文档表）

存储课程相关的文档资料。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | Integer | 主键 |
| title | String(100) | 文档标题 |
| file_url | String(255) | 文件URL |
| file_type | String(20) | 文件类型 |
| file_size | Integer | 文件大小（字节） |
| course_id | Integer | 课程ID，外键 |
| upload_time | DateTime | 上传时间 |
| is_deleted | Boolean | 是否已删除 |

关系：
- 一个文档属于一个课程 (course)

### 7. VideoSummary（视频摘要表）

存储AI生成的视频摘要信息。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | Integer | 主键 |
| video_id | Integer | 视频ID，外键，唯一 |
| main_points | Text | 主要观点 |
| keywords | String(255) | 知识点（逗号分隔） |
| sections | Text | 章节摘要（JSON格式） |
| generate_time | DateTime | 生成时间 |

方法：
- set_sections(sections_list): 将章节列表转为JSON存储
- get_sections(): 获取解析后的章节列表

### 8. StudentCourseEnrollment（学生选课表）

存储学生选课记录。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | Integer | 主键 |
| student_id | Integer | 学生ID，外键 |
| course_id | Integer | 课程ID，外键 |
| enroll_time | DateTime | 选课时间 |

约束：
- 学生ID和课程ID组合唯一

### 9. UserPermission（用户权限表）

存储用户特殊权限设置。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | Integer | 主键 |
| user_id | Integer | 用户ID，外键，唯一 |
| course_access | Text | 可访问课程ID列表（JSON格式） |
| comment_enabled | Boolean | 是否允许评论 |
| download_enabled | Boolean | 是否允许下载 |
| update_time | DateTime | 更新时间 |

方法：
- set_course_access(course_ids): 设置可访问课程ID列表
- get_course_access(): 获取可访问课程ID列表

## AI功能相关数据表

### 1. VideoKeyframe（视频关键帧表）

存储视频关键帧及其OCR/ASR信息。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | Integer | 主键 |
| video_id | Integer | 视频ID，外键 |
| frame_number | Integer | 帧编号 |
| time_point | Float | 时间点（秒） |
| time_formatted | String(20) | 格式化时间 |
| file_name | String(255) | 文件名 |
| ocr_result | Text | OCR识别结果（JSON格式） |
| asr_texts | Text | ASR识别结果 |
| create_time | DateTime | 创建时间 |

方法：
- set_ocr_result(ocr_list): 设置OCR结果
- get_ocr_result(): 获取OCR结果

### 2. VideoProcessingTask（视频处理任务表）

跟踪视频处理任务的状态。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | Integer | 主键 |
| video_id | Integer | 视频ID，外键，唯一 |
| task_id | String(100) | 任务ID |
| status | String(20) | 状态（pending, processing, completed, failed） |
| processing_type | String(20) | 处理类型（keyframe, ocr, asr, vector_index） |
| progress | Float | 进度（0-1） |
| error_message | Text | 错误信息 |
| start_time | DateTime | 开始时间 |
| end_time | DateTime | 结束时间 |

### 3. VideoVectorIndex（视频向量索引表）

存储视频向量索引信息，用于AI检索。

| 字段名 | 类型 | 描述 |
|--------|------|------|
| id | Integer | 主键 |
| video_id | Integer | 视频ID，外键 |
| index_path | String(255) | 索引文件路径 |
| embedding_model | String(100) | 使用的嵌入模型 |
| total_vectors | Integer | 向量总数 |
| create_time | DateTime | 创建时间 |
| update_time | DateTime | 更新时间 |

## 数据关系图

主要关系：
- 用户(Users) 1:N 课程(Course)：一个教师可以教授多个课程
- 课程(Course) 1:N 视频(Video)：一个课程可以有多个视频
- 课程(Course) 1:N 文档(Document)：一个课程可以有多个文档
- 用户(Users) M:N 课程(Course)：通过StudentCourseEnrollment关联，学生可以选修多个课程
- 视频(Video) 1:1 摘要(VideoSummary)：一个视频有一个摘要
- 视频(Video) 1:N 关键帧(VideoKeyframe)：一个视频有多个关键帧
- 视频(Video) 1:N 评论(VideoComment)：一个视频有多个评论
- 用户(Users) 1:N 评论(VideoComment)：一个用户可以发表多个评论

## 数据库索引

主要索引：
- Users表：username, email索引
- Course表：code索引
- 外键关系上的索引，如course_id, user_id, video_id等
- is_deleted字段上的索引，用于软删除功能

这一设计充分考虑了数据的完整性、查询效率和扩展性，支持系统的核心功能包括用户管理、课程管理、内容管理和AI智能功能。 