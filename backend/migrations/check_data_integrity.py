#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from flask import Flask
from models.models import db
from config.config import WinstarConfig
from sqlalchemy import text

def check_data_integrity():
    """检查questions表中的course_id数据完整性"""
    # 创建Flask应用
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = WinstarConfig.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化数据库
    db.init_app(app)
    
    with app.app_context():
        print("检查数据完整性...")
        
        # 1. 检查questions表中有多少条记录
        result = db.session.execute(text("SELECT COUNT(*) FROM questions"))
        total_questions = result.fetchone()[0]
        print(f"questions表总记录数: {total_questions}")
        
        # 2. 检查courses表中有多少条记录
        result = db.session.execute(text("SELECT COUNT(*) FROM courses"))
        total_courses = result.fetchone()[0]
        print(f"courses表总记录数: {total_courses}")
        
        # 3. 检查questions表中不存在对应courses记录的course_id
        result = db.session.execute(text("""
            SELECT DISTINCT q.course_id 
            FROM questions q 
            LEFT JOIN courses c ON q.course_id = c.id 
            WHERE c.id IS NULL
            LIMIT 20
        """))
        invalid_course_ids = result.fetchall()
        
        if invalid_course_ids:
            print(f"\n发现 {len(invalid_course_ids)} 个无效的course_id:")
            for row in invalid_course_ids:
                course_id = row[0]
                # 统计每个无效course_id的记录数
                count_result = db.session.execute(text("""
                    SELECT COUNT(*) FROM questions WHERE course_id = :course_id
                """), {"course_id": course_id})
                count = count_result.fetchone()[0]
                print(f"  course_id: {course_id} (影响 {count} 条记录)")
        else:
            print("\n所有course_id都有效！")
        
        # 4. 检查courses表中的一些示例ID
        print("\ncourses表中的前10个ID:")
        result = db.session.execute(text("SELECT id, name FROM courses LIMIT 10"))
        courses = result.fetchall()
        for course in courses:
            print(f"  ID: {course[0]}, Name: {course[1]}")
        
        # 5. 检查questions表中category字段的一些示例值
        print("\nquestions表中category字段的前10个值:")
        result = db.session.execute(text("SELECT DISTINCT category FROM questions WHERE category IS NOT NULL LIMIT 10"))
        categories = result.fetchall()
        for category in categories:
            print(f"  Category: {category[0]}")

if __name__ == "__main__":
    check_data_integrity()