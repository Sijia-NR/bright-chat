-- 修复 file_type 列长度
-- 执行日期: 2026-01-29
-- 问题: application/vnd.openxmlformats-officedocument.wordprocessingml.document 等 MIME 类型超过 50 字符

USE bright_chat;

-- 修改 file_type 列为 VARCHAR(255)
ALTER TABLE documents MODIFY COLUMN file_type VARCHAR(255) NOT NULL;

-- 验证修改
DESCRIBE documents;

SELECT '✅ file_type 列已修改为 VARCHAR(255)' AS status;
