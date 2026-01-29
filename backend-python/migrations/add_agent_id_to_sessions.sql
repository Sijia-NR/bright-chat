-- 添加 agent_id 列到 sessions 表
-- 用于区分普通会话和数字员工会话

ALTER TABLE sessions ADD COLUMN agent_id VARCHAR(36) NULL AFTER user_id;

-- 添加索引以加快查询速度
CREATE INDEX idx_sessions_agent_id ON sessions(agent_id);

-- 添加注释
ALTER TABLE sessions MODIFY COLUMN agent_id VARCHAR(36) NULL COMMENT '关联的数字员工 ID（可选）';
