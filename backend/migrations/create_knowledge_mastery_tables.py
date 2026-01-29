#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识点掌握程度相关表创建脚本
创建时间: 2024
"""

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

def check_table_exists(connection, table_name):
    """检查表是否存在"""
    result = connection.execute(text(f"""
        SELECT COUNT(*) as count 
        FROM information_schema.tables 
        WHERE table_schema = DATABASE() 
        AND table_name = '{table_name}'
    """))
    return result.fetchone().count > 0

def create_knowledge_mastery_tables():
    """创建知识点掌握程度相关表"""
    try:
        # 创建数据库连接
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
        with engine.connect() as connection:
            # 开始事务
            trans = connection.begin()
            
            try:
                # 1. 创建知识点掌握程度表
                if not check_table_exists(connection, 'knowledge_point_mastery'):
                    print("Creating knowledge_point_mastery table...")
                    create_mastery_table = """
                    CREATE TABLE IF NOT EXISTS knowledge_point_mastery (
                        id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL PRIMARY KEY,
                        user_id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户ID',
                        keyword_id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '知识点ID',
                        mastery_level FLOAT DEFAULT 0.0 COMMENT '掌握程度 0-1',
                        material_progress FLOAT DEFAULT 0.0 COMMENT '教学材料进度 0-1',
                        exercise_score FLOAT DEFAULT 0.0 COMMENT '练习得分 0-1',
                        sub_knowledge_contribution FLOAT DEFAULT 0.0 COMMENT '子知识点贡献 0-1',
                        calculation_details JSON COMMENT '计算详情',
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE CASCADE,
                        UNIQUE KEY uk_user_keyword (user_id, keyword_id),
                        INDEX idx_mastery_user (user_id),
                        INDEX idx_mastery_keyword (keyword_id),
                        INDEX idx_mastery_level (mastery_level)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='知识点掌握程度表';
                    """
                    connection.execute(text(create_mastery_table))
                    print("✓ knowledge_point_mastery table created successfully")
                else:
                    print("knowledge_point_mastery table already exists")
                
                # 2. 创建题目-知识点关联表
                if not check_table_exists(connection, 'question_keywords'):
                    print("Creating question_keywords table...")
                    create_question_keywords_table = """
                    CREATE TABLE IF NOT EXISTS question_keywords (
                        id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL PRIMARY KEY,
                        question_id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '题目ID',
                        keyword_id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '知识点ID',
                        weight FLOAT DEFAULT 1.0 COMMENT '权重',
                        difficulty_level INT DEFAULT 1 COMMENT '难度等级 1-5',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
                        FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE CASCADE,
                        UNIQUE KEY uk_question_keyword (question_id, keyword_id),
                        INDEX idx_qk_question (question_id),
                        INDEX idx_qk_keyword (keyword_id),
                        INDEX idx_qk_difficulty (difficulty_level)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='题目知识点关联表';
                    """
                    connection.execute(text(create_question_keywords_table))
                    print("✓ question_keywords table created successfully")
                else:
                    print("question_keywords table already exists")
                
                # 3. 创建文档学习进度表
                if not check_table_exists(connection, 'document_progress'):
                    print("Creating document_progress table...")
                    create_document_progress_table = """
                    CREATE TABLE IF NOT EXISTS document_progress (
                        id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL PRIMARY KEY,
                        user_id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户ID',
                        document_id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '文档ID',
                        progress FLOAT DEFAULT 0.0 COMMENT '阅读进度 0-1',
                        last_position INT DEFAULT 0 COMMENT '最后阅读位置',
                        completed BOOLEAN DEFAULT FALSE COMMENT '是否完成',
                        reading_time INT DEFAULT 0 COMMENT '阅读时长(秒)',
                        last_read_time DATETIME COMMENT '最后阅读时间',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                        UNIQUE KEY uk_user_document (user_id, document_id),
                        INDEX idx_dp_user (user_id),
                        INDEX idx_dp_document (document_id),
                        INDEX idx_dp_progress (progress),
                        INDEX idx_dp_completed (completed)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='文档学习进度表';
                    """
                    connection.execute(text(create_document_progress_table))
                    print("✓ document_progress table created successfully")
                else:
                    print("document_progress table already exists")
                
                # 提交事务
                trans.commit()
                print("\n✅ All knowledge mastery tables created successfully!")
                
            except Exception as e:
                # 回滚事务
                trans.rollback()
                print(f"❌ Error creating tables: {str(e)}")
                raise
                
    except SQLAlchemyError as e:
        print(f"❌ Database connection error: {str(e)}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        raise

def drop_knowledge_mastery_tables():
    """删除知识点掌握程度相关表（用于回滚）"""
    try:
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
        with engine.connect() as connection:
            trans = connection.begin()
            
            try:
                # 按依赖关系逆序删除表
                tables_to_drop = [
                    'knowledge_point_mastery',
                    'question_keywords', 
                    'document_progress'
                ]
                
                for table_name in tables_to_drop:
                    if check_table_exists(connection, table_name):
                        print(f"Dropping {table_name} table...")
                        connection.execute(text(f"DROP TABLE {table_name};"))
                        print(f"✓ {table_name} table dropped")
                
                trans.commit()
                print("\n✅ All knowledge mastery tables dropped successfully!")
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error dropping tables: {str(e)}")
                raise
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Knowledge Mastery Tables Migration')
    parser.add_argument('--drop', action='store_true', help='Drop tables instead of creating them')
    
    args = parser.parse_args()
    
    if args.drop:
        print("🗑️  Dropping knowledge mastery tables...")
        drop_knowledge_mastery_tables()
    else:
        print("🚀 Creating knowledge mastery tables...")
        create_knowledge_mastery_tables()