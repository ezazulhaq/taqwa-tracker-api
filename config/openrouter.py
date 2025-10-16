from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

openrouter_client = OpenAI(
    base_url=os.getenv("OPENROUTER_URL"),
    api_key=os.getenv("OPENROUTER_API_KEY")
)