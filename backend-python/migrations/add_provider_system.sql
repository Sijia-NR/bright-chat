-- 数字员工提供商系统数据库迁移脚本
-- 执行前请备份数据库

-- 1. 创建 llm_providers 表
CREATE TABLE IF NOT EXISTS llm_providers (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID',
    name VARCHAR(100) UNIQUE NOT NULL COMMENT 'e.g., openai-provider',
    display_name VARCHAR(100) NOT NULL COMMENT 'e.g., OpenAI Provider',
    base_url VARCHAR(500) NOT NULL COMMENT 'e.g., https://api.openai.com',
    description TEXT COMMENT 'Optional description',
    is_active BOOLEAN DEFAULT TRUE COMMENT 'Enable/disable provider',
    auth_type VARCHAR(50) DEFAULT 'bearer' COMMENT 'bearer, api_key, none',
    default_api_key TEXT COMMENT 'Default API key for models',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR(36) COMMENT 'Creator user ID',
    INDEX idx_name (name),
    INDEX idx_is_active (is_active),
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='LLM 提供商配置表';

-- 2. 修改 llm_models 表，添加提供商关联和上架状态
-- 添加提供商关联
ALTER TABLE llm_models
ADD COLUMN IF NOT EXISTS provider_id VARCHAR(36) NULL AFTER id,
ADD INDEX IF NOT EXISTS idx_provider_id (provider_id),
ADD FOREIGN KEY (provider_id) REFERENCES llm_providers(id) ON DELETE SET NULL;

-- 添加上架状态字段（核心需求）
ALTER TABLE llm_models
ADD COLUMN IF NOT EXISTS is_listed BOOLEAN DEFAULT FALSE COMMENT '是否上架到前端（只有上架的模型对用户可见）',
ADD INDEX IF NOT EXISTS idx_is_listed (is_listed);

-- 添加同步追踪字段
ALTER TABLE llm_models
ADD COLUMN IF NOT EXISTS synced_from_provider BOOLEAN DEFAULT FALSE COMMENT 'Auto-discovered flag',
ADD COLUMN IF NOT EXISTS last_synced_at DATETIME NULL COMMENT 'Last sync timestamp',
ADD COLUMN IF NOT EXISTS external_model_id VARCHAR(200) NULL COMMENT 'Model ID in provider system';

-- 使 api_url 可空（可从提供商继承）
ALTER TABLE llm_models MODIFY api_url VARCHAR(500) NULL;
