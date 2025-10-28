from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class AuditLogsResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    email: str
    event_type: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    success: bool
    details: Optional[str]
    created_at: datetime
