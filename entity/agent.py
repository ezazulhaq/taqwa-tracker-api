from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
from sqlmodel import Field, SQLModel, JSON, Column
from sqlalchemy import ARRAY, String

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
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
