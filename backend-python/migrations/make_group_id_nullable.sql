-- Migration: Make knowledge_bases.group_id nullable
-- Date: 2026-01-29
-- Description: Allow knowledge bases to exist without a group

-- 1. 首先为所有没有分组的知识库创建一个"默认分组"
INSERT IGNORE INTO knowledge_groups (id, user_id, name, description, `order`, created_at, updated_at)
SELECT
    CONCAT('default-group-', user_id) as id,
    user_id,
    '默认分组',
    '系统自动创建的默认分组',
    999,
    NOW(),
    NOW()
FROM (
    SELECT DISTINCT user_id
    FROM knowledge_bases
    WHERE group_id IS NOT NULL
) AS distinct_users;

-- 2. 将 orphan 知识库（引用不存在分组的）分配到默认分组
-- 注意：由于外键约束，这一步可能不需要，但保留作为安全措施
-- UPDATE knowledge_bases kb
-- LEFT JOIN knowledge_groups kg ON kb.group_id = kg.id
-- SET kb.group_id = CONCAT('default-group-', kb.user_id)
-- WHERE kb.id IS NOT NULL AND kb.group_id IS NOT NULL AND kg.id IS NULL;

-- 3. 删除外键约束
ALTER TABLE knowledge_bases DROP FOREIGN KEY knowledge_bases_ibfk_2;

-- 4. 修改 group_id 为可空
ALTER TABLE knowledge_bases MODIFY COLUMN group_id VARCHAR(36) NULL;

-- 5. 重新添加外键约束（允许 NULL）
ALTER TABLE knowledge_bases
ADD CONSTRAINT knowledge_bases_ibfk_2
FOREIGN KEY (group_id) REFERENCES knowledge_groups(id)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- 6. 添加索引以提升查询性能
CREATE INDEX ix_knowledge_bases_user_id_name ON knowledge_bases(user_id, name);
CREATE INDEX ix_knowledge_bases_group_id ON knowledge_bases(group_id);

-- 验证
SELECT
    'Migration completed' as status,
    COUNT(*) as total_bases,
    SUM(CASE WHEN group_id IS NULL THEN 1 ELSE 0 END) as ungrouped_bases
FROM knowledge_bases;
