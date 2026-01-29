"""
为SQLite添加触发器以模拟MySQL的ON UPDATE CURRENT_TIMESTAMP功能
"""

from flask import Flask
from models.models import db
import os

def create_triggers():
    """创建SQLite触发器"""
    from app import create_app
    app = create_app()
    
    with app.app_context():
        # 检查触发器是否存在
        result = db.engine.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND name='update_chat_sessions_timestamp'").fetchone()
        
        if not result:
            # 为chat_sessions表创建更新时间戳的触发器
            db.engine.execute("""
            CREATE TRIGGER update_chat_sessions_timestamp
            AFTER UPDATE ON chat_sessions
            FOR EACH ROW
            BEGIN
                UPDATE chat_sessions 
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.id;
            END;
            """)
            print("Created trigger for chat_sessions")
        
        print("Triggers setup completed")

if __name__ == "__main__":
    create_triggers() 