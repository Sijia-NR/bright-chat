from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ...models.session import (
    SessionCreate,
    SessionResponse,
    SessionListResponse,
    MessageCreate,
    MessageResponse,
    MessagesResponse,
    Message
)
from ...models.favorite import MessageFavorite
from ...core.database import get_db
from ...services.auth import auth_service
from ..middleware import setup_middleware

router = APIRouter(prefix="/sessions", tags=["Session Management"])


@router.get("/", response_model=SessionListResponse)
async def get_sessions(
    user_id: str = Query(..., description="User ID"),
    db: Session = Depends(get_db)
):
    """Get all sessions for a user."""
    from ...models.session import Session

    sessions = db.query(Session).filter(Session.user_id == user_id).all()
    return SessionListResponse(
        sessions=[SessionResponse.from_orm(session) for session in sessions]
    )


@router.post("/", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db)
):
    """Create a new session."""
    from ...models.session import Session

    try:
        # Create session
        db_session = Session(
            title=session_data.title,
            user_id=session_data.user_id
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)

        return SessionResponse.from_orm(db_session)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )


@router.get("/{session_id}/messages", response_model=MessagesResponse)
async def get_session_messages(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get messages for a specific session."""
    messages = db.query(Message).filter(Message.session_id == session_id).all()

    return MessagesResponse(
        messages=[MessageResponse.from_orm(message) for message in messages]
    )


@router.post("/{session_id}/messages")
async def save_messages(
    session_id: str,
    message_data: MessageCreate,
    db: Session = Depends(get_db)
):
    """Save messages to a session."""
    try:
        # Validate session exists
        from ...models.session import Session
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        # Save messages
        for msg in message_data.messages:
            db_message = Message(
                session_id=session_id,
                role=msg['role'],
                content=msg['content'],
                timestamp=msg['timestamp']
            )
            db.add(db_message)

        db.commit()

        return {"message": "Messages saved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save messages"
        )


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Delete a session and all its messages."""
    try:
        from ...models.session import Session, Message

        # 获取会话的所有消息 ID
        messages = db.query(Message).filter(Message.session_id == session_id).all()
        message_ids = [msg.id for msg in messages]

        # 先删除这些消息的收藏记录（由于外键约束）
        if message_ids:
            db.query(MessageFavorite).filter(MessageFavorite.message_id.in_(message_ids)).delete(synchronize_session=False)

        # 删除所有消息
        db.query(Message).filter(Message.session_id == session_id).delete()

        # 删除会话
        session = db.query(Session).filter(Session.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        db.delete(session)
        db.commit()

        return {"message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )