from dotenv import load_dotenv
from pinecone import Pinecone
import os

load_dotenv()

class PineconeConfig:
    
    def __init__(self, api_key: str, ):
        self.__api_key = api_key
        
    @property
    def api_key(self):
        return self.__api_key
    
config = PineconeConfig(
    api_key=os.getenv("PINECONE_API_KEY")
)

pc = Pinecone(api_key=config.api_key)
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))
