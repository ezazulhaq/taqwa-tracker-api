import jwt
from jwt import InvalidTokenError

from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlmodel import Session, select
from starlette import status

from config import database
from config.email import config as email_config
from config.jwt import config as jwt_config
from entity.auth import RefreshToken, User
from model.user import EmailVerification, PasswordRecovery, PasswordReset, Token, UserCreate, UserResponse
from services.audit import AuditService
from services.auth import AuthService
from services.email import EmailService
from services.security import SecurityService

router = APIRouter(prefix="/auth", tags=["Authentication Services"])

# OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")
Oauth2Dep = Annotated[str, Depends(oauth2_scheme)]

SessionDep = Annotated[Session, Depends(database.get_db_session)]

SecurityDep = Annotated[SecurityService, Depends()]
AuthDep = Annotated[AuthService, Depends()]
AuditDep = Annotated[AuditService, Depends()]
EmailDep = Annotated[EmailService, Depends()]


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    session: SessionDep,
    rate_limit: SecurityDep,
    auth: AuthDep,
    audit: AuditDep,
    email: EmailDep
):
    """
    Register a new user and send verification email
    """
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limit.check_rate_limit(f"signup_{client_ip}", max_requests=3):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many signup attempts. Please try again later."
        )
    
    # Check if user already exists
    existing_user = auth.get_user_by_email(session, user_data.email)
    if existing_user:
        # Log failed signup attempt
        ip_address, user_agent = audit.get_client_info(request)
        audit.log_audit_event(
            session, "signup", user_data.email,
            ip_address=ip_address, user_agent=user_agent,
            success=False, details="Email already registered"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength (basic validation)
    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    # Create verification token (valid for 24 hours)
    verification_token = auth.create_access_token(
        data={"sub": user_data.email, "type": "email_verification"},
        expires_delta=timedelta(hours=24)
    )
    
    # Create new user
    hashed_password = auth.get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        verification_token=verification_token,
        is_verified=False
    )
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    # Log successful signup
    ip_address, user_agent = audit.get_client_info(request)
    audit.log_audit_event(
        session, "signup", user_data.email, db_user.id,
        ip_address=ip_address, user_agent=user_agent
    )
    
    # Send verification email in background
    verification_link = f"{email_config.front_end_url}/verify-email?token={verification_token}"
    html_content = email.get_verification_email_html(verification_link, user_data.full_name)
    
    background_tasks.add_task(
        email.send_email_with_resend,
        to_email=user_data.email,
        subject=f"Verify your {email_config.app_name} account",
        html_content=html_content
    )
    
    return db_user

@router.post("/token", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    session: SessionDep,
    rate_limit: SecurityDep,
    auth: AuthDep,
    audit: AuditDep
):
    """
    OAuth2 compatible token endpoint
    Login with email (as username) and password
    """
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limit.check_rate_limit(f"login_{client_ip}", max_requests=10):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )
    
    user = auth.authenticate_user(session, form_data.username, form_data.password)
    
    if not user:
        # Log failed login
        ip_address, user_agent = audit.get_client_info(request)
        audit.log_audit_event(
            session, "login", form_data.username,
            ip_address=ip_address, user_agent=user_agent,
            success=False, details="Invalid credentials"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    session.add(user)
    session.commit()
    
    # Create tokens
    access_token_expires = timedelta(minutes=jwt_config.access_token_expire_minutes)
    access_token = auth.create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    refresh_token = auth.create_refresh_token(user.id, session, request)
    
    # Log successful login
    ip_address, user_agent = audit.get_client_info(request)
    audit.log_audit_event(
        session, "login", user.email, user.id,
        ip_address=ip_address, user_agent=user_agent
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=jwt_config.access_token_expire_minutes * 60,
        refresh_token=refresh_token
    )

@router.post("/login", response_model=Token)
async def login_json(
    email: EmailStr,
    password: str,
    request: Request,
    session: SessionDep,
    rate_limit: SecurityDep,
    auth: AuthDep,
    audit: AuditDep
):
    """
    Alternative login endpoint with JSON body
    """
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limit.check_rate_limit(f"login_{client_ip}", max_requests=10):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )
    
    user = auth.authenticate_user(session, email, password)
    
    if not user:
        # Log failed login
        ip_address, user_agent = audit.get_client_info(request)
        audit.log_audit_event(
            session, "login", email,
            ip_address=ip_address, user_agent=user_agent,
            success=False, details="Invalid credentials"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    session.add(user)
    session.commit()
    
    # Create tokens
    access_token_expires = timedelta(minutes=jwt_config.access_token_expire_minutes)
    access_token = auth.create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    refresh_token = auth.create_refresh_token(user.id, session, request)
    
    # Log successful login
    ip_address, user_agent = audit.get_client_info(request)
    audit.log_audit_event(
        session, "login", user.email, user.id,
        ip_address=ip_address, user_agent=user_agent
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=jwt_config.access_token_expire_minutes * 60,
        refresh_token=refresh_token
    )

@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    refresh_token: str,
    session: SessionDep,
    auth: AuthDep
):
    """
    Refresh access token using refresh token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token"
    )
    
    try:
        payload = jwt.decode(refresh_token, jwt_config.secret_key, algorithms=[jwt_config.algorithm])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "refresh":
            raise credentials_exception
        
        # Check if token exists and is not revoked
        statement = select(RefreshToken).where(
            RefreshToken.token == refresh_token,
            RefreshToken.revoked == False
        )
        db_token = session.exec(statement).first()
        
        if not db_token:
            raise credentials_exception
        
        # Check if token is expired
        if db_token.expires_at < datetime.now(timezone.utc):
            raise credentials_exception
        
        # Get user
        user = session.get(User, int(user_id))
        if not user or not user.is_active:
            raise credentials_exception
        
        # Create new access token
        access_token_expires = timedelta(minutes=jwt_config.access_token_expire_minutes)
        access_token = auth.create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=jwt_config.access_token_expire_minutes * 60,
            refresh_token=refresh_token
        )
        
    except InvalidTokenError:
        raise credentials_exception

@router.post("/logout")
async def logout(
    token: Oauth2Dep,
    refresh_token: Optional[str] = None,
    request: Request = None,
    session: SessionDep = None,
    auth: AuthDep = None,
    audit: AuditDep = None,
):
    """
    Logout user and revoke refresh token
    """
    # Get current user from token
    current_user = await auth.get_current_user(token, session)
    
    if refresh_token:
        # Revoke the refresh token
        statement = select(RefreshToken).where(
            RefreshToken.token == refresh_token,
            RefreshToken.user_id == current_user.id
        )
        db_token = session.exec(statement).first()
        
        if db_token:
            db_token.revoked = True
            session.add(db_token)
            session.commit()
    
    # Log logout
    if request:
        ip_address, user_agent = audit.get_client_info(request)
        audit.log_audit_event(
            session, "logout", current_user.email, current_user.id,
            ip_address=ip_address, user_agent=user_agent
        )
    
    return {"message": "Successfully logged out"}

@router.post("/verify-email")
async def verify_email(
    data: EmailVerification,
    background_tasks: BackgroundTasks,
    session: SessionDep,
    auth: AuthDep,
    mail: EmailDep
):
    """
    Verify user email with token
    """
    try:
        payload = jwt.decode(data.token, jwt_config.secret_key, algorithms=[jwt_config.algorithm])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if email is None or token_type != "email_verification":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )
        
        user = auth.get_user_by_email(session, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.is_verified:
            return {"message": "Email already verified"}
        
        # Update user verification status
        user.is_verified = True
        user.verification_token = None
        user.updated_at = datetime.now(timezone.utc)
        session.add(user)
        session.commit()
        
        # Send welcome email in background
        html_content = mail.get_welcome_email_html(user.full_name)
        background_tasks.add_task(
            mail.send_email_with_resend,
            to_email=user.email,
            subject=f"Welcome to {email_config.app_name}!",
            html_content=html_content
        )
        
        return {"message": "Email verified successfully"}
        
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

@router.post("/resend-verification")
async def resend_verification(
    email: EmailStr,
    background_tasks: BackgroundTasks,
    session: SessionDep,
    auth: AuthDep,
    mail: EmailDep
):
    """
    Resend verification email
    """
    user = auth.get_user_by_email(session, email)
    
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a verification link has been sent"}
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Create new verification token
    verification_token = auth.create_access_token(
        data={"sub": user.email, "type": "email_verification"},
        expires_delta=timedelta(hours=24)
    )
    
    user.verification_token = verification_token
    user.updated_at = datetime.now(timezone.utc)
    session.add(user)
    session.commit()
    
    # Send verification email in background
    verification_link = f"{email_config.front_end_url}/verify-email?token={verification_token}"
    html_content = mail.get_verification_email_html(verification_link, user.full_name)
    
    background_tasks.add_task(
        mail.send_email_with_resend,
        to_email=user.email,
        subject=f"Verify your {email_config.app_name} account",
        html_content=html_content
    )
    
    return {"message": "Verification email sent"}

@router.post("/recover")
async def recover_password(
    data: PasswordRecovery,
    background_tasks: BackgroundTasks,
    session: SessionDep,
    auth: AuthDep,
    mail: EmailDep
):
    """
    Send password recovery email
    """
    user = auth.get_user_by_email(session, data.email)
    
    # Always return success to prevent email enumeration
    if user:
        # Create password reset token (valid for 1 hour)
        reset_token = auth.create_access_token(
            data={"sub": user.email, "type": "password_reset"},
            expires_delta=timedelta(hours=1)
        )
        
        # Send password reset email in background
        reset_link = f"{email_config.front_end_url}/reset-password?token={reset_token}"
        html_content = mail.get_password_reset_email_html(reset_link, user.full_name)
        
        background_tasks.add_task(
            mail.send_email_with_resend,
            to_email=user.email,
            subject=f"Reset your {email_config.app_name} password",
            html_content=html_content
        )
    
    return {
        "message": "If the email exists, a password reset link has been sent",
        "email": data.email
    }

@router.post("/reset-password")
async def reset_password(
    data: PasswordReset,
    session: SessionDep,
    auth: AuthDep
):
    """
    Reset password using recovery token
    """
    try:
        payload = jwt.decode(data.token, jwt_config.secret_key, algorithms=[jwt_config.algorithm])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if email is None or token_type != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )
        
        user = auth.get_user_by_email(session, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Validate new password
        if len(data.new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )
        
        # Update password
        user.hashed_password = auth.get_password_hash(data.new_password)
        user.updated_at = datetime.now(timezone.utc)
        session.add(user)
        session.commit()
        
        # Revoke all refresh tokens for this user
        statement = select(RefreshToken).where(RefreshToken.user_id == user.id)
        tokens = session.exec(statement).all()
        for token in tokens:
            token.revoked = True
            session.add(token)
        session.commit()
        
        return {"message": "Password successfully reset"}
        
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
