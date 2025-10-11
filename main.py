from typing import Annotated, Sequence
from fastapi import FastAPI, HTTPException, Path
from services.surah_service import SurahService as surahService
from starlette import status
from model.surah import SurahDetails

app = FastAPI()

@app.get("/")
async def status_check():
    return {"status": "OK"}

@app.get("/surahs/{surah_no}", status_code=status.HTTP_200_OK, response_model=list[SurahDetails])
def get_ayahs_by_surah(
    surah_no: Annotated[int, Path(ge=1, le=114, title="Surah Number", description="Surah Number")], 
    ):
    surahDetails: list[SurahDetails] = surahService.get_ayahs_by_surah(surah_no)
    if not surahDetails:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ayahs not found")
    
    return surahDetails
