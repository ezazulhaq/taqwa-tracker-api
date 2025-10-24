from fastapi import FastAPI
from routers import auth, chat, quran, status

app = FastAPI()

app.include_router(status.router)
app.include_router(auth.router)
app.include_router(quran.router)
app.include_router(chat.router)
