import uuid

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class MessageRequest(BaseModel):
    user_id: uuid.UUID
    conversation_id: Optional[uuid.UUID] = None
    message: str = Field(..., min_length=1)

class MessageResponse(BaseModel):
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

class ConversationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    last_message_at: Optional[datetime]