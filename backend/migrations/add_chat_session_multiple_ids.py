#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加聊天会话多资源ID支持
为ChatSession表添加video_ids、course_ids、document_ids字段以支持多个资源引用
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.models import db, ChatSession
from sqlalchemy import text

def column_exists(table_name, column_name):
    """检查列是否存在（支持MySQL和SQLite）"""
    try:
        # 检测数据库类型
        db_url = db.engine.url
        if 'mysql' in str(db_url):
            # MySQL语法
            result = db.session.execute(text(f"""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = '{table_name}' 
                AND COLUMN_NAME = '{column_name}'
            """))
        else:
            # SQLite语法
            result = db.session.execute(text(f"""
                SELECT name FROM pragma_table_info('{table_name}') 
                WHERE name = '{column_name}'
            """))
        return result.fetchone() is not None
    except Exception as e:
        print(f"检查列 {column_name} 时出错: {e}")
        return False

def check_columns_exist():
    """检查新列是否已存在（支持MySQL和SQLite）"""
    try:
        # 检测数据库类型
        db_url = db.engine.url
        if 'mysql' in str(db_url):
            # MySQL语法
            result = db.session.execute(text("""
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'chat_sessions' 
                AND COLUMN_NAME IN ('video_ids', 'course_ids', 'document_ids')
            """))
        else:
            # SQLite语法
            result = db.session.execute(text("""
                SELECT name FROM pragma_table_info('chat_sessions') 
                WHERE name IN ('video_ids', 'course_ids', 'document_ids')
            """))
        existing_columns = [row[0] for row in result.fetchall()]
        return existing_columns
    except Exception as e:
        print(f"检查列存在性时出错: {e}")
        return []

def add_multiple_ids_columns():
    """为ChatSession表添加多个ID字段"""
    print("\n📝 添加多个ID字段...")
    try:
        # 检查字段是否已存在
        existing_columns = check_columns_exist()
        
        columns_to_add = []
        if 'video_ids' not in existing_columns:
            columns_to_add.append('video_ids')
        else:
            print("⚠️  video_ids 列已存在，跳过")
            
        if 'course_ids' not in existing_columns:
            columns_to_add.append('course_ids')
        else:
            print("⚠️  course_ids 列已存在，跳过")
            
        if 'document_ids' not in existing_columns:
            columns_to_add.append('document_ids')
        else:
            print("⚠️  document_ids 列已存在，跳过")
        
        # 逐个添加列，每次都提交事务
        for column_name in columns_to_add:
            with db.engine.connect() as conn:
                trans = conn.begin()
                try:
                    conn.execute(text(f"ALTER TABLE chat_sessions ADD COLUMN {column_name} TEXT"))
                    trans.commit()
                    print(f"✅ {column_name} 列添加成功")
                except Exception as e:
                    trans.rollback()
                    print(f"❌ 添加 {column_name} 列时出错: {e}")
                    raise
                
    except Exception as e:
        print(f"❌ 添加列时出错: {e}")
        raise

def migrate_existing_data():
    """迁移现有的单个ID到多个ID字段"""
    print("\n🔄 迁移现有数据...")
    try:
        # 重新创建session以避免表定义缓存问题
        db.session.close()
        
        # 查询所有有单个资源ID的会话
        sessions = ChatSession.query.filter(
            (ChatSession.video_id.isnot(None)) |
            (ChatSession.course_id.isnot(None)) |
            (ChatSession.document_id.isnot(None))
        ).all()
        
        migrated_count = 0
        for session in sessions:
            updated = False
            
            # 迁移video_id到video_ids
            if session.video_id and not session.get_video_ids():
                session.set_video_ids([session.video_id])
                updated = True
                
            # 迁移course_id到course_ids
            if session.course_id and not session.get_course_ids():
                session.set_course_ids([session.course_id])
                updated = True
                
            # 迁移document_id到document_ids
            if session.document_id and not session.get_document_ids():
                session.set_document_ids([session.document_id])
                updated = True
                
            if updated:
                migrated_count += 1
        
        # 提交所有更改
        db.session.commit()
        print(f"✅ 成功迁移 {migrated_count} 个会话的数据")
        
    except Exception as e:
        print(f"❌ 数据迁移失败: {str(e)}")
        db.session.rollback()
        raise

def migrate_config(config_name):
    """为指定配置执行迁移"""
    print(f"\n{'='*50}")
    print(f"🔧 开始为 {config_name} 配置执行迁移...")
    print(f"{'='*50}")
    
    try:
        app = create_app(config_name)
        with app.app_context():
            print(f"数据库URI: {app.config.get('SQLALCHEMY_DATABASE_URI', '未配置')}")
            add_multiple_ids_columns()
            migrate_existing_data()
            print(f"\n✅ {config_name} 配置迁移完成！")
    except Exception as e:
        print(f"\n❌ {config_name} 配置迁移失败: {e}")
        raise

if __name__ == '__main__':
    # 导入Flask应用
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from app import create_app
    from dotenv import load_dotenv
    
    # 加载环境变量
    load_dotenv()
    
    print("🚀 开始为所有配置环境执行聊天会话多资源ID支持迁移...")
    
    # 要迁移的配置列表
    configs_to_migrate = ['development', 'winstar']
    
    success_count = 0
    failed_configs = []
    
    for config_name in configs_to_migrate:
        try:
            migrate_config(config_name)
            success_count += 1
        except Exception as e:
            failed_configs.append((config_name, str(e)))
            print(f"⚠️  {config_name} 配置迁移失败，继续下一个配置...")
    
    print(f"\n{'='*60}")
    print("📊 迁移结果汇总:")
    print(f"✅ 成功: {success_count}/{len(configs_to_migrate)} 个配置")
    
    if failed_configs:
        print("❌ 失败的配置:")
        for config_name, error in failed_configs:
            print(f"   - {config_name}: {error}")
    else:
        print("🎉 所有配置迁移成功！")
    
    print(f"{'='*60}")