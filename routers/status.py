from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, text
from config import database
from starlette import status

router = APIRouter(tags=["Status Services"])

SessionDep = Annotated[Session, Depends(database.get_db_session)]

@router.get("/")
async def status_check():
    return {"status": "OK"}

@router.get("/health/db")
def test_db_connection(session: SessionDep):
    try:
        session.exec(text("SELECT 1"))
        return {"status": "OK", "message": "Database connection successful ✅"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database connection failed: {str(e)}")
