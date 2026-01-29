#!/usr/bin/env python3
import sys
import os
import uuid
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from flask import Flask
from models.models import db
from config.config import Config, WinstarConfig
from sqlalchemy import text, inspect

def check_table_exists(connection, table_name):
    """检查表是否存在"""
    inspector = inspect(connection)
    return table_name in inspector.get_table_names()

def check_column_exists(connection, table_name, column_name):
    """检查列是否存在"""
    inspector = inspect(connection)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def migrate_category_to_course_id(config_class):
    """将Question表的category字段迁移为course_id字段"""
    # 创建Flask应用
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = config_class.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化数据库
    db.init_app(app)
    
    with app.app_context():
        print(f"开始迁移 Question 表的 category 字段到 course_id 字段... (使用 {config_class.__name__})")
        
        # 使用db.session进行事务管理
        try:
            # 1. 检查questions表是否存在
            if not check_table_exists(db.engine, 'questions'):
                print("错误：questions表不存在")
                return False
            
            # 2. 检查courses表是否存在
            if not check_table_exists(db.engine, 'courses'):
                print("错误：courses表不存在，无法创建外键约束")
                return False
            
            # 3. 检查category字段是否存在
            if not check_column_exists(db.engine, 'questions', 'category'):
                print("category字段不存在，无需迁移")
                return True
            
            # 4. 检查course_id字段是否已存在
            if check_column_exists(db.engine, 'questions', 'course_id'):
                print("course_id字段已存在，跳过迁移")
                return True
            
            # 开始事务（使用db.session）
            db.session.begin()
            
            # 5. 添加course_id字段（先不加外键约束）
            print("添加course_id字段...")
            db.session.execute(text("""
                ALTER TABLE questions 
                ADD COLUMN course_id CHAR(36) NOT NULL DEFAULT '' 
                COMMENT '所属课程ID'
            """))
            
            # 6. 将category字段的数据复制到course_id字段
            print("复制category数据到course_id字段...")
            db.session.execute(text("""
                UPDATE questions 
                SET course_id = category 
                WHERE category IS NOT NULL AND category != ''
            """))
            
            # 7. 验证数据迁移和处理无效的course_id
            # 7.1 处理空值
            result = db.session.execute(text("""
                SELECT COUNT(*) as count 
                FROM questions 
                WHERE course_id = '' OR course_id IS NULL
            """))
            empty_count = result.fetchone()[0]
            
            if empty_count > 0:
                print(f"警告：有 {empty_count} 条记录的course_id为空")
                # 可以选择设置默认值或者回滚
                # 这里我们设置一个默认的UUID
                default_course_id = str(uuid.uuid4())
                print(f"为空记录设置默认course_id: {default_course_id}")
                db.session.execute(text("""
                    UPDATE questions 
                    SET course_id = :default_id 
                    WHERE course_id = '' OR course_id IS NULL
                """), {"default_id": default_course_id})
            
            # 7.2 检查并处理无效的course_id（在courses表中不存在的）
            result = db.session.execute(text("""
                SELECT DISTINCT q.course_id, COUNT(*) as count
                FROM questions q 
                LEFT JOIN courses c ON q.course_id = c.id 
                WHERE c.id IS NULL
                GROUP BY q.course_id
            """))
            invalid_course_ids = result.fetchall()
            
            if invalid_course_ids:
                print(f"\n发现 {len(invalid_course_ids)} 个无效的course_id，将创建默认课程或使用现有课程:")
                
                # 获取第一个现有课程作为默认课程
                result = db.session.execute(text("SELECT id FROM courses LIMIT 1"))
                first_course = result.fetchone()
                
                if first_course:
                    default_course_id = first_course[0]
                    print(f"使用现有课程ID作为默认值: {default_course_id}")
                else:
                    # 如果没有任何课程，创建一个默认课程
                    default_course_id = str(uuid.uuid4())
                    print(f"创建默认课程: {default_course_id}")
                    db.session.execute(text("""
                        INSERT INTO courses (id, name, description, created_at) 
                        VALUES (:course_id, '默认课程', '系统自动创建的默认课程', NOW())
                    """), {"course_id": default_course_id})
                
                # 更新所有无效的course_id
                for invalid_id, count in invalid_course_ids:
                    print(f"  更新无效course_id '{invalid_id}' ({count} 条记录) -> {default_course_id}")
                    db.session.execute(text("""
                        UPDATE questions 
                        SET course_id = :default_id 
                        WHERE course_id = :invalid_id
                    """), {"default_id": default_course_id, "invalid_id": invalid_id})
            
            # 8. 添加外键约束
            print("添加外键约束...")
            db.session.execute(text("""
                ALTER TABLE questions 
                ADD CONSTRAINT fk_questions_course_id 
                FOREIGN KEY (course_id) REFERENCES courses(id) 
                ON DELETE CASCADE ON UPDATE CASCADE
            """))
            
            # 9. 删除原来的category字段
            print("删除原category字段...")
            db.session.execute(text("""
                ALTER TABLE questions DROP COLUMN category
            """))
            
            # 提交事务
            db.session.commit()
            print("迁移完成！")
            return True
            
        except Exception as e:
            # 回滚事务
            db.session.rollback()
            print(f"迁移失败，已回滚: {str(e)}")
            return False
        finally:
            db.session.close()

def main():
    """主函数"""
    print("Question表category字段迁移到course_id字段")
    print("="*50)
    
    # 选择配置
    config_choice = input("选择配置环境 (1: Config, 2: WinstarConfig): ").strip()
    
    if config_choice == "1":
        config_class = Config
    elif config_choice == "2":
        config_class = WinstarConfig
    else:
        print("无效选择，使用默认配置 WinstarConfig")
        config_class = WinstarConfig
    
    # 确认迁移
    confirm = input(f"确认要使用 {config_class.__name__} 进行迁移吗？(y/N): ").strip().lower()
    if confirm != 'y':
        print("迁移已取消")
        return
    
    # 执行迁移
    success = migrate_category_to_course_id(config_class)
    
    if success:
        print("\n迁移成功完成！")
    else:
        print("\n迁移失败！")

if __name__ == "__main__":
    main()