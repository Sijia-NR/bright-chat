#!/usr/bin/env python3
"""
Simplified migration script to make knowledge_bases.group_id nullable
"""
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

            # 2. Drop foreign key constraint
            print("\n2. Dropping foreign key constraint...")
            try:
                # 首先查找外键约束名称
                result = conn.execute(text("""
                    SELECT CONSTRAINT_NAME
                    FROM information_schema.KEY_COLUMN_USAGE
                    WHERE TABLE_NAME = 'knowledge_bases'
                    AND COLUMN_NAME = 'group_id'
                    AND REFERENCED_TABLE_NAME IS NOT NULL
                """))
                fk_name = result.fetchone()
                if fk_name:
                    conn.execute(text(f"ALTER TABLE knowledge_bases DROP FOREIGN KEY {fk_name[0]}"))
                    print(f"   Foreign key '{fk_name[0]}' dropped")
                else:
                    print("   No foreign key found on group_id")
            except Exception as e:
                print(f"   Warning: {e}")

            # 3. Make column nullable
            print("\n3. Making group_id nullable...")
            conn.execute(text("ALTER TABLE knowledge_bases MODIFY COLUMN group_id VARCHAR(36) NULL"))
            print("   Column is now nullable")

            # 4. Re-add foreign key constraint
            print("\n4. Re-adding foreign key constraint...")
            conn.execute(text("""
                ALTER TABLE knowledge_bases
                ADD CONSTRAINT fk_knowledge_bases_group_id
                FOREIGN KEY (group_id) REFERENCES knowledge_groups(id)
                ON DELETE SET NULL
                ON UPDATE CASCADE
            """))
            print("   Foreign key re-added with ON DELETE SET NULL")

            # 5. Create indexes for performance
            print("\n5. Creating indexes...")
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
            print("\n6. Verifying migration...")
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
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    migrate()
