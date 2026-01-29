from sqlalchemy import create_engine, text, inspect
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.config.config import Config

def check_table_exists(connection, table_name):
    """检查表是否存在"""
    inspector = inspect(connection)
    return table_name in inspector.get_table_names()

def create_tables():
    # 创建数据库连接
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    
    with engine.connect() as connection:
        # 检查并创建作业表
        if not check_table_exists(connection, 'assignments'):
            print("Creating assignments table...")
            create_assignments_table = """
            CREATE TABLE IF NOT EXISTS assignments (
                id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL PRIMARY KEY,
                title VARCHAR(255) NOT NULL COMMENT '作业标题',
                course_id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '所属课程ID',
                teacher_id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '教师ID',
                due_date DATETIME NOT NULL COMMENT '截止日期',
                publish_time DATETIME COMMENT '发布时间',
                status VARCHAR(20) NOT NULL DEFAULT 'draft' COMMENT '作业状态: draft, published',
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                is_deleted BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (course_id) REFERENCES courses(id),
                FOREIGN KEY (teacher_id) REFERENCES users(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
            """
            connection.execute(text(create_assignments_table))
            
            # 创建索引
            print("Creating indexes for assignments table...")
            connection.execute(text("CREATE INDEX idx_assignments_course ON assignments(course_id);"))
            connection.execute(text("CREATE INDEX idx_assignments_teacher ON assignments(teacher_id);"))
            connection.execute(text("CREATE INDEX idx_assignments_status ON assignments(status);"))
            
        else:
            print("Assignments table already exists.")
            
        # 检查并创建题目表
        if not check_table_exists(connection, 'questions'):
            print("Creating questions table...")
            create_questions_table = """
            CREATE TABLE IF NOT EXISTS questions (
                id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL PRIMARY KEY,
                assignment_id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '所属作业ID',
                content TEXT NOT NULL COMMENT '题目内容',
                type VARCHAR(20) NOT NULL COMMENT '题目类型: single, multiple, blank',
                options JSON COMMENT '选项（单选/多选题）',
                answers TEXT COMMENT '答案',
                reference TEXT COMMENT '参考答案（问答题）',
                explanation TEXT COMMENT '答案解析',
                max_score FLOAT NOT NULL DEFAULT 5.0 COMMENT '题目满分分数',
                order_num INT NOT NULL DEFAULT 0 COMMENT '题目顺序',
                keywords JSON COMMENT '相关知识点列表，JSON格式',
                create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                is_deleted BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (assignment_id) REFERENCES assignments(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
            """
            connection.execute(text(create_questions_table))
            
            # 创建索引
            print("Creating indexes for questions table...")
            connection.execute(text("CREATE INDEX idx_questions_assignment ON questions(assignment_id);"))
            connection.execute(text("CREATE INDEX idx_questions_type ON questions(type);"))
            connection.execute(text("CREATE INDEX idx_questions_order ON questions(order_num);"))
            
        else:
            print("Questions table already exists.")
            
        # 检查并创建学生答题表
        if not check_table_exists(connection, 'student_answers'):
            print("Creating student_answers table...")
            create_student_answers_table = """
            CREATE TABLE IF NOT EXISTS student_answers (
                id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL PRIMARY KEY,
                student_id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '学生ID',
                assignment_id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '作业ID',
                question_id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '题目ID',
                answer JSON COMMENT '学生答案（JSON格式）',
                is_correct BOOLEAN DEFAULT NULL COMMENT '是否答对（可自动校验或教师手动标记）',
                score FLOAT DEFAULT NULL COMMENT '得分',
                submit_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间',
                update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id),
                FOREIGN KEY (assignment_id) REFERENCES assignments(id),
                FOREIGN KEY (question_id) REFERENCES questions(id),
                UNIQUE KEY uk_student_question (student_id, assignment_id, question_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
            """
            connection.execute(text(create_student_answers_table))
            
            # 创建索引
            print("Creating indexes for student_answers table...")
            connection.execute(text("CREATE INDEX idx_student_answers_student ON student_answers(student_id);"))
            connection.execute(text("CREATE INDEX idx_student_answers_assignment ON student_answers(assignment_id);"))
            connection.execute(text("CREATE INDEX idx_student_answers_question ON student_answers(question_id);"))
            
        else:
            print("Student answers table already exists.")
            
        connection.commit()
        print("Migration completed successfully!")

def drop_tables():
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    with engine.connect() as connection:
        if check_table_exists(connection, 'student_answers'):
            print("Dropping student_answers table...")
            connection.execute(text("DROP TABLE student_answers;"))
            
        if check_table_exists(connection, 'questions'):
            print("Dropping questions table...")
            connection.execute(text("DROP TABLE questions;"))
            
        if check_table_exists(connection, 'assignments'):
            print("Dropping assignments table...")
            connection.execute(text("DROP TABLE assignments;"))
            
        connection.commit()
        print("Tables dropped successfully!")

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--drop':
        drop_tables()
    else:
        create_tables() 