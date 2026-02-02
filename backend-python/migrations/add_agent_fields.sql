-- 添加 order 和 enable_knowledge 字段到 agents 表
-- 用于 Agent 排序和知识库开关控制
-- 创建时间: 2026-01-29

-- 检查并添加 enable_knowledge 字段
ALTER TABLE `agents`
ADD COLUMN IF NOT EXISTS `enable_knowledge` BOOLEAN NULL DEFAULT TRUE
COMMENT '是否启用知识库功能'
AFTER `llm_model_id`;

-- 检查并添加 order 字段
ALTER TABLE `agents`
ADD COLUMN IF NOT EXISTS `order` INT NULL DEFAULT 0
COMMENT 'Agent 显示顺序（数字越小越靠前）'
AFTER `enable_knowledge`;

-- 添加索引以加快排序查询
CREATE INDEX IF NOT EXISTS `idx_agents_order` ON `agents`(`order`);
CREATE INDEX IF NOT EXISTS `idx_agents_enable_knowledge` ON `agents`(`enable_knowledge`);

-- 更新现有数据的默认值
UPDATE `agents` SET `order` = 0 WHERE `order` IS NULL;
UPDATE `agents` SET `enable_knowledge` = TRUE WHERE `enable_knowledge` IS NULL;

-- 设置字段为 NOT NULL（在更新完默认值后）
ALTER TABLE `agents`
MODIFY COLUMN `order` INT NOT NULL DEFAULT 0,
MODIFY COLUMN `enable_knowledge` BOOLEAN NOT NULL DEFAULT TRUE;
