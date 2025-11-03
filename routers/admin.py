from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import EmailStr
from sqlmodel import Session, select

from audit.entity import AuditLog
from audit.model import AuditLogsResponse
from auth.entity import User
from auth.model import UserAdminResponse
from auth.service import AuthService
from config.database import get_db_session

admin_dep = Depends(AuthService.get_admin_user)

router = APIRouter(
    prefix="/admin",
    tags=["Admin Services"],
    dependencies=[admin_dep]
)

SessionDep = Annotated[Session, Depends(get_db_session)]

@router.get("/audit-logs", response_model=List[AuditLogsResponse])
async def get_all_audit_logs(
    session: SessionDep,
    limit: int = 100,
    email: Optional[EmailStr] = None,
    event_type: Optional[str] = None,
):
    """
    Get all audit logs (admin only)
    """
    statement = select(AuditLog).order_by(AuditLog.created_at.desc())
    
    if email:
        statement = statement.where(AuditLog.email == email)
    if event_type:
        statement = statement.where(AuditLog.event_type == event_type)
    
    statement = statement.limit(limit)
    logs = session.exec(statement).all()
    
    return logs

@router.get("/users", response_model=List[UserAdminResponse])
async def get_all_users(
    session: SessionDep,
    skip: int = 0,
    limit: int = 50
):
    """
    Get all users (admin only)
    """
    statement = select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
    users = session.exec(statement).all()
    
    return users

@router.post("/users/{user_id}/unlock")
async def unlock_user_account(
    session: SessionDep,
    user_id: int
):
    """
    Manually unlock a user account (admin only)
    """
    user = session.get(User, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.locked_until = None
    user.failed_login_attempts = 0
    session.add(user)
    session.commit()
    
    return {"message": f"User {user.email} unlocked successfully"}