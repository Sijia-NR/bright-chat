from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from passlib.context import CryptContext

from ..models.user import User, UserCreate, UserUpdate, LoginRequest, LoginResponse
from ..core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user_id
)
from ..core.database import get_db_session
from ..core.config import settings


class AuthService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def create_user(self, db: Session, user_data: UserCreate) -> User:
        """Create new user."""
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

        # Create user
        hashed_password = get_password_hash("default_password")  # In production, force user to set password
        db_user = User(
            username=user_data.username,
            password_hash=hashed_password,
            role=user_data.role
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def get_user_by_id(self, db: Session, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()

    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get user by username."""
        return db.query(User).filter(User.username == username).first()

    def update_user(self, db: Session, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """Update user."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        # Update fields
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        db.commit()
        db.refresh(user)
        return user

    def delete_user(self, db: Session, user_id: str) -> bool:
        """Delete user."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        db.delete(user)
        db.commit()
        return True

    def get_all_users(self, db: Session) -> list[User]:
        """Get all users."""
        return db.query(User).all()

    def login(self, login_data: LoginRequest) -> LoginResponse:
        """Login user and return access token."""
        with get_db_session() as db:
            user = self.authenticate_user(db, login_data.username, login_data.password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Inactive user"
                )

            # Create access token
            access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user.id},
                expires_delta=access_token_expires
            )

            return LoginResponse(
                id=user.id,
                username=user.username,
                role=user.role.value,
                created_at=user.created_at,
                token=access_token
            )

    def logout(self, token: str) -> None:
        """Logout user (token is invalidated by JWT expiry)."""
        # In a production environment, you might want to add token blacklisting
        # For now, we just validate the token to ensure it's valid
        verify_token(token)


# Create service instance
auth_service = AuthService()


def get_current_user(token: str, db: Session) -> User:
    """Get current user from token."""
    user_id = get_current_user_id(token)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user