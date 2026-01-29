from models.models import db
from models.models import VideoKeyframe, VideoProcessingTask, VideoVectorIndex
import os

def create_advanced_tables():
    """创建视频处理相关的数据库表"""
    # 创建目录
    os.makedirs("temp_keyframes", exist_ok=True)
    os.makedirs("vector_indices", exist_ok=True)
    
    # 创建表
    db.create_all()
    
    print("高级数据库表创建完成")

if __name__ == "__main__":
    from app import app
    with app.app_context():
        create_advanced_tables()
