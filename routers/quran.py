from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from config.database import get_db_session
from quran.model import AyahDetails, SurahResponse
from quran.service import QuranService
from starlette import status

router = APIRouter(
    prefix="/quran", 
    tags=["Quran Services"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Access forbidden"}
    }
)

SessionDep = Annotated[Session, Depends(get_db_session)]

QuranDep = Annotated[QuranService, Depends()]

@router.get(
    "/surahs",
    status_code=status.HTTP_200_OK,
    response_model=list[SurahResponse],
    summary="Get All Surahs",
    description="Retrieve a complete list of all 114 Surahs in the Quran with their basic information including names, total ayahs, and metadata.",
    responses={
        200: {
            "description": "Successfully retrieved all Surahs",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "surah_id": 1,
                            "name": "الفاتحة",
                            "name_transliteration": "Al-Fatihah",
                            "name_en": "The Opening",
                            "total_ayas": 7,
                            "type": "Meccan",
                            "order_revealed": 5,
                            "rukus": 1
                        },
                        {
                            "surah_id": 2,
                            "name": "البقرة",
                            "name_transliteration": "Al-Baqarah",
                            "name_en": "The Cow",
                            "total_ayas": 286,
                            "type": "Medinan",
                            "order_revealed": 87,
                            "rukus": 40
                        }
                    ]
                }
            }
        },
        404: {"description": "No Surahs found in database"},
        500: {"description": "Internal server error while fetching Surahs"}
    }
)
def get_surah_info(
    session: SessionDep,
    quran: QuranDep
    ):
    try:
        ayahDetails: list[SurahResponse] = quran.get_surahs(session)
        if not ayahDetails:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Surahs not found")
        
        return ayahDetails
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error fetching surahs")

@router.get(
    "/ayahs",
    status_code=status.HTTP_200_OK,
    response_model=list[AyahDetails],
    summary="Get Ayahs by Surah Number",
    description="Retrieve all Ayahs (verses) from a specific Surah with Arabic text, translations, and metadata. Surah numbers range from 1 (Al-Fatihah) to 114 (An-Nas).",
    responses={
        200: {
            "description": "Successfully retrieved Ayahs for the specified Surah",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "surah_no": 1,
                            "surah_name_ar": "الفاتحة",
                            "surah_name": "Al-Fatihah",
                            "ayah_no": 1,
                            "arabic_text": "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ",
                            "translation_text": "In the name of Allah, the Beneficent, the Merciful.",
                            "translator_name": "Dr. Muhammad Iqbal"
                        },
                        {
                            "surah_no": 1,
                            "surah_name_ar": "الفاتحة",
                            "surah_name": "Al-Fatihah",
                            "ayah_no": 2,
                            "arabic_text": "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَـٰلَمِينَ",
                            "translation_text": "Praise be to Allah, Lord of the Worlds.",
                            "translator_name": "Dr. Muhammad Iqbal"
                        }
                    ]
                }
            }
        },
        400: {"description": "Invalid Surah number. Must be between 1 and 114."},
        404: {"description": "No Ayahs found for the specified Surah number"},
        422: {"description": "Validation error - Surah number must be an integer between 1 and 114"},
        500: {"description": "Internal server error while fetching Ayahs"}
    }
)
def get_ayahs_by_surah(
    surah_no: Annotated[
        int, 
        Query(
            ge=1, 
            le=114, 
            title="Surah Number", 
            description="The number of the Surah (1-114). Examples: 1 for Al-Fatihah, 2 for Al-Baqarah, 114 for An-Nas",
            example=1
        )
    ], 
    session: SessionDep,
    quran: QuranDep
    ):
    try:
        ayahDetails: list[AyahDetails] = quran.get_ayahs(surah_no, session)
        if not ayahDetails:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ayahs not found")
        
        return ayahDetails
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error fetching surahs: {str(e)}")
