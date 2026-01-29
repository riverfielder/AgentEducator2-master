#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：添加章节管理支持
为videos和documents表添加chapter_id字段，创建course_chapters表

运行方法：
python backend/migrations/migrate_chapter_support.py

作者：课程详情管理功能开发
日期：2024年
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from models.models import db
from config.config import Config
import pymysql
from datetime import datetime
import uuid

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def check_table_exists(cursor, table_name):
    """检查表是否存在"""
    cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
    return cursor.fetchone() is not None

def check_column_exists(cursor, table_name, column_name):
    """检查列是否存在"""
    cursor.execute(f"SHOW COLUMNS FROM {table_name} LIKE '{column_name}'")
    return cursor.fetchone() is not None

def check_foreign_key_exists(cursor, table_name, constraint_name):
    """检查外键约束是否存在"""
    cursor.execute(f"""
        SELECT CONSTRAINT_NAME 
        FROM information_schema.KEY_COLUMN_USAGE 
        WHERE TABLE_NAME = '{table_name}' 
        AND CONSTRAINT_NAME = '{constraint_name}'
        AND TABLE_SCHEMA = DATABASE()
    """)
    return cursor.fetchone() is not None

def check_index_exists(cursor, table_name, index_name):
    """检查索引是否存在"""
    cursor.execute(f"SHOW INDEX FROM {table_name} WHERE Key_name = '{index_name}'")
    return cursor.fetchone() is not None

def migrate_database():
    """执行数据库迁移"""
    app = create_app()
    
    with app.app_context():
        try:
            # 获取数据库连接配置
            db_config = {
                'host': app.config['DB_HOST'],
                'port': app.config['DB_PORT'],
                'user': app.config['DB_USER'],
                'password': app.config['DB_PASSWORD'],
                'database': app.config['DB_NAME'],
                'charset': 'utf8mb4'
            }
            
            print("🚀 开始数据库迁移...")
            print(f"连接数据库: {db_config['host']}:{db_config['port']}/{db_config['database']}")
            
            # 连接数据库
            connection = pymysql.connect(**db_config)
            cursor = connection.cursor()
            
            # 1. 创建course_chapters表（如果不存在）
            print("\n📋 步骤1: 检查并创建course_chapters表...")
            if not check_table_exists(cursor, 'course_chapters'):
                print("创建course_chapters表...")
                cursor.execute("""
                    CREATE TABLE `course_chapters` (
                        `id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
                        `course_id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
                        `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
                        `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
                        `chapter_number` int NOT NULL DEFAULT 1 COMMENT '章节编号',
                        `order_index` int NULL DEFAULT 0,
                        `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP,
                        `update_time` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        `is_deleted` tinyint(1) NULL DEFAULT 0,
                        PRIMARY KEY (`id`) USING BTREE,
                        INDEX `idx_course_chapters_course_id`(`course_id` ASC) USING BTREE,
                        INDEX `idx_course_chapters_order_index`(`order_index` ASC) USING BTREE,
                        UNIQUE INDEX `uk_course_chapter_number`(`course_id` ASC, `chapter_number` ASC, `is_deleted` ASC) USING BTREE,
                        CONSTRAINT `fk_course_chapters_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
                    ) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '课程章节表' ROW_FORMAT = Dynamic
                """)
                print("✅ course_chapters表创建成功")
            else:
                print("✅ course_chapters表已存在")
            
            # 2. 为videos表添加chapter_id字段
            print("\n📹 步骤2: 为videos表添加chapter_id字段...")
            if not check_column_exists(cursor, 'videos', 'chapter_id'):
                print("添加videos.chapter_id字段...")
                cursor.execute("""
                    ALTER TABLE `videos` 
                    ADD COLUMN `chapter_id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '所属章节ID' 
                    AFTER `course_id`
                """)
                print("✅ videos.chapter_id字段添加成功")
            else:
                print("✅ videos.chapter_id字段已存在")
            
            # 为videos表添加chapter_id索引
            if not check_index_exists(cursor, 'videos', 'idx_videos_chapter_id'):
                print("添加videos.chapter_id索引...")
                cursor.execute("ALTER TABLE `videos` ADD INDEX `idx_videos_chapter_id`(`chapter_id` ASC) USING BTREE")
                print("✅ videos章节索引添加成功")
            else:
                print("✅ videos章节索引已存在")
            
            # 为videos表添加章节内排序索引
            if not check_index_exists(cursor, 'videos', 'idx_videos_chapter_order'):
                print("添加videos章节排序索引...")
                cursor.execute("ALTER TABLE `videos` ADD INDEX `idx_videos_chapter_order`(`chapter_id` ASC, `order_index` ASC) USING BTREE")
                print("✅ videos章节排序索引添加成功")
            else:
                print("✅ videos章节排序索引已存在")
            
            # 为videos表添加外键约束
            if not check_foreign_key_exists(cursor, 'videos', 'fk_videos_chapter'):
                print("添加videos章节外键约束...")
                cursor.execute("""
                    ALTER TABLE `videos` 
                    ADD CONSTRAINT `fk_videos_chapter` 
                    FOREIGN KEY (`chapter_id`) REFERENCES `course_chapters` (`id`) 
                    ON DELETE RESTRICT ON UPDATE RESTRICT
                """)
                print("✅ videos章节外键约束添加成功")
            else:
                print("✅ videos章节外键约束已存在")
            
            # 3. 为documents表添加chapter_id字段
            print("\n📄 步骤3: 为documents表添加chapter_id字段...")
            if not check_column_exists(cursor, 'documents', 'chapter_id'):
                print("添加documents.chapter_id字段...")
                cursor.execute("""
                    ALTER TABLE `documents` 
                    ADD COLUMN `chapter_id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '所属章节ID' 
                    AFTER `course_id`
                """)
                print("✅ documents.chapter_id字段添加成功")
            else:
                print("✅ documents.chapter_id字段已存在")
            
            # 为documents表添加chapter_id索引
            if not check_index_exists(cursor, 'documents', 'idx_documents_chapter_id'):
                print("添加documents.chapter_id索引...")
                cursor.execute("ALTER TABLE `documents` ADD INDEX `idx_documents_chapter_id`(`chapter_id` ASC) USING BTREE")
                print("✅ documents章节索引添加成功")
            else:
                print("✅ documents章节索引已存在")
            
            # 为documents表添加外键约束
            if not check_foreign_key_exists(cursor, 'documents', 'fk_documents_chapter'):
                print("添加documents章节外键约束...")
                cursor.execute("""
                    ALTER TABLE `documents` 
                    ADD CONSTRAINT `fk_documents_chapter` 
                    FOREIGN KEY (`chapter_id`) REFERENCES `course_chapters` (`id`) 
                    ON DELETE SET NULL ON UPDATE CASCADE
                """)
                print("✅ documents章节外键约束添加成功")
            else:
                print("✅ documents章节外键约束已存在")
            
            # 4. 检查并添加order_index字段（如果不存在）
            print("\n🔢 步骤4: 检查排序字段...")
            
            # 检查videos表的order_index字段
            if not check_column_exists(cursor, 'videos', 'order_index'):
                print("添加videos.order_index字段...")
                cursor.execute("""
                    ALTER TABLE `videos` 
                    ADD COLUMN `order_index` int NULL DEFAULT 0 COMMENT '章节内排序' 
                    AFTER `chapter_id`
                """)
                print("✅ videos.order_index字段添加成功")
            else:
                print("✅ videos.order_index字段已存在")
            
            # 检查documents表的order_index字段
            if not check_column_exists(cursor, 'documents', 'order_index'):
                print("添加documents.order_index字段...")
                cursor.execute("""
                    ALTER TABLE `documents` 
                    ADD COLUMN `order_index` int NULL DEFAULT 0 COMMENT '排序权重' 
                    AFTER `chapter_id`
                """)
                print("✅ documents.order_index字段添加成功")
            else:
                print("✅ documents.order_index字段已存在")
            
            # 5. 提交所有更改
            connection.commit()
            print("\n🎉 数据库迁移完成！")
            
            # 6. 验证迁移结果
            print("\n🔍 验证迁移结果...")
            print("检查表结构...")
            
            # 检查course_chapters表
            cursor.execute("DESCRIBE course_chapters")
            chapters_columns = cursor.fetchall()
            print(f"✅ course_chapters表有 {len(chapters_columns)} 个字段")
            
            # 检查videos表的chapter_id字段
            cursor.execute("DESCRIBE videos")
            videos_columns = [col[0] for col in cursor.fetchall()]
            if 'chapter_id' in videos_columns and 'order_index' in videos_columns:
                print("✅ videos表章节字段完整")
            else:
                print("❌ videos表章节字段不完整")
            
            # 检查documents表的chapter_id字段
            cursor.execute("DESCRIBE documents")
            documents_columns = [col[0] for col in cursor.fetchall()]
            if 'chapter_id' in documents_columns and 'order_index' in documents_columns:
                print("✅ documents表章节字段完整")
            else:
                print("❌ documents表章节字段不完整")
            
            print("\n📊 迁移统计:")
            cursor.execute("SELECT COUNT(*) FROM course_chapters")
            chapters_count = cursor.fetchone()[0]
            print(f"- 课程章节数量: {chapters_count}")
            
            cursor.execute("SELECT COUNT(*) FROM videos WHERE chapter_id IS NOT NULL")
            assigned_videos = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM videos")
            total_videos = cursor.fetchone()[0]
            print(f"- 已分配章节的视频: {assigned_videos}/{total_videos}")
            
            cursor.execute("SELECT COUNT(*) FROM documents WHERE chapter_id IS NOT NULL")
            assigned_docs = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM documents")
            total_docs = cursor.fetchone()[0]
            print(f"- 已分配章节的文档: {assigned_docs}/{total_docs}")
            
        except Exception as e:
            print(f"❌ 迁移失败: {str(e)}")
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

def create_sample_chapters():
    """为现有课程创建示例章节（可选）"""
    app = create_app()
    
    with app.app_context():
        try:
            from models.models import Course, CourseChapter
            
            print("\n📚 创建示例章节...")
            
            # 获取所有课程
            courses = Course.query.filter_by(is_deleted=False).all()
            
            for course in courses:
                # 检查课程是否已有章节
                existing_chapters = CourseChapter.query.filter_by(course_id=course.id, is_deleted=False).count()
                
                if existing_chapters == 0:
                    print(f"为课程 '{course.name}' 创建默认章节...")
                    
                    # 创建默认章节
                    default_chapters = [
                        {"title": "第一章 课程介绍", "description": "课程概述与学习目标"},
                        {"title": "第二章 基础知识", "description": "基础概念与原理"},
                        {"title": "第三章 实践应用", "description": "实际应用与案例分析"},
                    ]
                    
                    for i, chapter_data in enumerate(default_chapters):
                        chapter = CourseChapter(
                            id=str(uuid.uuid4()),
                            course_id=course.id,
                            title=chapter_data["title"],
                            description=chapter_data["description"],
                            chapter_number=i + 1,
                            order_index=i,
                            create_time=datetime.now(),
                            update_time=datetime.now(),
                            is_deleted=False
                        )
                        db.session.add(chapter)
                    
                    print(f"✅ 为课程 '{course.name}' 创建了 {len(default_chapters)} 个章节")
                else:
                    print(f"✅ 课程 '{course.name}' 已有 {existing_chapters} 个章节")
            
            db.session.commit()
            print("🎉 示例章节创建完成！")
            
        except Exception as e:
            print(f"❌ 创建示例章节失败: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    print("=" * 60)
    print("🔧 闻道平台数据库迁移工具")
    print("功能：添加课程章节管理支持")
    print("=" * 60)
    
    try:
        # 执行数据库结构迁移
        migrate_database()
        
        # 询问是否创建示例章节
        create_samples = input("\n是否为现有课程创建示例章节？(y/N): ").strip().lower()
        if create_samples in ['y', 'yes']:
            create_sample_chapters()
        
        print("\n🎉 迁移完成！团队成员现在可以使用章节管理功能了。")
        print("\n📝 使用说明:")
        print("1. 启动后端服务: python backend/app.py")
        print("2. 启动前端服务: cd frontend && npm run dev")
        print("3. 访问课程详情管理页面即可使用章节功能")
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {str(e)}")
        print("请检查数据库连接配置和权限设置")
        sys.exit(1) 