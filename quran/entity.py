from sqlmodel import SQLModel, Field, Relationship
from typing import Optional

class Language(SQLModel, table=True):
    __tablename__ = "languages"
    
    language_code: str = Field(primary_key=True, max_length=3)
    language_name: str = Field(max_length=255)

class Translator(SQLModel, table=True):
    __tablename__ = "translators"
    
    translator_id: int = Field(primary_key=True)
    name: str = Field(max_length=255)
    language_code: Optional[str] = Field(default=None, max_length=3, foreign_key="languages.language_code")
    full_name: Optional[str] = Field(default="")
    is_active: bool = Field(default=True)

class Surah(SQLModel, table=True):
    __tablename__ = "surahs"
    
    surah_id: int = Field(primary_key=True)
    name: str = Field(max_length=255)
    name_transliteration: Optional[str] = Field(default=None, max_length=255)
    name_en: Optional[str] = Field(default=None, max_length=255)
    total_ayas: int
    type: Optional[str] = Field(default=None, max_length=255)
    order_revealed: Optional[int] = Field(default=None)
    rukus: Optional[int] = Field(default=None)

class VSurahDetails(SQLModel, table=True):
    __tablename__ = "v_surah_details"
    
    surah_no: int = Field(primary_key=True)
    surah_name_ar: str
    surah_name: str
    ayah_no: int = Field(primary_key=True)
    arabic_text: str
    translation_text: str
    translator_name: str = Field(primary_key=True)
