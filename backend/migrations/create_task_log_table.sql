-- 创建任务日志表
CREATE TABLE IF NOT EXISTS task_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(50),
    video_id CHAR(36),
    log_level VARCHAR(20),
    message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 创建索引提高查询性能
    INDEX idx_task_logs_task_id (task_id),
    INDEX idx_task_logs_video_id (video_id),
    INDEX idx_task_logs_timestamp (timestamp),
    INDEX idx_task_logs_log_level (log_level),
    
    -- 添加外键约束
    CONSTRAINT fk_task_logs_video FOREIGN KEY (video_id)
        REFERENCES videos(id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 添加查询权限
GRANT SELECT, INSERT, UPDATE, DELETE ON task_logs TO 'app_user'@'%';

-- 添加注释
ALTER TABLE task_logs 
    COMMENT '视频处理任务日志表';
ALTER TABLE task_logs MODIFY COLUMN id INT AUTO_INCREMENT COMMENT '日志ID';
ALTER TABLE task_logs MODIFY COLUMN task_id VARCHAR(50) COMMENT '任务ID';
ALTER TABLE task_logs MODIFY COLUMN video_id CHAR(36) COMMENT '关联视频ID';
ALTER TABLE task_logs MODIFY COLUMN log_level VARCHAR(20) COMMENT '日志级别(info,warning,error)';
ALTER TABLE task_logs MODIFY COLUMN message TEXT COMMENT '日志消息内容';
ALTER TABLE task_logs MODIFY COLUMN timestamp DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '日志记录时间';
