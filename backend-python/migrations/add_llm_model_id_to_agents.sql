-- 添加 llm_model_id 字段到 agents 表
-- 用于 Agent 指定特定的 LLM 模型
-- 创建时间: 2026-01-25

-- 添加 llm_model_id 字段
ALTER TABLE `agents`
ADD COLUMN `llm_model_id` VARCHAR(36) NULL AFTER `config`,
ADD INDEX `idx_llm_model_id` (`llm_model_id`),
ADD CONSTRAINT `fk_agents_llm_model`
    FOREIGN KEY (`llm_model_id`)
    REFERENCES `llm_models`(`id`)
    ON DELETE SET NULL
    ON UPDATE CASCADE;

-- 为现有 Agent 设置默认模型（可选，或保持 NULL 向后兼容）
-- 如果需要为现有 Agent 设置默认模型，请取消下面的注释
-- UPDATE `agents` SET `llm_model_id` = (
--     SELECT id FROM `llm_models` WHERE `is_active` = TRUE ORDER BY `created_at` ASC LIMIT 1
-- ) WHERE `llm_model_id` IS NULL;
