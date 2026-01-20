#!/usr/bin/env python3
"""
Database initialization script for Bright-Chat API
"""
import os
import sys
import logging
from typing import Dict, Any

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import core modules directly
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app'))
from core.database import init_db, drop_db, check_db_connection
from core.config import settings
from core.security import get_password_hash
from services.auth import auth_service
from sqlalchemy.orm import Session
from models.user import User, UserRole

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_admin_user(db: Session) -> User:
    """Create admin user if it doesn't exist."""
    admin_user = db.query(User).filter(User.username == "admin").first()
    if admin_user:
        logger.info("Admin user already exists")
        return admin_user

    logger.info("Creating admin user...")
    admin_user = User(
        username="admin",
        password_hash=get_password_hash("admin123"),
        role=UserRole.ADMIN
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    logger.info(f"Admin user created successfully: {admin_user.username}")
    return admin_user


def create_sample_users(db: Session) -> None:
    """Create sample users for testing."""
    # Check if sample users already exist
    existing_users = db.query(User).filter(User.username.in_(["testuser1", "testuser2"])).all()
    if existing_users:
        logger.info("Sample users already exist")
        return

    logger.info("Creating sample users...")
    sample_users = [
        User(
            username="testuser1",
            password_hash=get_password_hash("password123"),
            role=UserRole.USER
        ),
        User(
            username="testuser2",
            password_hash=get_password_hash("password123"),
            role=UserRole.USER
        )
    ]

    for user in sample_users:
        db.add(user)

    db.commit()
    logger.info("Sample users created successfully")


def check_database_connection() -> bool:
    """Check database connection."""
    logger.info("Checking database connection...")
    if not check_db_connection():
        logger.error("Failed to connect to database")
        return False
    logger.info("Database connection successful")
    return True


# Import SessionLocal after adding path
from sqlalchemy.orm import sessionmaker

# Create sessionmaker
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=None
)

def main():
    """Main function to initialize database."""
    logger.info("Starting database initialization...")

    # Check database connection
    if not check_database_connection():
        logger.error("Database connection failed. Please check your database settings.")
        sys.exit(1)

    # Create tables
    logger.info("Creating database tables...")
    init_db()
    logger.info("Database tables created successfully")

    # Create admin user
    with SessionLocal() as db:
        create_admin_user(db)
        create_sample_users(db)

    logger.info("Database initialization completed successfully!")
    logger.info("Default credentials:")
    logger.info("  Admin: admin / admin123")


def reset_database():
    """Reset database (drop all tables and recreate)."""
    logger.warning("Resetting database...")
    if not check_database_connection():
        logger.error("Database connection failed")
        sys.exit(1)

    # Drop all tables
    drop_db()
    logger.info("Database tables dropped successfully")

    # Recreate tables
    init_db()
    logger.info("Database tables recreated successfully")

    # Create admin user
    with SessionLocal() as db:
        create_admin_user(db)
        create_sample_users(db)

    logger.info("Database reset completed successfully!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database initialization script")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset database (drop all tables and recreate)"
    )

    args = parser.parse_args()

    if args.reset:
        reset_database()
    else:
        main()