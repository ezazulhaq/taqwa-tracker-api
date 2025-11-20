import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class OpenRouterConfig:
    
    def __init__(self, base_url: str, api_key: str, mistral_model: str, openapi_model: str):
        self.__base_url = base_url
        self.__api_key = api_key
        self.__mistral_model = mistral_model
        self.__openapi_model = openapi_model
    
    @property
    def base_url(self):
        return self.__base_url
    
    @property
    def api_key(self):
        return self.__api_key
    
    @property
    def mistral_model(self):
        return self.__mistral_model
    
    @property
    def openapi_model(self):
        return self.__openapi_model


config = OpenRouterConfig(
    base_url=os.getenv("OPENROUTER_URL"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
    mistral_model=os.getenv("OPENROUTER_MODEL_MISTRAL"),
    openapi_model=os.getenv("OPENROUTER_MODEL_OPENAI")
)

openrouter_client = OpenAI(
    base_url=config.base_url,
    api_key=config.api_key,
)