from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from auth.entity import User
from config import database

from audit.entity import AuditLog
from audit.model import AuditLogsResponse
from auth.service import AuthService
from pydantic import EmailStr

router = APIRouter(prefix="/audit", tags=["Audit Services"])

# OAuth2
Oauth2Dep = Annotated[str, Depends(OAuth2PasswordBearer(tokenUrl="auth/token"))]

SessionDep = Annotated[Session, Depends(database.get_db_session)]

AdminDep = Annotated[User, Depends(AuthService.get_admin_user)]

@router.get("/audit-logs", response_model=List[AuditLogsResponse])
async def get_all_audit_logs(
    admin_user: AdminDep,
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