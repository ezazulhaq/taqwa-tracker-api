
from typing import Optional
from fastapi import Request
from sqlmodel import Session
from entity.audit import AuditLog


class AuditService:

    @staticmethod
    def log_audit_event(
        session: Session,
        event_type: str,
        email: Optional[str] = None,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        details: Optional[str] = None
    ):
        """
        Log security audit event
        """
        audit_log = AuditLog(
            user_id=user_id,
            event_type=event_type,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            details=details
        )
        session.add(audit_log)
        session.commit()

    @staticmethod
    def get_client_info(request: Request) -> tuple[str, str]:
        """
        Extract client IP and user agent from request
        """
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        return ip_address, user_agent
