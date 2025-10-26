import os
from dotenv import load_dotenv

load_dotenv()

class ResendConfig:
    
    def __init__(self, api_key, from_email, app_name, front_end_url):
        self.__api_key = api_key
        self.__from_email = from_email
        self.__app_name = app_name
        self.__front_end_url = front_end_url
        
    @property
    def api_key(self):
        return self.__api_key
    
    @property
    def from_email(self):
        return self.__from_email
    
    @property
    def app_name(self):
        return self.__app_name
    
    @property
    def front_end_url(self):
        return self.__front_end_url
    

config = ResendConfig(
    api_key=os.getenv("RESEND_API_KEY"),
    from_email=os.getenv("RESEND_FROM_EMAIL"),
    app_name=os.getenv("APP_NAME", "The Taqwa Tracker"),
    front_end_url=os.getenv("FRONTEND_URL")
)
