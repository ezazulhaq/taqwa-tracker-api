from datetime import datetime, timezone
from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from config import database
from auth.entity import RefreshToken, User
from auth.model import SessionInfo, UserResponse
from auth.service import AuthService
from starlette import status

router = APIRouter(prefix="/user", tags=["User Services"])

SessionDep = Annotated[Session, Depends(database.get_db_session)]

UserDep = Annotated[User, Depends(AuthService.get_current_user)]

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: UserDep
):
    """
    Get current authenticated user information
    """
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_user(
    current_user: UserDep,
    session: SessionDep,
    full_name: Optional[str] = None
    
):
    """
    Update current user information
    """
    if full_name is not None:
        current_user.full_name = full_name
    
    current_user.updated_at = datetime.now(timezone.utc)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return current_user

@router.delete("/me")
async def delete_user(
    current_user: UserDep,
    session: SessionDep
):
    """
    Deactivate current user account
    """
    current_user.is_active = False
    current_user.updated_at = datetime.now(timezone.utc)
    session.add(current_user)
    session.commit()
    
    return {"message": "User account deactivated"}

# ============================================================================
# SESSION MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/me/sessions", response_model=list[SessionInfo])
async def get_active_sessions(
    current_user: UserDep,
    session: SessionDep
):
    """
    Get all active sessions for current user
    """
    statement = select(RefreshToken).where(
        RefreshToken.user_id == current_user.id,
        RefreshToken.revoked == False,
        RefreshToken.expires_at > datetime.now(timezone.utc)
    ).order_by(RefreshToken.created_at.desc())
    
    active_tokens = session.exec(statement).all()
    
    sessions = []
    for token_obj in active_tokens:
        sessions.append(SessionInfo(
            id=token_obj.id,
            created_at=token_obj.created_at,
            ip_address=token_obj.ip_address,
            user_agent=token_obj.user_agent
        ))
    
    return sessions

@router.delete("/me/sessions/{session_id}")
async def revoke_session(
    session_id: UUID,
    current_user: UserDep,
    session: SessionDep
):
    """
    Revoke a specific session (logout from that device)
    """    
    statement = select(RefreshToken).where(
        RefreshToken.id == session_id,
        RefreshToken.user_id == current_user.id
    )
    token_obj = session.exec(statement).first()
    
    if not token_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    token_obj.revoked = True
    session.add(token_obj)
    session.commit()
    
    return {"message": "Session revoked successfully"}

@router.delete("/me/sessions")
async def revoke_all_sessions(
    current_user: UserDep,
    session: SessionDep
):
    """
    Revoke all sessions except current one (logout from all devices)
    """    
    statement = select(RefreshToken).where(
        RefreshToken.user_id == current_user.id,
        RefreshToken.revoked == False
    )
    tokens = session.exec(statement).all()
    
    for token_obj in tokens:
        token_obj.revoked = True
        session.add(token_obj)
    
    session.commit()
    
    return {"message": f"Revoked {len(tokens)} session(s)"}