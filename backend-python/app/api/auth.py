from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..models.user import LoginRequest, LoginResponse
from ..services.auth import auth_service
from ..core.database import get_db
from ..core.security import create_refresh_token
from .middleware import setup_middleware

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login user and return access token."""
    try:
        response = auth_service.login(request)
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/logout")
async def logout():
    """Logout user. In a real implementation, this might invalidate the token."""
    # In production, you might want to add token blacklisting here
    return {"message": "Successfully logged out"}