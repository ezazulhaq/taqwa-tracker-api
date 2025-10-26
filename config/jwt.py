import os
from dotenv import load_dotenv

load_dotenv()

class JWTConfig:
    
    def __init__(self, secret_key: str, algorithm: str, access_token_expire_minutes: int, refresh_token_expire_days: int):
        self.__secret_key = secret_key
        self.__algorithm = algorithm
        self.__access_token_expire_minutes = access_token_expire_minutes
        self.__refresh_token_expire_days = refresh_token_expire_days
    
    @property
    def secret_key(self):
        return self.__secret_key
    
    @property
    def algorithm(self):
        return self.__algorithm
    
    @property
    def access_token_expire_minutes(self):
        return self.__access_token_expire_minutes
    
    @property
    def refresh_token_expire_days(self):
        return self.__refresh_token_expire_days


config = JWTConfig(
    secret_key=os.getenv("JWT_SECRET_KEY"),
    algorithm=os.getenv("JWT_ALGORITHM"),
    access_token_expire_minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES")),
    refresh_token_expire_days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS"))
)
