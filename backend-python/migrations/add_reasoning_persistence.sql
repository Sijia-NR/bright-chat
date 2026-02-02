-- Agent 思维链持久化迁移脚本
-- 添加 reasoning_steps 和 message_id 字段到 agent_executions 表
-- Migration Date: 2026-01-31

-- 1. 添加 message_id 字段（精确关联消息）
ALTER TABLE agent_executions
ADD COLUMN message_id VARCHAR(36) NULL
COMMENT '关联的消息ID（messages.id）'
AFTER session_id;

-- 2. 添加外键约束（可选，如果不希望强制关联可以不加）
-- ALTER TABLE agent_executions
-- ADD CONSTRAINT fk_agent_executions_message
-- FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE SET NULL;

-- 3. 添加 reasoning_steps 字段
ALTER TABLE agent_executions
ADD COLUMN reasoning_steps LONGTEXT NULL
COMMENT 'Agent 推理步骤数组（JSON格式）'
AFTER execution_log;

-- 4. 添加索引（优化查询性能）
CREATE INDEX idx_agent_executions_message_id
ON agent_executions(message_id);

-- 5. 验证迁移结果
DESCRIBE agent_executions;

-- 6. 验证索引
SHOW INDEX FROM agent_executions WHERE Key_name = 'idx_agent_executions_message_id';
