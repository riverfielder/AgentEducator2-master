 SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ========================================
-- 1. 扩展现有表
-- ========================================

-- 注意：以下字段已在模型中定义，如果数据库中不存在则取消注释
-- 扩展 documents 表，增加处理状态字段（如果不存在）
-- ALTER TABLE `documents` 
-- ADD COLUMN `processing_status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT 'unprocessed' COMMENT '处理状态: unprocessed/processing/completed/failed',
-- ADD COLUMN `markitdown_content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci COMMENT 'Markitdown转换后的markdown内容';

-- 扩展 task_logs 表，支持文档处理日志（如果不存在）
-- ALTER TABLE `task_logs` 
-- ADD COLUMN `document_id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '关联文档ID',
-- ADD INDEX `ix_task_logs_document_id` (`document_id`),
-- ADD CONSTRAINT `task_logs_document_fk` FOREIGN KEY (`document_id`) REFERENCES `documents` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

-- 扩展 chat_sessions 表，支持基于文档的聊天（如果不存在）
-- ALTER TABLE `chat_sessions` 
-- ADD COLUMN `document_id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '关联文档ID',
-- ADD INDEX `ix_chat_sessions_document_id` (`document_id`),
-- ADD CONSTRAINT `chat_sessions_document_fk` FOREIGN KEY (`document_id`) REFERENCES `documents` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

-- ========================================
-- 2. 新增核心表
-- ========================================

-- 文档处理任务表
DROP TABLE IF EXISTS `document_processing_tasks`;
CREATE TABLE `document_processing_tasks` (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `document_id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `task_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '任务状态: pending/running/completed/failed',
  `processing_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '处理类型: markitdown/segmentation/vectorization/summary',
  `progress` float DEFAULT NULL COMMENT '处理进度 0.0-1.0',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '错误信息',
  `start_time` datetime NOT NULL COMMENT '开始时间',
  `end_time` datetime DEFAULT NULL COMMENT '结束时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_doc_processing_tasks_document_id` (`document_id` ASC) USING BTREE,
  INDEX `idx_doc_processing_tasks_status` (`status` ASC) USING BTREE,
  INDEX `idx_doc_processing_tasks_type` (`processing_type` ASC) USING BTREE,
  CONSTRAINT `doc_processing_tasks_document_fk` FOREIGN KEY (`document_id`) REFERENCES `documents` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '文档处理任务表' ROW_FORMAT = Dynamic;

-- 文档段落表
DROP TABLE IF EXISTS `document_segments`;
CREATE TABLE `document_segments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `document_id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `segment_number` int NOT NULL COMMENT '段落序号',
  `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '段落标题',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'Markitdown转换后的内容',
  `page_number` int DEFAULT NULL COMMENT '页码（如果适用）',
  `segment_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '段落类型: paragraph/table/list/heading等',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_doc_segments_document_id` (`document_id` ASC) USING BTREE,
  INDEX `idx_doc_segments_number` (`document_id` ASC, `segment_number` ASC) USING BTREE,
  INDEX `idx_doc_segments_type` (`segment_type` ASC) USING BTREE,
  CONSTRAINT `doc_segments_document_fk` FOREIGN KEY (`document_id`) REFERENCES `documents` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '文档段落表' ROW_FORMAT = Dynamic;

-- 文档向量索引表
DROP TABLE IF EXISTS `document_vector_indices`;
CREATE TABLE `document_vector_indices` (
  `id` int NOT NULL AUTO_INCREMENT,
  `document_id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `index_path` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '向量索引文件路径',
  `embedding_model` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '嵌入模型名称',
  `total_vectors` int DEFAULT NULL COMMENT '向量总数',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_doc_vector_indices_document_id` (`document_id` ASC) USING BTREE,
  CONSTRAINT `doc_vector_indices_document_fk` FOREIGN KEY (`document_id`) REFERENCES `documents` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '文档向量索引表' ROW_FORMAT = Dynamic;

-- 文档摘要表
DROP TABLE IF EXISTS `document_summaries`;
CREATE TABLE `document_summaries` (
  `id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `document_id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `main_points` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '主要要点',
  `keywords` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '知识点列表',
  `sections` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '章节摘要',
  `whole_summary` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '整体摘要',
  `generate_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uq_doc_summary_document_id` (`document_id` ASC) USING BTREE,
  CONSTRAINT `doc_summaries_document_fk` FOREIGN KEY (`document_id`) REFERENCES `documents` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '文档摘要表' ROW_FORMAT = Dynamic;

-- 文档知识点关联表
DROP TABLE IF EXISTS `document_keywords`;
CREATE TABLE `document_keywords` (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `document_id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `keyword_id` char(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `weight` float DEFAULT NULL COMMENT '知识点权重',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uq_document_keyword` (`document_id` ASC, `keyword_id` ASC) USING BTREE,
  INDEX `idx_doc_keywords_keyword_id` (`keyword_id` ASC) USING BTREE,
  INDEX `idx_doc_keywords_weight` (`weight` DESC) USING BTREE,
  CONSTRAINT `doc_keywords_document_fk` FOREIGN KEY (`document_id`) REFERENCES `documents` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `doc_keywords_keyword_fk` FOREIGN KEY (`keyword_id`) REFERENCES `keywords` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '文档知识点关联表' ROW_FORMAT = Dynamic;

-- ========================================
-- 3. 索引优化
-- ========================================

-- 为现有表添加复合索引
CREATE INDEX `idx_documents_processing_status` ON `documents` (`processing_status`, `course_id`);
CREATE INDEX `idx_documents_chapter_processing` ON `documents` (`chapter_id`, `processing_status`);

SET FOREIGN_KEY_CHECKS = 1;