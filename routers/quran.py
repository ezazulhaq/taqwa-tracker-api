from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlmodel import Session

from config.database import get_db_session
from model.surah import SurahDetails
from services.surah_service import SurahService
from starlette import status

router = APIRouter(prefix="/quran")

SessionDep = Annotated[Session, Depends(get_db_session)]

@router.get("/surahs/{surah_no}", status_code=status.HTTP_200_OK, response_model=list[SurahDetails])
def get_ayahs_by_surah(
    surah_no: Annotated[int, Path(ge=1, le=114, title="Surah Number", description="Surah Number")], 
    session: SessionDep
    ):
    try:
        surah_service = SurahService()
        surahDetails: list[SurahDetails] = surah_service.get_surahs(surah_no, session)
        if not surahDetails:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ayahs not found")
        
        return surahDetails
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error fetching surahs: {str(e)}")
