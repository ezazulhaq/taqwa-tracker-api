from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import UUID as PGUUID


class Feedback(SQLModel, table=True):
    """Feedback database model"""
    __tablename__ = "feedback"
    
    id: Optional[UUID] = Field(default=None, sa_column=Column(PGUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: Optional[UUID] = Field(default=None, foreign_key="users.id")
    content: str
    category: Optional[str] = None
    email_sent: bool = Field(default=False)
    email: str = Field(default="")