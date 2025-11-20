from dotenv import load_dotenv
import os
import google.generativeai as genai

load_dotenv()

class GeminiConfig:
    
    def __init__(self, api_key: str, embedding_model: str):
        self.__api_key = api_key
        self.__embedding_model = embedding_model
        
    @property
    def api_key(self):
        return self.__api_key
    
    @property
    def embedding_model(self):
        return self.__embedding_model

config = GeminiConfig(
    api_key=os.getenv("GEMINI_API_KEY"),
    embedding_model=os.getenv("GEMINI_MODEL_EMBED")
)
    
genai.configure(api_key=config.api_key)
genai_client = genai
