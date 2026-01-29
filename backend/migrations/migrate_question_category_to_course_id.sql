-- 迁移Question表的category字段为course_id字段
-- 执行前请备份数据库！

-- 1. 添加course_id字段（临时允许NULL）
ALTER TABLE questions 
ADD COLUMN course_id CHAR(36) NULL 
COMMENT '所属课程ID';

-- 2. 将category字段的数据复制到course_id字段
UPDATE questions 
SET course_id = category 
WHERE category IS NOT NULL AND category != '';

-- 3. 检查是否有空的course_id记录
SELECT COUNT(*) as empty_count 
FROM questions 
WHERE course_id IS NULL OR course_id = '';

-- 4. 如果有空记录，可以设置默认值或删除这些记录
-- 选项A: 设置默认值（需要替换为实际存在的课程ID）
-- UPDATE questions 
-- SET course_id = 'your-default-course-id' 
-- WHERE course_id IS NULL OR course_id = '';

-- 选项B: 删除空记录（谨慎使用）
-- DELETE FROM questions WHERE course_id IS NULL OR course_id = '';

-- 5. 将course_id字段设置为NOT NULL
ALTER TABLE questions 
MODIFY COLUMN course_id CHAR(36) NOT NULL 
COMMENT '所属课程ID';

-- 6. 添加外键约束
ALTER TABLE questions 
ADD CONSTRAINT fk_questions_course_id 
FOREIGN KEY (course_id) REFERENCES courses(id) 
ON DELETE CASCADE ON UPDATE CASCADE;

-- 7. 删除原来的category字段
ALTER TABLE questions 
DROP COLUMN category;

-- 验证迁移结果
SELECT 
    COUNT(*) as total_questions,
    COUNT(DISTINCT course_id) as unique_courses
FROM questions;

-- 检查外键约束是否正确创建
SHOW CREATE TABLE questions;