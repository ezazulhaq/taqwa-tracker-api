from fastapi import FastAPI
from routers import audit, auth, chat, quran, status, user

app = FastAPI()

app.include_router(status.router)
app.include_router(auth.router)
app.include_router(quran.router)
app.include_router(chat.router)
app.include_router(user.router)
app.include_router(audit.router)
