
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID


class User(SQLModel, table=True):
    """User database model"""
    __tablename__ = "users"
    
    id: Optional[UUID] = Field(default=None, sa_column=Column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")))
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    verification_token: Optional[str] = None
    failed_login_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = None
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RefreshToken(SQLModel, table=True):
    """Refresh token database model"""
    __tablename__ = "refresh_tokens"
    
    id: Optional[UUID] = Field(default=None, sa_column=Column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")))
    user_id: UUID = Field(foreign_key="users.id")
    token: str = Field(unique=True, index=True)
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    revoked: bool = Field(default=False)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
