#!/usr/bin/env python3
"""
简化版Question表category字段迁移到course_id字段的脚本
此脚本仅生成SQL语句，不直接执行数据库操作
"""

def generate_migration_sql():
    """生成迁移SQL语句"""
    sql_statements = [
        "-- 迁移Question表的category字段为course_id字段",
        "-- 执行前请备份数据库！",
        "",
        "-- 1. 添加course_id字段（临时允许NULL）",
        "ALTER TABLE questions",
        "ADD COLUMN course_id CHAR(36) NULL",
        "COMMENT '所属课程ID';",
        "",
        "-- 2. 将category字段的数据复制到course_id字段",
        "UPDATE questions",
        "SET course_id = category",
        "WHERE category IS NOT NULL AND category != '';",
        "",
        "-- 3. 检查是否有空的course_id记录",
        "SELECT COUNT(*) as empty_count",
        "FROM questions",
        "WHERE course_id IS NULL OR course_id = '';",
        "",
        "-- 4. 如果有空记录，需要处理（二选一）",
        "-- 选项A: 设置默认值（需要替换为实际存在的课程ID）",
        "-- UPDATE questions",
        "-- SET course_id = 'your-default-course-id'",
        "-- WHERE course_id IS NULL OR course_id = '';",
        "",
        "-- 选项B: 删除空记录（谨慎使用）",
        "-- DELETE FROM questions WHERE course_id IS NULL OR course_id = '';",
        "",
        "-- 5. 将course_id字段设置为NOT NULL",
        "ALTER TABLE questions",
        "MODIFY COLUMN course_id CHAR(36) NOT NULL",
        "COMMENT '所属课程ID';",
        "",
        "-- 6. 添加外键约束",
        "ALTER TABLE questions",
        "ADD CONSTRAINT fk_questions_course_id",
        "FOREIGN KEY (course_id) REFERENCES courses(id)",
        "ON DELETE CASCADE ON UPDATE CASCADE;",
        "",
        "-- 7. 删除原来的category字段",
        "ALTER TABLE questions",
        "DROP COLUMN category;",
        "",
        "-- 验证迁移结果",
        "SELECT",
        "    COUNT(*) as total_questions,",
        "    COUNT(DISTINCT course_id) as unique_courses",
        "FROM questions;",
        "",
        "-- 检查外键约束是否正确创建",
        "SHOW CREATE TABLE questions;"
    ]
    
    return "\n".join(sql_statements)

def main():
    """主函数"""
    print("Question表category字段迁移到course_id字段")
    print("="*50)
    print()
    print("由于环境限制，此脚本生成SQL语句供手动执行。")
    print("请将以下SQL语句保存到文件中，并在数据库中手动执行：")
    print()
    print("="*50)
    print(generate_migration_sql())
    print("="*50)
    print()
    print("注意事项：")
    print("1. 执行前请备份数据库")
    print("2. 如果有course_id为空的记录，请先处理这些记录")
    print("3. 确保所有category值都对应有效的课程ID")
    print("4. 建议在测试环境先执行验证")
    
    # 将SQL保存到文件
    sql_file = "migrate_question_category_to_course_id.sql"
    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write(generate_migration_sql())
    
    print(f"\nSQL语句已保存到文件: {sql_file}")

if __name__ == "__main__":
    main()