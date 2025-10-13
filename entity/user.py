from datetime import datetime
from typing import Any, Dict, Optional
import uuid
from sqlmodel import JSON, Column, Field, SQLModel


class UserProfile(SQLModel, table=True):
    __tablename__ = "user_profiles"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="auth.users.id", unique=True)
    location: Optional[str] = Field(default=None)
    timezone: Optional[str] = Field(default=None)
    preferred_madhab: Optional[str] = Field(default=None)
    language: Optional[str] = Field(default="en")
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
