from sqlalchemy import create_engine, text, inspect
import sys
import os
import json
import uuid
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import WinstarConfig

db_uri = WinstarConfig.SQLALCHEMY_DATABASE_URI

def check_table_exists(connection, table_name):
    inspector = inspect(connection)
    return table_name in inspector.get_table_names()

def check_column_exists(connection, table_name, column_name):
    inspector = inspect(connection)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def migrate_question_bank_to_question():
    """将question_bank表的功能迁移到question表"""
    engine = create_engine(db_uri)
    
    with engine.connect() as connection:
        print("开始迁移 question_bank 到 question 表...")
        
        # 1. 检查表是否存在
        if not check_table_exists(connection, 'questions'):
            print("错误：questions表不存在，请先创建questions表")
            return False
            
        if not check_table_exists(connection, 'question_bank'):
            print("question_bank表不存在，无需迁移")
            return True
        
        # 2. 为questions表添加缺失的字段
        print("为questions表添加缺失字段...")
        
        # 添加category字段
        if not check_column_exists(connection, 'questions', 'category'):
            print("添加category字段...")
            connection.execute(text("ALTER TABLE questions ADD COLUMN category VARCHAR(64);"))
        
        # 添加difficulty字段
        if not check_column_exists(connection, 'questions', 'difficulty'):
            print("添加difficulty字段...")
            connection.execute(text("ALTER TABLE questions ADD COLUMN difficulty VARCHAR(16);"))
        
        # 添加tags字段
        if not check_column_exists(connection, 'questions', 'tags'):
            print("添加tags字段...")
            connection.execute(text("ALTER TABLE questions ADD COLUMN tags JSON;"))
        
        # 添加remark字段
        if not check_column_exists(connection, 'questions', 'remark'):
            print("添加remark字段...")
            connection.execute(text("ALTER TABLE questions ADD COLUMN remark TEXT;"))
        
        # 添加creator_id字段
        if not check_column_exists(connection, 'questions', 'creator_id'):
            print("添加creator_id字段...")
            connection.execute(text("ALTER TABLE questions ADD COLUMN creator_id VARCHAR(36);"))
        
        # 添加created_at字段（如果不存在）
        if not check_column_exists(connection, 'questions', 'created_at'):
            print("添加created_at字段...")
            connection.execute(text("ALTER TABLE questions ADD COLUMN created_at DATETIME;"))
        
        # 3. 创建虚拟课程和教师用于题库作业
        print("创建虚拟课程和教师用于题库作业...")
        
        # 检查是否已存在题库课程
        result = connection.execute(text("SELECT id FROM courses WHERE name = '题库课程' LIMIT 1;"))
        course_row = result.fetchone()
        
        if course_row:
            course_id = course_row[0]
            print(f"使用现有题库课程: {course_id}")
        else:
            # 创建新的题库课程
            course_id = str(uuid.uuid4())
            current_time = int(datetime.now().timestamp())
            connection.execute(text("""
                INSERT INTO courses (id, name, code, description, image_url, start_date, end_date, hours, 
                                   student_count, status, is_public, semester, teacher_id, create_time, update_time)
                VALUES (:course_id, '题库课程', 'QUESTION_BANK', '用于存储题库题目的虚拟课程', NULL, 
                       :start_date, :end_date, 0, 0, 1, FALSE, '题库学期', NULL, :create_time, :update_time)
            """), {
                'course_id': course_id,
                'start_date': current_time,
                'end_date': current_time + 365 * 24 * 3600,  # 一年后
                'create_time': datetime.now(),
                'update_time': datetime.now()
            })
            print(f"创建新题库课程: {course_id}")
        
        # 检查是否已存在题库教师
        result = connection.execute(text("SELECT id FROM users WHERE username = 'question_bank_teacher' LIMIT 1;"))
        teacher_row = result.fetchone()
        
        if teacher_row:
            teacher_id = teacher_row[0]
            print(f"使用现有题库教师: {teacher_id}")
        else:
            # 创建新的题库教师
            teacher_id = str(uuid.uuid4())
            connection.execute(text("""
                INSERT INTO users (id, username, password, email, role, avatar, class_name, status, create_time, update_time)
                VALUES (:teacher_id, 'question_bank_teacher', 'question_bank_password', 'question_bank@example.com', 
                       'teacher', NULL, NULL, 'active', :create_time, :update_time)
            """), {
                'teacher_id': teacher_id,
                'create_time': datetime.now(),
                'update_time': datetime.now()
            })
            print(f"创建新题库教师: {teacher_id}")
        
        # 4. 创建临时作业用于存储题库题目
        print("创建临时作业用于存储题库题目...")
        
        # 检查是否已存在题库作业
        result = connection.execute(text("SELECT id FROM assignments WHERE title = '题库题目' LIMIT 1;"))
        assignment_row = result.fetchone()
        
        if assignment_row:
            assignment_id = assignment_row[0]
            print(f"使用现有题库作业: {assignment_id}")
        else:
            # 创建新的题库作业
            assignment_id = str(uuid.uuid4())
            connection.execute(text("""
                INSERT INTO assignments (id, title, course_id, teacher_id, due_date, status, create_time, update_time)
                VALUES (:assignment_id, '题库题目', :course_id, :teacher_id, :due_date, 'draft', :create_time, :update_time)
            """), {
                'assignment_id': assignment_id,
                'course_id': course_id,
                'teacher_id': teacher_id,
                'due_date': datetime(2099, 12, 31),  # 设置一个很远的截止日期
                'create_time': datetime.now(),
                'update_time': datetime.now()
            })
            print(f"创建新题库作业: {assignment_id}")
        
        # 5. 迁移数据
        print("开始迁移数据...")
        
        # 获取question_bank表中的所有数据
        result = connection.execute(text("SELECT * FROM question_bank;"))
        question_bank_data = result.fetchall()
        
        print(f"找到 {len(question_bank_data)} 条题库数据")
        
        for row in question_bank_data:
            # 转换字段映射
            question_type_map = {
                'single': 'single',
                'multiple': 'multiple', 
                'blank': 'blank',
                'essay': 'essay'
            }
            
            # 处理答案字段
            answer_data = row.answer
            if isinstance(answer_data, list):
                if len(answer_data) == 1:
                    # 单选题
                    answer_str = answer_data[0]
                    reference_str = None
                else:
                    # 多选题
                    answer_str = ','.join(answer_data)
                    reference_str = None
            else:
                # 填空题或问答题
                answer_str = str(answer_data) if answer_data else None
                reference_str = str(answer_data) if answer_data else None
            
            # 处理选项字段
            options_data = row.options
            if options_data:
                options_json = json.dumps(options_data, ensure_ascii=False)
            else:
                options_json = None
            
            # 处理标签字段
            tags_data = row.tags
            if tags_data:
                tags_json = json.dumps(tags_data, ensure_ascii=False)
            else:
                tags_json = None
            
            # 插入到questions表
            question_id = str(uuid.uuid4())
            connection.execute(text("""
                INSERT INTO questions (
                    id, assignment_id, type, content, options, answers, reference, 
                    explanation, order_num, max_score, keywords, create_time, update_time,
                    category, difficulty, tags, remark, creator_id, created_at
                ) VALUES (
                    :question_id, :assignment_id, :type, :content, :options, :answers, :reference,
                    :explanation, :order_num, :max_score, :keywords, :create_time, :update_time,
                    :category, :difficulty, :tags, :remark, :creator_id, :created_at
                )
            """), {
                'question_id': question_id,
                'assignment_id': assignment_id,
                'type': question_type_map.get(row.question_type, 'single'),
                'content': row.content,
                'options': options_json,
                'answers': answer_str,
                'reference': reference_str,
                'explanation': row.explanation,
                'order_num': 0,  # 默认顺序
                'max_score': 5.0,  # 默认分数
                'keywords': None,  # 暂时为空
                'create_time': datetime.now(),
                'update_time': datetime.now(),
                'category': row.category,
                'difficulty': row.difficulty,
                'tags': tags_json,
                'remark': row.remark,
                'creator_id': row.creator_id,
                'created_at': row.created_at or datetime.now()
            })
        
        print(f"成功迁移 {len(question_bank_data)} 条数据")
        
        # 6. 删除question_bank表
        print("删除question_bank表...")
        connection.execute(text("DROP TABLE question_bank;"))
        
        # 提交所有更改
        connection.commit()
        
        print("迁移完成！")
        return True

if __name__ == '__main__':
    migrate_question_bank_to_question()