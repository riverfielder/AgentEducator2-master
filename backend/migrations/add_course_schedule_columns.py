"""
添加课程排课时间字段的迁移脚本
"""
import sys
import os

# 将当前脚本所在的父目录添加到Python路径中，以便能够导入app和models
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from models.models import db
import traceback

def run_migration():
    """运行迁移脚本，添加schedule_start_time和schedule_end_time列"""
    try:
        from app import create_app
        app = create_app()
    except Exception as e:
        # Fallback if cannot import app easily (e.g. env issues)
        print(f"Cannot import app, assuming manual run or different env setup. Error: {e}")
        traceback.print_exc()
        return
    
    with app.app_context():
        try:
            # Check if columns exist (simple check using SQLAlchemy functionality)
            # Note: execute returns ResultProxy in older SQLAlchemy or Result in newer.
            # fetchall() works for both usually.
            
            # Adapting to underlying DB type. Assuming SQLite based on context.
            # If MySQL, syntax is similar.
            
            # Using text() for safety across different SQLAlchemy versions
            from sqlalchemy import text
            
            # Check columns
            try:
                # Try SQLite PRAGMA
                res = db.session.execute(text("PRAGMA table_info(courses)")).fetchall()
                if res:
                    columns = [col[1] for col in res]
                else:
                    # Fallback for MySQL or others if PRAGMA doesn't work/return
                    # This part is tricky without knowing exact DB. Assuming SQLite as per chat history.
                    columns = [] 
            except Exception:
                # If PRAGMA fails, maybe it's MySQL. "SHOW COLUMNS FROM courses"
                try:
                    res = db.session.execute(text("SHOW COLUMNS FROM courses")).fetchall()
                    columns = [col[0] for col in res]
                except Exception:
                    columns = []
            
            if 'schedule_start_time' not in columns:
                try:
                    db.session.execute(text("ALTER TABLE courses ADD COLUMN schedule_start_time DATETIME"))
                    print("Added schedule_start_time column")
                except Exception as e:
                     print(f"Failed to add schedule_start_time: {e}")

            if 'schedule_end_time' not in columns:
                try:
                    db.session.execute(text("ALTER TABLE courses ADD COLUMN schedule_end_time DATETIME"))
                    print("Added schedule_end_time column")
                except Exception as e:
                     print(f"Failed to add schedule_end_time: {e}")

            # Commit if transaction management requires it (e.g. Postgres, but SQLite/MySQL DDL is often auto-commit or implicit)
            try:
                db.session.commit()
            except:
                pass
                
            print("Migration check/execution completed")
            
        except Exception as e:
            print(f"Migration failed: {e}")
            traceback.print_exc()

if __name__ == '__main__':
    run_migration()
