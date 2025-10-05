from pydantic import BaseModel

class SurahDetails(BaseModel):
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
