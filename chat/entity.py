
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
import uuid
from sqlmodel import ARRAY, JSON, Column, Field, SQLModel, String


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")
    title: str = Field(default="Islamic Guidance Chat")
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))

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

class AgentExecution(SQLModel, table=True):
    __tablename__ = "agent_executions"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: Optional[uuid.UUID] = Field(default=None, foreign_key="conversations.id")
    message_id: Optional[uuid.UUID] = Field(default=None, foreign_key="messages.id")
    user_query: str
    execution_plan: Dict[str, Any] = Field(sa_column=Column(JSON))
    steps_executed: Dict[str, Any] = Field(sa_column=Column(JSON))
    tools_used: Optional[List[str]] = Field(default_factory=list, sa_column=Column(ARRAY(String)))
    execution_time_ms: Optional[int] = Field(default=None)
    success: Optional[bool] = Field(default=True)
    error_message: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
