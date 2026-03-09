from flask_sqlalchemy import SQLAlchemy
import uuid
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.types import TypeDecorator
from datetime import datetime
import json
from sqlalchemy import Enum, JSON

db = SQLAlchemy()

# 创建自定义UUID类型转换器
class UUIDType(TypeDecorator):
    impl = CHAR(36)
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif isinstance(value, uuid.UUID):
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return uuid.UUID(value)

    def is_mutable(self):
        return False

class Users(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # teacher, student
    user_number = db.Column(db.String(10), unique=True, nullable=True)  # 用户编号：学号/教职工号
    avatar = db.Column(db.String(255))  # 用户头像URL
    class_name = db.Column(db.String(50))  # 学生所属班级
    status = db.Column(db.String(20), default='active')  # 学生状态: active, inactive, graduated
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = db.Column(db.Boolean, default=False)
    
    # 添加关系，使查询更方便 - 修改为使用back_populates
    taught_courses = db.relationship('Course', backref='teacher', lazy='dynamic', 
                                     foreign_keys='Course.teacher_id')
    enrolled_courses = db.relationship('StudentCourseEnrollment', backref='student', 
                                      lazy='dynamic', foreign_keys='StudentCourseEnrollment.student_id')
    permissions = db.relationship('UserPermission', back_populates='user')  # 使用back_populates
    video_progress = db.relationship('UserVideoProgress', backref='user', lazy='dynamic')
    comments = db.relationship('VideoComment', backref='user', lazy='dynamic')

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    start_date = db.Column(db.BigInteger, nullable=False, comment='课程开始日期(时间戳)')
    end_date = db.Column(db.BigInteger, nullable=False, comment='课程结束日期(时间戳)')
    
    # 排课时间字段
    schedule_start_time = db.Column(db.DateTime, nullable=True, comment='排课开始时间')
    schedule_end_time = db.Column(db.DateTime, nullable=True, comment='排课结束时间')
    
    hours = db.Column(db.Integer, nullable=False)
    student_count = db.Column(db.Integer, default=0)
    status = db.Column(db.Integer, nullable=False, comment='课程状态: 0=upcoming, 1=active, 2=completed')  # 从字符串改为整数
    is_public = db.Column(db.Boolean, default=False, comment='是否为公开课')  # 新增字段：是否为公开课
    semester = db.Column(db.String(20), nullable=False)
    teacher_id = db.Column(UUIDType, db.ForeignKey('users.id'))  # 添加教师ID字段
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = db.Column(db.Boolean, default=False)
    
    # 添加关系，使查询更方便
    videos = db.relationship('Video', backref='course', lazy='dynamic')
    chapters = db.relationship('CourseChapter', backref='course', lazy='dynamic')
    enrollments = db.relationship('StudentCourseEnrollment', backref='course', lazy='dynamic')

class Video(db.Model):
    """视频资源"""
    __tablename__ = 'videos'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4, comment='视频ID')
    title = db.Column(db.String(255), nullable=False, comment='视频标题')
    description = db.Column(db.Text, nullable=True, comment='视频描述')
    cover_url = db.Column(db.String(255), nullable=True, comment='封面图URL')
    video_url = db.Column(db.String(255), nullable=False, comment='视频URL（本地路径）')
    duration = db.Column(db.Integer, nullable=False, default=0, comment='视频时长(秒)')
    course_id = db.Column(UUIDType, db.ForeignKey('courses.id'), nullable=False, comment='所属课程ID')
    chapter_id = db.Column(UUIDType, db.ForeignKey('course_chapters.id'), nullable=True, comment='所属章节ID')
    order_index = db.Column(db.Integer, default=0, comment='章节内排序')
    view_count = db.Column(db.Integer, default=0, comment='观看次数')
    comment_count = db.Column(db.Integer, default=0, comment='评论数量')
    upload_time = db.Column(db.DateTime, default=datetime.now, comment='上传时间')
    #update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    is_deleted = db.Column(db.Boolean, default=False, comment='是否删除')
    completed_count = db.Column(db.Integer, default=0, comment='完成观看的人数')
    
    # 关系
    comments = db.relationship('VideoComment', backref='video', lazy='dynamic')
    progress_records = db.relationship('UserVideoProgress', backref='video', lazy='dynamic')
    summary = db.relationship('VideoSummary', backref='video', uselist=False)
    processing_tasks = db.relationship('VideoProcessingTask', back_populates='video', lazy=True)
    chapter = db.relationship('CourseChapter', backref='videos')
    
    @property
    def completion_rate(self):
        """计算视频完成率"""
        if self.view_count == 0:
            return 0
        return self.completed_count / self.view_count if self.view_count > 0 else 0
    
    @property
    def effective_play_url(self):
        """获取有效的播放地址"""
        # 返回原始的video_url
        return self.video_url
    
    def get_local_path(self):
        """获取本地文件路径"""
        import os
        return os.path.join(os.getcwd(), self.video_url.lstrip('/'))
    
    def is_local_file_exists(self):
        """检查本地文件是否存在"""
        import os
        return os.path.exists(self.get_local_path())

class VideoComment(db.Model):
    __tablename__ = 'video_comments'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    content = db.Column(db.Text, nullable=False)
    video_id = db.Column(UUIDType, db.ForeignKey('videos.id'), nullable=False)
    user_id = db.Column(UUIDType, db.ForeignKey('users.id'), nullable=False)
    parent_id = db.Column(UUIDType, db.ForeignKey('video_comments.id'))  # 回复的评论ID
    time_point = db.Column(db.Integer)  # 视频时间点（秒）
    create_time = db.Column(db.DateTime, default=datetime.now)
    likes = db.Column(db.Integer, default=0)
    is_deleted = db.Column(db.Boolean, default=False)
    
    # 添加回复关系，方便获取评论的回复
    replies = db.relationship('VideoComment', 
                             backref=db.backref('parent', remote_side=[id]),
                             lazy='dynamic')
    
    # 添加点赞关系
    liked_by = db.relationship('CommentLike', backref='comment', lazy='dynamic')

class CommentLike(db.Model):
    """评论点赞记录"""
    __tablename__ = 'comment_likes'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    comment_id = db.Column(UUIDType, db.ForeignKey('video_comments.id'), nullable=False)
    user_id = db.Column(UUIDType, db.ForeignKey('users.id'), nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)
    
    __table_args__ = (
        db.UniqueConstraint('comment_id', 'user_id', name='unique_comment_like'),
    )

class UserVideoProgress(db.Model):
    __tablename__ = 'user_video_progress'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUIDType, db.ForeignKey('users.id'), nullable=False)
    video_id = db.Column(UUIDType, db.ForeignKey('videos.id'), nullable=False)
    progress = db.Column(db.Float, default=0)  # 0-1之间的浮点数
    last_position = db.Column(db.Integer, default=0)  # 上次观看位置（秒）
    completed = db.Column(db.Boolean, default=False)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'video_id', name='uq_user_video'),
    )

class Document(db.Model):
    """课程文档资料（支持章节管理）"""
    __tablename__ = 'documents'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4, comment='文档ID')
    title = db.Column(db.String(255), nullable=False, comment='文档标题')
    description = db.Column(db.Text, nullable=True, comment='文档描述')
    file_url = db.Column(db.String(255), nullable=False, comment='文件URL')
    file_type = db.Column(db.String(50), nullable=False, comment='文件类型')
    file_size = db.Column(db.BigInteger, default=0, comment='文件大小(字节)')
    course_id = db.Column(UUIDType, db.ForeignKey('courses.id'), nullable=False, comment='所属课程ID')
    chapter_id = db.Column(UUIDType, db.ForeignKey('course_chapters.id'), nullable=True, comment='所属章节ID')
    order_index = db.Column(db.Integer, default=0, comment='排序权重')
    download_count = db.Column(db.Integer, default=0, comment='下载次数')
    upload_time = db.Column(db.DateTime, default=datetime.now, comment='上传时间')
    is_deleted = db.Column(db.Boolean, default=False, comment='是否删除')
    
    # 新增字段：智能处理相关
    processing_status = db.Column(db.String(20), default='unprocessed', comment='处理状态: unprocessed/processing/completed/failed')
    markitdown_content = db.Column(db.Text, nullable=True, comment='Markitdown转换后的markdown内容')
    
    # 关系
    course = db.relationship('Course', backref='documents')
    chapter = db.relationship('CourseChapter', backref='documents')
    
    # 新增关系：智能处理相关
    processing_tasks = db.relationship('DocumentProcessingTask', back_populates='document', lazy='dynamic')
    segments = db.relationship('DocumentSegment', back_populates='document', lazy='dynamic')
    vector_indices = db.relationship('DocumentVectorIndex', back_populates='document', lazy='dynamic')
    summary = db.relationship('DocumentSummary', back_populates='document', uselist=False)
    document_keywords = db.relationship('DocumentKeyword', back_populates='document', lazy='dynamic')
    
    def get_local_path(self):
        """获取本地文件路径"""
        import os
        return os.path.join(os.getcwd(), self.file_url.lstrip('/'))
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'title': self.title,
            'description': self.description,
            'fileUrl': self.file_url,
            'fileType': self.file_type,
            'fileSize': self.file_size,
            'courseId': str(self.course_id),
            'chapterId': str(self.chapter_id) if self.chapter_id else None,
            'orderIndex': self.order_index,
            'downloadCount': self.download_count,
            'uploadTime': self.upload_time.isoformat() if self.upload_time else None,
            'processingStatus': self.processing_status
        }
    def get_local_path(self):
        """获取本地文件路径"""
        import os
        return os.path.join(os.getcwd(), self.file_url.lstrip('/'))

class KnowledgePointMastery(db.Model):
    """知识点掌握程度模型"""
    __tablename__ = 'knowledge_point_mastery'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUIDType, db.ForeignKey('users.id'), nullable=False)
    keyword_id = db.Column(UUIDType, db.ForeignKey('keywords.id'), nullable=False)
    mastery_level = db.Column(db.Float, default=0.0, comment='掌握程度 0-1')
    material_progress = db.Column(db.Float, default=0.0, comment='教学材料进度 0-1')
    exercise_score = db.Column(db.Float, default=0.0, comment='练习得分 0-1')
    sub_knowledge_contribution = db.Column(db.Float, default=0.0, comment='子知识点贡献 0-1')
    calculation_details = db.Column(db.JSON, comment='计算详情')
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    user = db.relationship('Users', backref=db.backref('knowledge_masteries', lazy='dynamic'))
    keyword = db.relationship('Keyword', backref=db.backref('user_masteries', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'keyword_id', name='uk_user_keyword'),
    )
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'keyword_id': str(self.keyword_id),
            'keyword_name': self.keyword.name if self.keyword else None,
            'mastery_level': self.mastery_level,
            'material_progress': self.material_progress,
            'material_score': self.material_progress,  # 前端兼容字段
            'exercise_score': self.exercise_score,
            'sub_knowledge_contribution': self.sub_knowledge_contribution,
            'child_contribution': self.sub_knowledge_contribution,  # 前端兼容字段
            'calculation_details': self.calculation_details,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class QuestionKeyword(db.Model):
    """题目-知识点关联模型"""
    __tablename__ = 'question_keywords'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    question_id = db.Column(UUIDType, db.ForeignKey('questions.id'), nullable=False)
    keyword_id = db.Column(UUIDType, db.ForeignKey('keywords.id'), nullable=False)
    weight = db.Column(db.Float, default=1.0, comment='权重')
    difficulty_level = db.Column(db.Integer, default=1, comment='难度等级 1-5')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    question = db.relationship('Question', backref=db.backref('question_keywords', lazy='dynamic'))
    keyword = db.relationship('Keyword', backref=db.backref('question_keywords', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('question_id', 'keyword_id', name='uk_question_keyword'),
    )
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': str(self.id),
            'question_id': str(self.question_id),
            'keyword_id': str(self.keyword_id),
            'keyword_name': self.keyword.name if self.keyword else None,
            'keyword_category': self.keyword.category if self.keyword else None,
            'weight': self.weight,
            'difficulty_level': self.difficulty_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DocumentProgress(db.Model):
    """文档学习进度模型"""
    __tablename__ = 'document_progress'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUIDType, db.ForeignKey('users.id'), nullable=False)
    document_id = db.Column(UUIDType, db.ForeignKey('documents.id'), nullable=False)
    progress = db.Column(db.Float, default=0.0, comment='阅读进度 0-1')
    last_position = db.Column(db.Integer, default=0, comment='最后阅读位置')
    completed = db.Column(db.Boolean, default=False, comment='是否完成')
    reading_time = db.Column(db.Integer, default=0, comment='阅读时长(秒)')
    last_read_time = db.Column(db.DateTime, comment='最后阅读时间')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    user = db.relationship('Users', backref=db.backref('document_progress', lazy='dynamic'))
    document = db.relationship('Document', backref=db.backref('user_progress', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'document_id', name='uk_user_document'),
    )
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'document_id': str(self.document_id),
            'document_title': self.document.title if self.document else None,
            'progress': self.progress,
            'last_position': self.last_position,
            'completed': self.completed,
            'reading_time': self.reading_time,
            'last_read_time': self.last_read_time.isoformat() if self.last_read_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
class CourseChapter(db.Model):
    """课程章节模型"""
    __tablename__ = 'course_chapters'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4, comment='章节ID')
    course_id = db.Column(UUIDType, db.ForeignKey('courses.id'), nullable=False, comment='所属课程ID')
    title = db.Column(db.String(255), nullable=False, comment='章节标题')
    description = db.Column(db.Text, nullable=True, comment='章节描述')
    chapter_number = db.Column(db.Integer, nullable=False, comment='章节编号')
    order_index = db.Column(db.Integer, default=0, comment='排序权重')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    is_deleted = db.Column(db.Boolean, default=False, comment='是否删除')
    
    __table_args__ = (
        db.Index('idx_course_chapters_course_id', 'course_id'),
        db.Index('idx_course_chapters_order', 'course_id', 'order_index')
    )
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'courseId': str(self.course_id),
            'title': self.title,
            'description': self.description,
            'chapterNumber': self.chapter_number,
            'orderIndex': self.order_index,
            'createTime': self.create_time.isoformat() if self.create_time else None,
            'updateTime': self.update_time.isoformat() if self.update_time else None
        }

class VideoSummary(db.Model):
    __tablename__ = 'video_summaries'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    video_id = db.Column(UUIDType, db.ForeignKey('videos.id'), nullable=False, unique=True)
    keywords = db.Column(db.String(255))  # 逗号分隔的知识点
    sections = db.Column(db.Text)  # JSON格式存储的章节摘要
    whole_summary = db.Column(db.Text)  # 整体摘要
    generate_time = db.Column(db.DateTime, default=datetime.now)
    
    def set_sections(self, sections_list):
        self.sections = json.dumps(sections_list)
        
    def get_sections(self):
        return json.loads(self.sections) if self.sections else []

class StudentCourseEnrollment(db.Model):
    __tablename__ = 'student_course_enrollments'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    student_id = db.Column(UUIDType, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(UUIDType, db.ForeignKey('courses.id'), nullable=False)
    enroll_time = db.Column(db.DateTime, default=datetime.now)
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', name='uq_student_course'),
    )

class UserPermission(db.Model):
    __tablename__ = 'user_permission'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUIDType, db.ForeignKey('users.id'), nullable=False)
    course_access = db.Column(db.Text, nullable=True)  # JSON格式的课程ID列表
    comment_enabled = db.Column(db.Boolean, default=True)
    download_enabled = db.Column(db.Boolean, default=False)
    update_time = db.Column(db.DateTime, default=datetime.now)
    
    # 关联用户 - 修改为使用back_populates
    user = db.relationship('Users', back_populates='permissions')
    
    def set_course_access(self, course_ids):
        """设置可访问课程ID列表"""
        self.course_access = json.dumps(course_ids)
    
    def get_course_access(self):
        """获取可访问课程ID列表"""
        if not self.course_access:
            return []
        try:
            return json.loads(self.course_access)
        except:
            return []

class VideoProcessingTask(db.Model):
    """视频处理任务模型"""
    __tablename__ = 'video_processing_tasks'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    video_id = db.Column(UUIDType, db.ForeignKey('videos.id'), nullable=False, comment='关联的视频ID')
    task_id = db.Column(db.String(50), nullable=False, comment='处理任务ID')
    status = db.Column(db.String(20), nullable=False, comment='处理状态：pending, processing, completed, failed')
    processing_type = db.Column(db.String(20), nullable=False, comment='处理类型：transcoding, thumbnail, subtitle, all')
    progress = db.Column(db.Float, default=0.0, comment='处理进度，0-100')
    error_message = db.Column(db.Text, nullable=True, comment='错误信息')
    start_time = db.Column(db.DateTime, default=datetime.now, nullable=False, comment='开始时间')
    end_time = db.Column(db.DateTime, nullable=True, comment='结束时间')
    
    # 修改关系定义，使用back_populates对应Video中的processing_tasks
    video = db.relationship('Video', back_populates='processing_tasks')

class VideoKeyframe(db.Model):
    """存储视频关键帧及其OCR/ASR信息"""
    __tablename__ = 'video_keyframes'
    
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(UUIDType, db.ForeignKey('videos.id'), nullable=False)
    frame_number = db.Column(db.Integer, nullable=False)
    time_point = db.Column(db.Float, nullable=False)  # 秒
    time_formatted = db.Column(db.String(20))
    file_name = db.Column(db.String(255))
    ocr_result = db.Column(db.Text)  # 存储OCR识别到的文本
    asr_texts = db.Column(db.Text)  # 存储ASR识别到的文本
    create_time = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    video = db.relationship('Video', backref=db.backref('keyframes', lazy='dynamic'))
    
    def set_ocr_result(self, ocr_list):
        self.ocr_result = json.dumps(ocr_list, ensure_ascii=False)
        
    def get_ocr_result(self):
        return json.loads(self.ocr_result) if self.ocr_result else []

class VideoVectorIndex(db.Model):
    """存储视频向量索引的信息"""
    __tablename__ = 'video_vector_indices'
    
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(UUIDType, db.ForeignKey('videos.id'), nullable=False)
    index_path = db.Column(db.String(255), nullable=False)  # 存储索引文件路径
    embedding_model = db.Column(db.String(100))  # 使用的嵌入模型
    total_vectors = db.Column(db.Integer, default=0)
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    video = db.relationship('Video', backref=db.backref('vector_indices', lazy='dynamic'))

class TaskLog(db.Model):
    __tablename__ = 'task_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(50), index=True)
    video_id = db.Column(UUIDType, db.ForeignKey('videos.id'), index=True)  # 添加外键关联到videos表
    document_id = db.Column(UUIDType, db.ForeignKey('documents.id'), index=True)  # 新增：文档ID字段
    log_level = db.Column(db.String(20))
    message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    
    # 可选：添加关系，方便通过log获取video/document对象
    video = db.relationship('Video', backref=db.backref('task_logs', lazy='dynamic'))
    document = db.relationship('Document', backref=db.backref('task_logs', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'video_id': str(self.video_id) if self.video_id else None,
            'document_id': str(self.document_id) if self.document_id else None,
            'log_level': self.log_level,
            'message': self.message,
            'timestamp': self.timestamp.isoformat()
        }

# 聊天会话模型
class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUIDType, db.ForeignKey('users.id'), nullable=False)
    video_id = db.Column(UUIDType, db.ForeignKey('videos.id'), nullable=True)
    course_id = db.Column(UUIDType, db.ForeignKey('courses.id'), nullable=True)
    document_id = db.Column(UUIDType, db.ForeignKey('documents.id'), nullable=True)  # 新增：文档ID字段
    
    # 多个资源ID字段（JSON格式存储）
    video_ids = db.Column(db.Text, nullable=True)  # 存储多个视频ID
    course_ids = db.Column(db.Text, nullable=True)  # 存储多个课程ID
    document_ids = db.Column(db.Text, nullable=True)  # 存储多个文档ID
    
    title = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = db.Column(db.Boolean, default=False)
    
    # 关联关系
    user = db.relationship('Users', backref='chat_sessions')
    video = db.relationship('Video', backref='chat_sessions')
    course = db.relationship('Course', backref='chat_sessions')
    document = db.relationship('Document', backref='chat_sessions')  # 新增：文档关系
    messages = db.relationship('ChatMessage', backref='session', cascade='all, delete-orphan')
    
    def set_video_ids(self, video_ids):
        """设置多个视频ID"""
        if video_ids is None or len(video_ids) == 0:
            self.video_ids = None
        else:
            self.video_ids = json.dumps([str(vid) for vid in video_ids if vid])
    
    def get_video_ids(self):
        """获取多个视频ID"""
        if not self.video_ids:
            return []
        try:
            return json.loads(self.video_ids)
        except:
            return []
    
    def set_course_ids(self, course_ids):
        """设置多个课程ID"""
        if course_ids is None or len(course_ids) == 0:
            self.course_ids = None
        else:
            self.course_ids = json.dumps([str(cid) for cid in course_ids if cid])
    
    def get_course_ids(self):
        """获取多个课程ID"""
        if not self.course_ids:
            return []
        try:
            return json.loads(self.course_ids)
        except:
            return []
    
    def set_document_ids(self, document_ids):
        """设置多个文档ID"""
        if document_ids is None or len(document_ids) == 0:
            self.document_ids = None
        else:
            self.document_ids = json.dumps([str(did) for did in document_ids if did])
    
    def get_document_ids(self):
        """获取多个文档ID"""
        if not self.document_ids:
            return []
        try:
            return json.loads(self.document_ids)
        except:
            return []
    
    def add_resource_ids_from_sources(self, sources):
        """从引用源中添加资源ID"""
        if not sources:
            return
        
        # 获取当前的ID列表
        current_video_ids = set(self.get_video_ids())
        current_course_ids = set(self.get_course_ids())
        current_document_ids = set(self.get_document_ids())
        
        # 从sources中提取新的ID
        for source in sources:
            if hasattr(source, 'video_id') and source.video_id:
                current_video_ids.add(str(source.video_id))
            elif isinstance(source, dict) and source.get('video_id'):
                current_video_ids.add(str(source['video_id']))
                
            if hasattr(source, 'course_id') and source.course_id:
                current_course_ids.add(str(source.course_id))
            elif isinstance(source, dict) and source.get('course_id'):
                current_course_ids.add(str(source['course_id']))
                
            if hasattr(source, 'document_id') and source.document_id:
                current_document_ids.add(str(source.document_id))
            elif isinstance(source, dict) and source.get('document_id'):
                current_document_ids.add(str(source['document_id']))
        
        # 更新ID列表
        self.set_video_ids(list(current_video_ids))
        self.set_course_ids(list(current_course_ids))
        self.set_document_ids(list(current_document_ids))
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'video_id': str(self.video_id) if self.video_id else None,
            'course_id': str(self.course_id) if self.course_id else None,
            'document_id': str(self.document_id) if self.document_id else None,
            'video_ids': self.get_video_ids(),
            'course_ids': self.get_course_ids(),
            'document_ids': self.get_document_ids(),
            'title': self.title,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'message_count': len(self.messages) if self.messages else 0
        }

# 聊天消息模型
class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    session_id = db.Column(UUIDType, db.ForeignKey('chat_sessions.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # user 或 assistant
    content = db.Column(db.Text, nullable=False)
    time_references = db.Column(db.Text, nullable=True)  # 存储引用的视频时间点，JSON字符串
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def set_time_references(self, references):
        """设置时间引用点"""
        if references is None:
            self.time_references = None
        else:
            self.time_references = json.dumps(references)
    
    def get_time_references(self):
        """获取时间引用点"""
        if not self.time_references:
            return None
        try:
            return json.loads(self.time_references)
        except:
            return None
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'session_id': str(self.session_id),
            'role': self.role,
            'content': self.content,
            'time_references': self.get_time_references(),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

# 知识图谱相关模型

class Keyword(db.Model):
    """知识点模型 - 存储所有知识点"""
    __tablename__ = 'keywords'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False, unique=True, comment='知识点名称')
    category = db.Column(db.String(50), nullable=False, comment='知识点分类：core_concept, main_module, specific_point')
    description = db.Column(db.Text, nullable=True, comment='知识点描述')
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    video_keywords = db.relationship('VideoKeyword', back_populates='keyword', lazy='dynamic')
    course_keywords = db.relationship('CourseKeyword', back_populates='keyword', lazy='dynamic')
    document_keywords = db.relationship('DocumentKeyword', back_populates='keyword', lazy='dynamic')
    keyword_relations_source = db.relationship('KeywordRelation', 
                                             foreign_keys='KeywordRelation.source_keyword_id',
                                             back_populates='source_keyword', lazy='dynamic')
    keyword_relations_target = db.relationship('KeywordRelation',
                                             foreign_keys='KeywordRelation.target_keyword_id', 
                                             back_populates='target_keyword', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S')
        }

class VideoKeyword(db.Model):
    """视频知识点关系表"""
    __tablename__ = 'video_keywords'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    video_id = db.Column(UUIDType, db.ForeignKey('videos.id'), nullable=False)
    keyword_id = db.Column(UUIDType, db.ForeignKey('keywords.id'), nullable=False)
    weight = db.Column(db.Float, default=1.0, comment='知识点在视频中的重要程度')
    create_time = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    video = db.relationship('Video', backref='video_keywords')
    keyword = db.relationship('Keyword', back_populates='video_keywords')
    
    __table_args__ = (
        db.UniqueConstraint('video_id', 'keyword_id', name='uq_video_keyword'),
    )

class CourseKeyword(db.Model):
    """课程知识点关系表"""
    __tablename__ = 'course_keywords'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    course_id = db.Column(UUIDType, db.ForeignKey('courses.id'), nullable=False)
    keyword_id = db.Column(UUIDType, db.ForeignKey('keywords.id'), nullable=False)
    video_count = db.Column(db.Integer, default=0, comment='包含该知识点的视频数量')
    avg_weight = db.Column(db.Float, default=0.0, comment='该知识点在课程中的平均权重')
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    course = db.relationship('Course', backref='course_keywords')
    keyword = db.relationship('Keyword', back_populates='course_keywords')
    
    __table_args__ = (
        db.UniqueConstraint('course_id', 'keyword_id', name='uq_course_keyword'),
    )

class KeywordRelation(db.Model):
    """知识点关系表 - 存储知识点之间的关系"""
    __tablename__ = 'keyword_relations'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    source_keyword_id = db.Column(UUIDType, db.ForeignKey('keywords.id'), nullable=False)
    target_keyword_id = db.Column(UUIDType, db.ForeignKey('keywords.id'), nullable=False)
    relation_type = db.Column(db.String(50), nullable=False, comment='关系类型：prerequisite, related, contains等')
    strength = db.Column(db.Float, default=1.0, comment='关系强度 0-1')
    description = db.Column(db.Text, nullable=True, comment='关系描述')
    create_time = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    source_keyword = db.relationship('Keyword', 
                                   foreign_keys=[source_keyword_id],
                                   back_populates='keyword_relations_source')
    target_keyword = db.relationship('Keyword',
                                   foreign_keys=[target_keyword_id], 
                                   back_populates='keyword_relations_target')
    
    __table_args__ = (
        db.UniqueConstraint('source_keyword_id', 'target_keyword_id', 'relation_type', 
                          name='uq_keyword_relation'),
    )
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'source_keyword_id': str(self.source_keyword_id),
            'target_keyword_id': str(self.target_keyword_id),
            'relation_type': self.relation_type,
            'strength': self.strength,
            'description': self.description
        }

class KnowledgeGraphProcessingTask(db.Model):
    """知识图谱处理任务表"""
    __tablename__ = 'knowledge_graph_tasks'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    course_id = db.Column(UUIDType, db.ForeignKey('courses.id'), nullable=False)
    task_type = db.Column(db.String(50), nullable=False, comment='任务类型：keyword_extraction, categorization, relation_building')
    status = db.Column(db.String(20), nullable=False, default='pending', comment='任务状态：pending, processing, completed, failed')
    progress = db.Column(db.Float, default=0.0, comment='处理进度 0-1')
    result_data = db.Column(db.Text, nullable=True, comment='处理结果JSON数据')
    error_message = db.Column(db.Text, nullable=True, comment='错误信息')
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    create_time = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    course = db.relationship('Course', backref='knowledge_graph_tasks')
    
    def set_result_data(self, data):
        """设置结果数据"""
        self.result_data = json.dumps(data, ensure_ascii=False)
    
    def get_result_data(self):
        """获取结果数据"""
        if not self.result_data:
            return {}
        try:
            return json.loads(self.result_data)
        except:
            return {}
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'course_id': str(self.course_id),
            'task_type': self.task_type,
            'status': self.status,
            'progress': self.progress,
            'result_data': self.get_result_data(),
            'error_message': self.error_message,
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else None,
            'end_time': self.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.end_time else None,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S')
        }

# 文档智能处理相关模型

class DocumentProcessingTask(db.Model):
    """文档处理任务模型"""
    __tablename__ = 'document_processing_tasks'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    document_id = db.Column(UUIDType, db.ForeignKey('documents.id'), nullable=False, comment='关联的文档ID')
    task_id = db.Column(db.String(50), nullable=False, comment='处理任务ID')
    status = db.Column(db.String(20), nullable=False, comment='处理状态：pending, running, completed, failed')
    processing_type = db.Column(db.String(20), nullable=False, comment='处理类型：markitdown, segmentation, vectorization, summary')
    progress = db.Column(db.Float, default=0.0, comment='处理进度，0-1')
    error_message = db.Column(db.Text, nullable=True, comment='错误信息')
    start_time = db.Column(db.DateTime, default=datetime.now, nullable=False, comment='开始时间')
    end_time = db.Column(db.DateTime, nullable=True, comment='结束时间')
    
    # 关系
    document = db.relationship('Document', back_populates='processing_tasks')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'document_id': str(self.document_id),
            'task_id': self.task_id,
            'status': self.status,
            'processing_type': self.processing_type,
            'progress': self.progress,
            'error_message': self.error_message,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None
        }

class DocumentSegment(db.Model):
    """文档段落模型"""
    __tablename__ = 'document_segments'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(UUIDType, db.ForeignKey('documents.id'), nullable=False)
    segment_number = db.Column(db.Integer, nullable=False, comment='段落序号')
    title = db.Column(db.String(255), nullable=True, comment='段落标题')
    content = db.Column(db.Text, nullable=False, comment='Markitdown转换后的内容')
    page_number = db.Column(db.Integer, nullable=True, comment='页码（如果适用）')
    segment_type = db.Column(db.String(50), nullable=True, comment='段落类型: paragraph/table/list/heading等')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    
    # 关系
    document = db.relationship('Document', back_populates='segments')
    
    def to_dict(self):
        return {
            'id': self.id,
            'document_id': str(self.document_id),
            'segment_number': self.segment_number,
            'title': self.title,
            'content': self.content,
            'page_number': self.page_number,
            'segment_type': self.segment_type,
            'create_time': self.create_time.isoformat() if self.create_time else None
        }

class DocumentVectorIndex(db.Model):
    """文档向量索引模型"""
    __tablename__ = 'document_vector_indices'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(UUIDType, db.ForeignKey('documents.id'), nullable=False)
    index_path = db.Column(db.String(255), nullable=False, comment='向量索引文件路径')
    embedding_model = db.Column(db.String(100), nullable=True, comment='嵌入模型名称')
    total_vectors = db.Column(db.Integer, default=0, comment='向量总数')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系
    document = db.relationship('Document', back_populates='vector_indices')
    
    def to_dict(self):
        return {
            'id': self.id,
            'document_id': str(self.document_id),
            'index_path': self.index_path,
            'embedding_model': self.embedding_model,
            'total_vectors': self.total_vectors,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None
        }

class DocumentSummary(db.Model):
    """文档摘要模型"""
    __tablename__ = 'document_summaries'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    document_id = db.Column(UUIDType, db.ForeignKey('documents.id'), nullable=False, unique=True)
    main_points = db.Column(db.Text, nullable=True, comment='主要要点')
    keywords = db.Column(db.String(255), nullable=True, comment='知识点列表')
    sections = db.Column(db.Text, nullable=True, comment='章节摘要')
    whole_summary = db.Column(db.Text, nullable=True, comment='整体摘要')
    generate_time = db.Column(db.DateTime, default=datetime.now, comment='生成时间')
    
    # 关系
    document = db.relationship('Document', back_populates='summary')
    
    def set_sections(self, sections_list):
        """设置章节摘要"""
        self.sections = json.dumps(sections_list, ensure_ascii=False)
    
    def get_sections(self):
        """获取章节摘要"""
        return json.loads(self.sections) if self.sections else []
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'document_id': str(self.document_id),
            'main_points': self.main_points,
            'keywords': self.keywords,
            'sections': self.get_sections(),
            'whole_summary': self.whole_summary,
            'generate_time': self.generate_time.isoformat() if self.generate_time else None
        }

class DocumentKeyword(db.Model):
    """文档知识点关系表"""
    __tablename__ = 'document_keywords'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    document_id = db.Column(UUIDType, db.ForeignKey('documents.id'), nullable=False)
    keyword_id = db.Column(UUIDType, db.ForeignKey('keywords.id'), nullable=False)
    weight = db.Column(db.Float, default=1.0, comment='知识点在文档中的重要程度')
    create_time = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    document = db.relationship('Document', back_populates='document_keywords')
    keyword = db.relationship('Keyword', back_populates='document_keywords')
    
    __table_args__ = (
        db.UniqueConstraint('document_id', 'keyword_id', name='uq_document_keyword'),
    )
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'document_id': str(self.document_id),
            'keyword_id': str(self.keyword_id),
            'keyword_name': self.keyword.name if self.keyword else None,
            'weight': self.weight,
            'create_time': self.create_time.isoformat() if self.create_time else None
        }

class Question(db.Model):
    """题目模型"""
    __tablename__ = 'questions'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    assignment_id = db.Column(UUIDType, db.ForeignKey('assignments.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False, comment='题目类型: single, multiple, blank, essay')
    content = db.Column(db.Text, nullable=False, comment='题目内容')
    options = db.Column(db.Text, nullable=True, comment='选项JSON格式，用于单选和多选题')
    answers = db.Column(db.Text, nullable=True, comment='答案，填空题使用')
    reference = db.Column(db.Text, nullable=True, comment='参考答案，问答题使用')
    explanation = db.Column(db.Text, nullable=True, comment='答案解析')
    order_num = db.Column(db.Integer, default=0, comment='题目顺序')
    max_score = db.Column(db.Float, default=5.0, comment='题目满分分数')
    keywords = db.Column(db.Text, nullable=True, comment='相关知识点列表，JSON格式')
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 新增字段：从QuestionBank迁移过来的字段
    course_id = db.Column(UUIDType, db.ForeignKey('courses.id'), nullable=False, comment='所属课程ID')
    difficulty = db.Column(db.String(16), nullable=True, comment='难度')
    tags = db.Column(db.JSON, nullable=True, comment='标签')
    remark = db.Column(db.Text, nullable=True, comment='备注')
    creator_id = db.Column(db.String(36), nullable=True, comment='创建者ID')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    
    # 关系
    assignment = db.relationship('Assignment', back_populates='questions')
    course = db.relationship('Course', backref='questions')
    
    def set_options(self, options_list):
        """设置选项"""
        if isinstance(options_list, str):
            self.options = options_list
        else:
            self.options = json.dumps(options_list)

    def get_options(self):
        """获取选项"""
        if not self.options:
            return []
        try:
            return json.loads(self.options)
        except:
            return []
            
    def set_keywords(self, keywords_list):
        """设置知识点列表"""
        if isinstance(keywords_list, str):
            self.keywords = keywords_list
        else:
            self.keywords = json.dumps(keywords_list)
    
    def get_keywords(self):
        """获取知识点列表"""
        if not self.keywords:
            return []
        try:
            return json.loads(self.keywords)
        except:
            return []
    
    def to_dict(self):
        course_name = self.course.name if self.course else None
        return {
            'id': str(self.id),
            'type': self.type,
            'question_type': self.type,  # 兼容前端
            'content': self.content,
            'options': self.get_options(),
            'answers': self.answers,
            'correct_answer': self.answers,  # 添加前端期望的字段名
            'answer': self.answers,  # 添加另一个兼容字段名
            'reference': self.reference,
            'explanation': self.explanation,
            'orderIndex': self.order_num,
            'maxScore': self.max_score,
            'keywords': self.get_keywords(),
            'category': str(self.course_id),  # 课程ID
            'course_id': str(self.course_id),
            'course_name': course_name,
            'difficulty': self.difficulty or 'medium',
            'tags': [qk.keyword.name for qk in self.question_keywords if qk.keyword],
            'remark': self.remark,
            'creator_id': self.creator_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Assignment(db.Model):
    """作业模型"""
    __tablename__ = 'assignments'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(255), nullable=False, comment='作业标题')
    course_id = db.Column(UUIDType, db.ForeignKey('courses.id'), nullable=False)
    teacher_id = db.Column(UUIDType, db.ForeignKey('users.id'), nullable=False)
    due_date = db.Column(db.DateTime, nullable=False, comment='截止日期')
    publish_time = db.Column(db.DateTime, nullable=True, comment='发布时间')
    status = db.Column(db.String(20), nullable=False, default='draft', comment='作业状态: draft, published')
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = db.Column(db.Boolean, default=False)
    
    # 关系
    course = db.relationship('Course', backref='assignments')
    teacher = db.relationship('Users', backref='created_assignments')
    questions = db.relationship('Question', back_populates='assignment', 
                              order_by='Question.order_num', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'title': self.title,
            'courseId': str(self.course_id),
            'courseName': self.course.name if self.course else None,
            'teacherId': str(self.teacher_id),
            'teacherName': self.teacher.username if self.teacher else None,
            'dueDate': self.due_date.isoformat() if self.due_date else None,
            'publishTime': self.publish_time.isoformat() if self.publish_time else None,
            'status': self.status,
            'questions': [question.to_dict() for question in self.questions]
        }

class StudentAnswer(db.Model):
    """学生答题记录模型"""
    __tablename__ = 'student_answers'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    student_id = db.Column(UUIDType, db.ForeignKey('users.id'), nullable=False)
    assignment_id = db.Column(UUIDType, db.ForeignKey('assignments.id'), nullable=False)
    question_id = db.Column(UUIDType, db.ForeignKey('questions.id'), nullable=False)
    answer = db.Column(db.JSON, comment='学生答案（JSON格式）')
    is_correct = db.Column(db.Boolean, default=None, comment='是否答对')
    score = db.Column(db.Float, default=None, comment='得分')
    comment = db.Column(db.Text, nullable=True, comment='批改评语')
    submit_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
      # 关系
    student = db.relationship('Users', backref=db.backref('answers', lazy='dynamic'))
    assignment = db.relationship('Assignment', backref=db.backref('student_answers', lazy='dynamic'))
    question = db.relationship('Question', backref=db.backref('student_answers', lazy='dynamic'))
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'assignment_id', 'question_id', 
                           name='uk_student_question'),
    )
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': str(self.id),
            'student_id': str(self.student_id),
            'assignment_id': str(self.assignment_id),
            'question_id': str(self.question_id),
            'answer': self.answer,
            'is_correct': self.is_correct,
            'score': self.score,
            'comment': self.comment,
            'submit_time': self.submit_time.isoformat() if self.submit_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None
        }

class DailyStats(db.Model):
    """日统计数据模型"""
    __tablename__ = 'daily_stats'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.Date, nullable=False, comment='统计日期')
    course_id = db.Column(UUIDType, db.ForeignKey('courses.id'), nullable=True, comment='课程ID，为空表示全局统计')
    total_students = db.Column(db.Integer, nullable=True, comment='总学生数')
    active_students = db.Column(db.Integer, nullable=True, comment='活跃学生数')
    video_views = db.Column(db.Integer, nullable=True, comment='视频观看次数')
    avg_completion_rate = db.Column(db.Float, nullable=True, comment='平均完成率')
    new_enrollments = db.Column(db.Integer, nullable=True, comment='新增注册数')
    total_comments = db.Column(db.Integer, nullable=True, comment='总评论数')
    
    # 关系
    course = db.relationship('Course', backref='daily_stats')
    
    __table_args__ = (
        db.UniqueConstraint('date', 'course_id', name='_date_course_uc'),
        db.Index('ix_daily_stats_date', 'date'),
        db.Index('ix_daily_stats_course_id', 'course_id'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat() if self.date else None,
            'course_id': str(self.course_id) if self.course_id else None,
            'total_students': self.total_students,
            'active_students': self.active_students,
            'video_views': self.video_views,
            'avg_completion_rate': self.avg_completion_rate,
            'new_enrollments': self.new_enrollments,
            'total_comments': self.total_comments
        }
