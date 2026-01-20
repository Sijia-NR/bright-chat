#!/usr/bin/env python3
import os
import sys
import logging

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test database connection."""
    try:
        # Import here to avoid import issues
        from sqlalchemy import create_engine
        from sqlalchemy.exc import OperationalError

        # Create database URL
        db_url = "mysql+pymysql://root:123456@47.116.218.206:13306/test_db"

        logger.info("Testing database connection...")
        logger.info(f"Database URL: mysql+pymysql://root:***@47.116.218.206:13306/test_db")

        # Create engine
        engine = create_engine(db_url, pool_pre_ping=True)

        # Test connection
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
            logger.info("Database connection successful!")

        # Test database creation
        logger.info("Creating bright_chat database...")
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("CREATE DATABASE IF NOT EXISTS bright_chat CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            conn.commit()
            logger.info("Database created successfully!")

        return True

    except OperationalError as e:
        logger.error(f"Database connection failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = test_database_connection()
    if success:
        print("✅ Database setup successful!")
    else:
        print("❌ Database setup failed!")
        sys.exit(1)