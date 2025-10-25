from typing import Annotated, Optional
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from config import database

from entity.audit import AuditLog
from services.auth import AuthService

router = APIRouter(prefix="/audit", tags=["Audit Services"])

# OAuth2
Oauth2Dep = Annotated[str, Depends(OAuth2PasswordBearer(tokenUrl="auth/token"))]

SessionDep = Annotated[Session, Depends(database.get_db_session)]

AuthDep = Annotated[AuthService, Depends()]

@router.get("/audit-logs")
async def get_all_audit_logs(
    token: Oauth2Dep,
    session: SessionDep,
    auth: AuthDep,
    limit: int = 100,
    event_type: Optional[str] = None,
):
    """
    Get all audit logs (admin only - add authentication!)
    """
    # Get current user from token
    current_user = await auth.get_current_user(token, session)
    
    statement = select(AuditLog).where(AuditLog.user_id == current_user.id).order_by(AuditLog.created_at.desc())
    
    if event_type:
        statement = statement.where(AuditLog.event_type == event_type)
    
    statement = statement.limit(limit)
    logs = session.exec(statement).all()
    
    return [{
        "id": log.id,
        "user_id": log.user_id,
        "email": log.email,
        "event_type": log.event_type,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "success": log.success,
        "details": log.details,
        "created_at": log.created_at
    } for log in logs]