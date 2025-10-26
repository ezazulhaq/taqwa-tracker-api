from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None

class TokenData(BaseModel):
    email: Optional[str] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime

class PasswordRecovery(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str

class EmailVerification(BaseModel):
    token: str

class SessionInfo(BaseModel):
    id: UUID
    created_at: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    is_current: bool = False

class UserResponseExtended(UserResponse):
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0