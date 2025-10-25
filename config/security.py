
import os
class SecurityConfig:
    
    def __init__(self, max_login_attempts: int, lockout_duration_minutes: int, rate_limit_requests: int):
        self.__max_login_attempts = max_login_attempts
        self.__lockout_duration_minutes = lockout_duration_minutes
        self.__rate_limit_requests = rate_limit_requests

    @property
    def max_login_attempts(self) -> int:
        return self.__max_login_attempts
    
    @property
    def lockout_duration_minutes(self) -> int:
        return self.__lockout_duration_minutes
    
    @property
    def rate_limit_requests(self) -> int:
        return self.__rate_limit_requests


config = SecurityConfig(
    max_login_attempts=int(os.getenv("MAX_LOGIN_ATTEMPTS", "5")),
    lockout_duration_minutes=int(os.getenv("LOCKOUT_DURATION_MINUTES", "15")),
    rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
)