from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[datetime] = None

class AgentStep(BaseModel):
    step: int
    action: str
    tool_used: str
    result: str
    reasoning: str

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    message_id: str
    agent_steps: List[AgentStep]
    tools_used: List[str]
