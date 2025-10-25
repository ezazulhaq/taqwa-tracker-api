import jwt

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer

from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
from passlib.context import CryptContext
from sqlmodel import Session, select
from config import database
from config.jwt import config as jwt_config
from config.security import config as security_config
from entity.auth import RefreshToken, User
from model.user import TokenData
from starlette import status
from services.audit import AuditService

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
Oauth2Dep = Annotated[str, Depends(oauth2_scheme)]

SessionDep = Annotated[Session, Depends(database.get_db_session)]

class AuthService:
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=jwt_config.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, jwt_config.secret_key, algorithm=jwt_config.algorithm)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(user_id: int, session: Session, request: Optional[Request] = None) -> str:
        """Create and store refresh token"""
        audit_service = AuditService()
        
        expires_at = datetime.now(timezone.utc) + timedelta(days=jwt_config.refresh_token_expire_days)
        
        token_data = {
            "sub": str(user_id),
            "exp": expires_at,
            "type": "refresh"
        }
        
        token = jwt.encode(token_data, jwt_config.secret_key, algorithm=jwt_config.algorithm)
        
        # Get client info
        ip_address = None
        user_agent = None
        if request:
            ip_address, user_agent = audit_service.get_client_info(request)
        
        # Store in database
        db_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        session.add(db_token)
        session.commit()
        
        return token

    @staticmethod
    def get_user_by_email(session: Session, email: str) -> Optional[User]:
        """Get user by email"""
        statement = select(User).where(User.email == email)
        return session.exec(statement).first()

    @staticmethod
    def authenticate_user(session: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = AuthService.get_user_by_email(session, email)
        if not user:
            return None
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            remaining = int((user.locked_until - datetime.now(timezone.utc)).total_seconds() / 60)
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account locked due to multiple failed login attempts. Try again in {remaining} minutes."
            )
        
        # Reset lock if expired
        if user.locked_until and user.locked_until <= datetime.now(timezone.utc):
            user.locked_until = None
            user.failed_login_attempts = 0
            session.add(user)
            session.commit()
        
        if not AuthService.verify_password(password, user.hashed_password):
            # Increment failed attempts
            user.failed_login_attempts += 1
            
            # Lock account if too many attempts
            if user.failed_login_attempts >= security_config.max_login_attempts:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=security_config.lockout_duration_minutes)
                session.add(user)
                session.commit()
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail=f"Account locked due to {security_config.max_login_attempts} failed login attempts. Try again in {security_config.lockout_duration_minutes} minutes."
                )
            
            session.add(user)
            session.commit()
            return None
        
        # Reset failed attempts on successful login
        if user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            session.add(user)
            session.commit()
        
        return user

    @staticmethod
    async def get_current_user(
        token: Oauth2Dep,
        session: SessionDep
    ) -> User:
        """Get current user from JWT token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, jwt_config.secret_key, algorithms=[jwt_config.algorithm])
            email: str = payload.get("sub")
            token_type: str = payload.get("type")
            
            if email is None or token_type != "access":
                raise credentials_exception
                
            token_data = TokenData(email=email)
        except jwt.InvalidTokenError:
            raise credentials_exception
        
        user = AuthService.get_user_by_email(session, email=token_data.email)
        if user is None:
            raise credentials_exception
        
        return user

    @staticmethod
    async def get_current_active_user(
        current_user: Annotated[User, Depends(get_current_user)]
    ) -> User:
        """Ensure user is active"""
        if not current_user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user
