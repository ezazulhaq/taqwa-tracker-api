from typing import Annotated, Sequence
from fastapi import FastAPI, HTTPException, Path
from fastapi import Depends
from sqlmodel import Session, text
from services.surah_service import SurahService as surahService
from config.database import get_db_session
from starlette import status
from model.surah import SurahDetails

SessionDep = Annotated[Session, Depends(get_db_session)]

app = FastAPI()

@app.get("/")
async def status_check():
    return {"status": "OK"}

@app.get("/health/db")
def test_db_connection(session: SessionDep):
    try:
        session.exec(text("SELECT 1"))
        raise HTTPException(status_code=status.HTTP_200_OK, detail="Database connection successful ✅")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database connection failed: {str(e)}")

@app.get("/surahs/{surah_no}", status_code=status.HTTP_200_OK, response_model=list[SurahDetails])
def get_ayahs_by_surah(
    surah_no: Annotated[int, Path(ge=1, le=114, title="Surah Number", description="Surah Number")], 
    session: SessionDep
    ):
    surahDetails: list[SurahDetails] = surahService.get_surahs(surah_no, session)
    if not surahDetails:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ayahs not found")
    
    return surahDetails
