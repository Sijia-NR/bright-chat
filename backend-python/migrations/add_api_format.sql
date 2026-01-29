-- Add api_format field to llm_models table
-- This migration adds support for selecting API format (OpenAI standard or IAS custom)
-- Created: 2026-01-25

-- Backup first (run manually before executing this migration):
-- CREATE TABLE llm_models_backup_20260125 AS SELECT * FROM llm_models;

-- Add api_format column as ENUM type
ALTER TABLE llm_models
ADD COLUMN api_format ENUM('openai', 'ias')
NOT NULL
DEFAULT 'openai'
COMMENT 'API format: openai standard or ias custom'
AFTER model_type;

-- Create index for better query performance
CREATE INDEX idx_api_format ON llm_models(api_format);

-- Verify the changes
-- SELECT id, name, model_type, api_format FROM llm_models LIMIT 5;
