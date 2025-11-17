from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr


class FeedbackRequest(BaseModel):
    """Feedback request model"""
    user_id: Optional[UUID] = None
    category: Optional[str] = None
    email: EmailStr
    content: str


class FeedbackResponse(BaseModel):
    """Feedback response model"""
    id: UUID
    message: str
    email_sent: bool