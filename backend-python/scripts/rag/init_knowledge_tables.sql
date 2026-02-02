-- BrightChat 知识库和数字员工功能 - 数据库初始化脚本
-- Knowledge Base and Digital Employee Feature - Database Initialization Script
--
-- 说明: 此脚本创建知识库和Agent功能所需的数据表
-- Usage: mysql -u bright_chat -p bright_chat < init_knowledge_tables.sql

-- ============================================
-- 1. 知识库分组表
-- ============================================
CREATE TABLE IF NOT EXISTS `knowledge_groups` (
    `id` VARCHAR(36) PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `description` TEXT,
    `user_id` VARCHAR(36) NOT NULL,
    `color` VARCHAR(20) DEFAULT '#3B82F6',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    INDEX `idx_kg_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 2. 知识库表
-- ============================================
CREATE TABLE IF NOT EXISTS `knowledge_bases` (
    `id` VARCHAR(36) PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `description` TEXT,
    `user_id` VARCHAR(36) NOT NULL,
    `group_id` VARCHAR(36),
    `embedding_model` VARCHAR(100) DEFAULT 'bge-large-zh-v1.5',
    `chunk_size` INT DEFAULT 500,
    `chunk_overlap` INT DEFAULT 50,
    `is_active` BOOLEAN DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`group_id`) REFERENCES `knowledge_groups`(`id`) ON DELETE SET NULL,
    INDEX `idx_kb_user` (`user_id`),
    INDEX `idx_kb_group` (`group_id`),
    INDEX `idx_kb_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 3. 知识库文档表
-- ============================================
CREATE TABLE IF NOT EXISTS `documents` (
    `id` VARCHAR(36) PRIMARY KEY,
    `knowledge_base_id` VARCHAR(36) NOT NULL,
    `filename` VARCHAR(255) NOT NULL,
    `file_type` VARCHAR(50),
    `file_size` INT,
    `chunk_count` INT DEFAULT 0,
    `upload_status` VARCHAR(50) DEFAULT 'processing',
    `error_message` TEXT,
    `uploaded_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `processed_at` DATETIME,
    FOREIGN KEY (`knowledge_base_id`) REFERENCES `knowledge_bases`(`id`) ON DELETE CASCADE,
    INDEX `idx_doc_kb` (`knowledge_base_id`),
    INDEX `idx_doc_status` (`upload_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 4. Agent 配置表
-- ============================================
CREATE TABLE IF NOT EXISTS `agents` (
    `id` VARCHAR(36) PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `display_name` VARCHAR(255),
    `description` TEXT,
    `agent_type` VARCHAR(50) NOT NULL,
    `system_prompt` TEXT,
    `knowledge_base_ids` JSON,
    `tools` JSON,
    `config` JSON,
    `is_active` BOOLEAN DEFAULT TRUE,
    `created_by` VARCHAR(36),
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (`created_by`) REFERENCES `users`(`id`) ON DELETE SET NULL,
    INDEX `idx_agent_type` (`agent_type`),
    INDEX `idx_agent_active` (`is_active`),
    INDEX `idx_agent_creator` (`created_by`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 5. Agent 执行记录表
-- ============================================
CREATE TABLE IF NOT EXISTS `agent_executions` (
    `id` VARCHAR(36) PRIMARY KEY,
    `agent_id` VARCHAR(36) NOT NULL,
    `user_id` VARCHAR(36) NOT NULL,
    `session_id` VARCHAR(36),
    `input_prompt` TEXT NOT NULL,
    `status` VARCHAR(50) DEFAULT 'running',
    `steps` INT DEFAULT 0,
    `result` TEXT,
    `error_message` TEXT,
    `execution_log` JSON,
    `started_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `completed_at` DATETIME,
    FOREIGN KEY (`agent_id`) REFERENCES `agents`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`session_id`) REFERENCES `sessions`(`id`) ON DELETE SET NULL,
    INDEX `idx_exec_agent` (`agent_id`),
    INDEX `idx_exec_user` (`user_id`),
    INDEX `idx_exec_session` (`session_id`),
    INDEX `idx_exec_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- 6. 插入示例数据（可选）
-- ============================================

-- 插入默认 Agent 模板（可选，用于测试）
INSERT IGNORE INTO `agents` (
    `id`, `name`, `display_name`, `description`, `agent_type`,
    `system_prompt`, `tools`, `config`, `is_active`, `created_by`
) VALUES
(
    UUID(),
    'general_assistant',
    '通用助手',
    '能够回答各种问题、执行计算、搜索信息的通用AI助手',
    'tool',
    '你是一个有用的AI助手。你可以使用各种工具来帮助用户解决问题。在回答问题时，要简洁、准确、友好。',
    '["calculator", "datetime", "knowledge_search"]',
    '{"temperature": 0.7, "max_steps": 10}',
    TRUE,
    (SELECT `id` FROM `users` WHERE `username` = 'admin' LIMIT 1)
);

-- ============================================
-- 7. 验证表创建
-- ============================================
-- 检查所有表是否创建成功
SELECT
    TABLE_NAME,
    TABLE_ROWS,
    CREATE_TIME
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME IN ('knowledge_groups', 'knowledge_bases', 'documents', 'agents', 'agent_executions')
ORDER BY TABLE_NAME;

-- 完成提示
SELECT '知识库和Agent功能数据库初始化完成!' AS Status;
