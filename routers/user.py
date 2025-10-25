from datetime import datetime, timezone
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from config import database
from entity.auth import RefreshToken
from model.user import SessionInfo, UserResponse
from services.auth import AuthService
from starlette import status

router = APIRouter()

# OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
Oauth2Dep = Annotated[str, Depends(oauth2_scheme)]

SessionDep = Annotated[Session, Depends(database.get_db_session)]

AuthDep = Annotated[AuthService, Depends()]

@router.get("/users/me", response_model=UserResponse)
async def read_users_me(
    token: Oauth2Dep,
    session: SessionDep,
    auth: AuthDep
):
    """
    Get current authenticated user information
    """
    # Get current user from token
    current_user = await auth.get_current_user(token, session)
    return current_user

@router.put("/users/me", response_model=UserResponse)
async def update_user(
    token: Oauth2Dep,
    session: SessionDep,
    auth: AuthDep,
    full_name: Optional[str] = None
    
):
    """
    Update current user information
    """
    # Get current user from token
    current_user = await auth.get_current_user(token, session)
    
    if full_name is not None:
        current_user.full_name = full_name
    
    current_user.updated_at = datetime.now(timezone.utc)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return current_user

@router.delete("/users/me")
async def delete_user(
    token: Oauth2Dep,
    session: SessionDep,
    auth: AuthDep,
):
    """
    Deactivate current user account
    """
    # Get current user from token
    current_user = await auth.get_current_user(token, session)
    
    current_user.is_active = False
    current_user.updated_at = datetime.now(timezone.utc)
    session.add(current_user)
    session.commit()
    
    return {"message": "User account deactivated"}

# ============================================================================
# SESSION MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/users/me/sessions", response_model=list[SessionInfo])
async def get_active_sessions(
    token: Oauth2Dep,
    session: SessionDep,
    auth: AuthDep,
):
    """
    Get all active sessions for current user
    """
    # Get current user from token
    current_user = await auth.get_current_user(token, session)
    
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

@router.delete("/users/me/sessions/{session_id}")
async def revoke_session(
    session_id: int,
    token: Oauth2Dep,
    session: SessionDep,
    auth: AuthDep,
):
    """
    Revoke a specific session (logout from that device)
    """
    # Get current user from token
    current_user = await auth.get_current_user(token, session)
    
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

@router.delete("/users/me/sessions")
async def revoke_all_sessions(
    token: Oauth2Dep,
    session: SessionDep,
    auth: AuthDep,
):
    """
    Revoke all sessions except current one (logout from all devices)
    """
    # Get current user from token
    current_user = await auth.get_current_user(token, session)
    
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