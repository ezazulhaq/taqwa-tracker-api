from uuid import UUID
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel
from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID

class AuditLog(SQLModel, table=True):
    """Audit log for security events"""
    __tablename__ = "audit_logs"
    
    id: Optional[UUID] = Field(default=None, sa_column=Column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")))
    user_id: UUID = Field(foreign_key="users.id")
    event_type: str = Field(index=True)  # signup, login, logout, password_reset, etc.
    email: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = Field(default=True)
    details: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
