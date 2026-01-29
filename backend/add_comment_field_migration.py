#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为StudentAnswer表添加comment字段
用于保存批改评语
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.models import db
from sqlalchemy import text
from app import create_app
from config import WinstarConfig  # 假设WinstarConfig在config.py中

def add_comment_field():
    """为StudentAnswer表添加comment字段"""
    app = create_app(WinstarConfig)  # 使用WinstarConfig
    
    with app.app_context():
        try:
            # 检查字段是否已存在
            result = db.session.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'student_answers' 
                AND COLUMN_NAME = 'comment'
                AND TABLE_SCHEMA = DATABASE()
            """))
            
            if result.fetchone() is None:
                # 字段不存在，添加字段
                print("正在为student_answers表添加comment字段...")
                db.session.execute(text("""
                    ALTER TABLE student_answers 
                    ADD COLUMN comment TEXT NULL COMMENT '批改评语'
                """))
                db.session.commit()
                print("✅ 成功添加comment字段")
            else:
                print("ℹ️ comment字段已存在，跳过添加")
                
        except Exception as e:
            print(f"❌ 添加字段失败: {str(e)}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    print("开始数据库迁移...")
    add_comment_field()
    print("数据库迁移完成！")
