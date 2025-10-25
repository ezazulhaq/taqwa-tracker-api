from collections import defaultdict
from datetime import datetime, timedelta, timezone
from functools import wraps
from fastapi import HTTPException, Request
from starlette import status
from config.security import config as security_config

class SecurityService:
    # Simple in-memory rate limiting (use Redis in production)
    rate_limit_store = defaultdict(list)

    @staticmethod
    def check_rate_limit(identifier: str, max_requests: int = security_config.rate_limit_requests) -> bool:
        """
        Check if request exceeds rate limit
        """
        now = datetime.now(timezone.utc)
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old entries
        SecurityService.rate_limit_store[identifier] = [
            timestamp for timestamp in SecurityService.rate_limit_store[identifier]
            if timestamp > minute_ago
        ]
        
        # Check limit
        if len(SecurityService.rate_limit_store[identifier]) >= max_requests:
            return False
        
        # Add current request
        SecurityService.rate_limit_store[identifier].append(now)
        return True

    @staticmethod
    def rate_limit(max_requests: int = security_config.rate_limit_requests):
        """
        Decorator for rate limiting endpoints
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                request: Request = kwargs.get('request')
                if request:
                    client_ip = request.client.host
                    if not SecurityService.check_rate_limit(client_ip, max_requests):
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail="Too many requests. Please try again later."
                        )
                return await func(*args, **kwargs)
            return wrapper
        return decorator
