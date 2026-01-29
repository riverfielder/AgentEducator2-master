"""
移除OSS相关字段的数据库迁移脚本
执行此脚本从Video表移除OSS相关字段
"""

from models.models import db
from flask import current_app
import logging

logger = logging.getLogger(__name__)

def remove_oss_fields():
    """移除OSS相关字段"""
    try:
        # 检查数据库引擎类型
        engine = db.engine
        
        # 从Video表移除OSS相关字段
        with engine.connect() as conn:
            # 检查字段是否存在
            result = conn.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'videos' AND COLUMN_NAME IN ('play_path', 'oss_key', 'oss_uploaded', 'update_time')
            """)
            existing_columns = [row[0] for row in result.fetchall()]
            
            # 删除存在的OSS相关字段
            if 'play_path' in existing_columns:
                conn.execute("ALTER TABLE videos DROP COLUMN play_path")
                logger.info("删除 play_path 字段成功")
            
            if 'oss_key' in existing_columns:
                conn.execute("ALTER TABLE videos DROP COLUMN oss_key")
                logger.info("删除 oss_key 字段成功")
            
            if 'oss_uploaded' in existing_columns:
                conn.execute("ALTER TABLE videos DROP COLUMN oss_uploaded")
                logger.info("删除 oss_uploaded 字段成功")
                
            if 'update_time' in existing_columns:
                conn.execute("ALTER TABLE videos DROP COLUMN update_time")
                logger.info("删除 update_time 字段成功")
            
            # 提交事务
            conn.commit()
            
        logger.info("OSS字段移除完成")
        return True
        
    except Exception as e:
        logger.error(f"OSS字段移除失败: {str(e)}")
        return False

if __name__ == "__main__":
    # 创建Flask应用上下文
    from app import app
    
    with app.app_context():
        print("开始执行OSS字段移除...")
        success = remove_oss_fields()
        
        if success:
            print("✅ OSS字段移除成功完成")
        else:
            print("❌ OSS字段移除失败")
