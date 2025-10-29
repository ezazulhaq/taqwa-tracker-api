from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlmodel import Session

from config.database import get_db_session
from quran.model import SurahDetails
from quran.service import QuranService
from starlette import status

router = APIRouter(prefix="/quran", tags=["Quran Services"])

SessionDep = Annotated[Session, Depends(get_db_session)]

QuranDep = Annotated[QuranService, Depends()]

@router.get("/surahs/{surah_no}", status_code=status.HTTP_200_OK, response_model=list[SurahDetails])
def get_ayahs_by_surah(
    surah_no: Annotated[int, Path(ge=1, le=114, title="Surah Number", description="Surah Number")], 
    session: SessionDep,
    quran: QuranDep
    ):
    try:
        surahDetails: list[SurahDetails] = quran.get_surahs(surah_no, session)
        if not surahDetails:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ayahs not found")
        
        return surahDetails
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error fetching surahs: {str(e)}")
