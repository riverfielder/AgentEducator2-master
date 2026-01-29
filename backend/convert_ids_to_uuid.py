"""
将数据库表的自增ID转换为UUID的迁移脚本
"""

import uuid
from flask import Flask
from models.models import db, Video, Document, VideoProcessingTask
from sqlalchemy import text
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:mysql_jZQHwE@localhost:3307/wendao_platform'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def generate_uuid():
    """生成UUID"""
    return str(uuid.uuid4())

def convert_video_ids():
    """将视频表的ID转换为UUID"""
    with app.app_context():
        # 创建临时表
        db.session.execute(text("""
        CREATE TABLE videos_new (
            id CHAR(36) PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            cover_url VARCHAR(255),
            video_url VARCHAR(255) NOT NULL,
            duration INT NOT NULL DEFAULT 0,
            course_id INT NOT NULL,
            view_count INT DEFAULT 0,
            comment_count INT DEFAULT 0,
            upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_deleted BOOLEAN DEFAULT FALSE
        )
        """))
        
        # 获取所有视频
        videos = db.session.execute(text("SELECT * FROM videos WHERE is_deleted = 0")).fetchall()
        id_mapping = {}  # 存储旧ID到新UUID的映射
        
        # 插入数据到新表
        for video in videos:
            new_id = generate_uuid()
            id_mapping[video.id] = new_id
            
            db.session.execute(text("""
            INSERT INTO videos_new 
            VALUES (:id, :title, :description, :cover_url, :video_url, :duration, 
                   :course_id, :view_count, :comment_count, :upload_time, :is_deleted)
            """), {
                'id': new_id,
                'title': video.title,
                'description': video.description,
                'cover_url': video.cover_url,
                'video_url': video.video_url,
                'duration': video.duration,
                'course_id': video.course_id,
                'view_count': video.view_count,
                'comment_count': video.comment_count,
                'upload_time': video.upload_time,
                'is_deleted': video.is_deleted
            })
        
        # 重命名表
        db.session.execute(text("RENAME TABLE videos TO videos_old, videos_new TO videos"))
        db.session.commit()
        
        print("视频表ID转换完成")
        return id_mapping

def convert_document_ids():
    """将文档表的ID转换为UUID"""
    with app.app_context():
        # 创建临时表
        db.session.execute(text("""
        CREATE TABLE documents_new (
            id CHAR(36) PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            file_url VARCHAR(255) NOT NULL,
            file_type VARCHAR(50) NOT NULL,
            file_size INT DEFAULT 0,
            course_id INT NOT NULL,
            upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_deleted BOOLEAN DEFAULT FALSE
        )
        """))
        
        # 获取所有文档
        documents = db.session.execute(text("SELECT * FROM documents WHERE is_deleted = 0")).fetchall()
        
        # 插入数据到新表
        for document in documents:
            new_id = generate_uuid()
            
            db.session.execute(text("""
            INSERT INTO documents_new 
            VALUES (:id, :title, :file_url, :file_type, :file_size, :course_id, :upload_time, :is_deleted)
            """), {
                'id': new_id,
                'title': document.title,
                'file_url': document.file_url,
                'file_type': document.file_type,
                'file_size': document.file_size,
                'course_id': document.course_id,
                'upload_time': document.upload_time,
                'is_deleted': document.is_deleted
            })
        
        # 重命名表
        db.session.execute(text("RENAME TABLE documents TO documents_old, documents_new TO documents"))
        db.session.commit()
        
        print("文档表ID转换完成")

if __name__ == "__main__":
    video_id_mapping = convert_video_ids()
    convert_document_ids()
    
    print("所有表ID转换完成")
