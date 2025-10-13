from typing import Optional
from pydantic import BaseModel


class UserProfile(BaseModel):
    user_id: Optional[str]
    location: Optional[str]
    timezone: Optional[str]
    preferred_madhab: Optional[str]
    language: Optional[str]
