"""
聊天历史记录表的迁移脚本
用于添加chat_sessions和chat_messages表，SQLite版本
"""

from flask import Flask
from models.models import db
import os

def run_migration():
    """运行迁移脚本，添加聊天历史相关表"""
    from app import create_app
    app = create_app()
    
    with app.app_context():
        # 检查表是否已存在
        chat_sessions_exists = db.engine.dialect.has_table(db.engine, 'chat_sessions')
        chat_messages_exists = db.engine.dialect.has_table(db.engine, 'chat_messages')
        
        if not chat_sessions_exists:
            # 创建聊天会话表 - SQLite版本
            db.engine.execute("""
            CREATE TABLE chat_sessions (
              id CHAR(36) NOT NULL,
              user_id CHAR(36) NOT NULL,
              video_id CHAR(36),
              course_id CHAR(36),
              title VARCHAR(255) NOT NULL,
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              is_deleted BOOLEAN NOT NULL DEFAULT 0,
              PRIMARY KEY (id),
              FOREIGN KEY (user_id) REFERENCES users (id),
              FOREIGN KEY (video_id) REFERENCES videos (id),
              FOREIGN KEY (course_id) REFERENCES courses (id)
            );
            """)
            
            # 创建索引
            db.engine.execute("CREATE INDEX idx_user ON chat_sessions (user_id);")
            db.engine.execute("CREATE INDEX idx_video ON chat_sessions (video_id);")
            db.engine.execute("CREATE INDEX idx_course ON chat_sessions (course_id);")
            
            print("Created chat_sessions table")
        
        if not chat_messages_exists:
            # 创建聊天消息表 - SQLite版本
            db.engine.execute("""
            CREATE TABLE chat_messages (
              id CHAR(36) NOT NULL,
              session_id CHAR(36) NOT NULL,
              role VARCHAR(20) NOT NULL,
              content TEXT NOT NULL,
              time_references TEXT,
              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (id),
              FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
            );
            """)
            
            # 创建索引
            db.engine.execute("CREATE INDEX idx_session ON chat_messages (session_id);")
            
            print("Created chat_messages table")
        
        print("Migration completed")

if __name__ == "__main__":
    run_migration() 