#!/usr/bin/env python3
"""
Migration script to make knowledge_bases.group_id nullable

This script allows knowledge bases to exist without belonging to a group.
"""
import os
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate():
    """Execute the migration"""
    engine = create_engine(settings.DATABASE_URL)

    print("="*60)
    print("Migration: Make knowledge_bases.group_id nullable")
    print("="*60)

    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()

        try:
            # 1. Check current state
            print("\n1. Checking current state...")
            result = conn.execute(text("""
                SELECT
                    COUNT(*) as total_bases,
                    SUM(CASE WHEN group_id IS NULL THEN 1 ELSE 0 END) as null_group_bases
                FROM knowledge_bases
            """))
            row = result.fetchone()
            print(f"   Total knowledge bases: {row[0]}")
            print(f"   Bases with NULL group_id: {row[1]}")

            # 2. Create default groups for users who don't have one
            print("\n2. Creating default groups for users...")
            result = conn.execute(text("""
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
                ) AS distinct_users
            """))
            print(f"   Created or skipped default groups")

            # 3. Drop foreign key constraint
            print("\n3. Dropping foreign key constraint...")
            try:
                conn.execute(text("ALTER TABLE knowledge_bases DROP FOREIGN KEY knowledge_bases_ibfk_2"))
                print("   Foreign key dropped")
            except Exception as e:
                print(f"   Warning: {e}")
                print("   (Foreign key may not exist or already dropped)")

            # 4. Make column nullable
            print("\n4. Making group_id nullable...")
            conn.execute(text("ALTER TABLE knowledge_bases MODIFY COLUMN group_id VARCHAR(36) NULL"))
            print("   Column is now nullable")

            # 5. Re-add foreign key constraint
            print("\n5. Re-adding foreign key constraint...")
            conn.execute(text("""
                ALTER TABLE knowledge_bases
                ADD CONSTRAINT knowledge_bases_ibfk_2
                FOREIGN KEY (group_id) REFERENCES knowledge_groups(id)
                ON DELETE SET NULL
                ON UPDATE CASCADE
            """))
            print("   Foreign key re-added with ON DELETE SET NULL")

            # 6. Create indexes for performance
            print("\n6. Creating indexes...")
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_knowledge_bases_user_id_name
                    ON knowledge_bases(user_id, name)
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_knowledge_bases_group_id
                    ON knowledge_bases(group_id)
                """))
                print("   Indexes created")
            except Exception as e:
                print(f"   Warning: {e}")

            # Commit transaction
            trans.commit()
            print("\n" + "="*60)
            print("✅ Migration completed successfully!")
            print("="*60)

            # Verify migration
            print("\n7. Verifying migration...")
            result = conn.execute(text("""
                SELECT
                    COUNT(*) as total_bases,
                    SUM(CASE WHEN group_id IS NULL THEN 1 ELSE 0 END) as ungrouped_bases
                FROM knowledge_bases
            """))
            row = result.fetchone()
            print(f"   Total knowledge bases: {row[0]}")
            print(f"   Ungrouped bases (NULL group_id): {row[1]}")

        except Exception as e:
            # Rollback on error
            trans.rollback()
            print(f"\n❌ Migration failed: {e}")
            print("Transaction rolled back")
            sys.exit(1)

if __name__ == "__main__":
    migrate()
