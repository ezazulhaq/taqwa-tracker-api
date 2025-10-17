from typing import Annotated
from fastapi import FastAPI, HTTPException, Depends, status
from sqlmodel import Session, text
from config.database import get_db_session
from routers import chat, quran

SessionDep = Annotated[Session, Depends(get_db_session)]

app = FastAPI()

app.include_router(quran.router)
app.include_router(chat.router)

@app.get("/")
async def status_check():
    return {"status": "OK"}

@app.get("/health/db")
def test_db_connection(session: SessionDep):
    try:
        session.exec(text("SELECT 1"))
        return {"status": "OK", "message": "Database connection successful ✅"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database connection failed: {str(e)}")
