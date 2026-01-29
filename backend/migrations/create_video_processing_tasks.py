"""
创建视频处理任务表的迁移脚本
"""

from models.models import db
from models.models import VideoProcessingTask
from sqlalchemy import inspect
def create_table():
    """创建视频处理任务表"""
    # 检查表是否存在
    inspector = inspect(db.engine)
    table_exists = inspector.has_table(VideoProcessingTask.__tablename__)
    
    if not table_exists:
        # 创建表
        VideoProcessingTask.__table__.create(db.engine)
        print(f"成功创建表 {VideoProcessingTask.__tablename__}")
    else:
        print(f"表 {VideoProcessingTask.__tablename__} 已存在")

if __name__ == "__main__":
    create_table()
