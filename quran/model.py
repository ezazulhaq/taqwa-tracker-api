from typing import Optional
from pydantic import BaseModel

class LanguageResponse(BaseModel):
    language_code: str
    language_name: str

class TranslatorResponse(BaseModel):
    translator_id: int
    name: str
    language_code: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = True

class SurahResponse(BaseModel):
    surah_id: int
    name: str
    name_transliteration: Optional[str] = None
    name_en: Optional[str] = None
    total_ayas: int
    type: Optional[str] = None
    order_revealed: Optional[int] = None
    rukus: Optional[int] = None

class AyahDetails(BaseModel):
    surah_no: int
    surah_name_ar: str
    surah_name: str
    ayah_no: int
    arabic_text: str
    translation_text: str
    translator_name: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "surah_no": 1,
                "surah_name_ar": "الفاتحة",
                "surah_name": "Al-Fatihah",
                "ayah_no": 1,
                "arabic_text": "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ",
                "translation_text": "In the name of Allah, the Beneficent, the Merciful.",
                "translator_name": "Dr. Muhammad Iqbal"
            }
        }
    }
