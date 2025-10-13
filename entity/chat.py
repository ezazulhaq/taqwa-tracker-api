
from datetime import datetime
from typing import Any, Dict, Literal, Optional
import uuid
from sqlmodel import JSON, Column, Field, SQLModel


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="auth.users.id")
    title: str = Field(default="Islamic Guidance Chat")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

class ConversationSummary(SQLModel, table=True):
    __tablename__ = "conversation_summaries"
    
    id: uuid.UUID = Field(primary_key=True)
    user_id: Optional[uuid.UUID] = Field(default=None)
    title: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    message_count: int
    last_message_at: Optional[datetime]


class Message(SQLModel, table=True):
    __tablename__ = "messages"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: Optional[uuid.UUID] = Field(default=None, foreign_key="conversations.id")
    role: str = Field(default="user")
    content: str
    message_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column("metadata", JSON))
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
