from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import UUID

class Source(SQLModel, table=True):
    __tablename__ = "sources"
    
    id: UUID = Field(primary_key=True)
    name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)

class Chapter(SQLModel, table=True):
    __tablename__ = "chapters"
    
    id: UUID = Field(primary_key=True)
    source_id: UUID = Field(foreign_key="sources.id")
    chapter_no: int
    chapter_name: str = Field(max_length=255)

class Hadith(SQLModel, table=True):
    __tablename__ = "hadiths"
    
    id: UUID = Field(primary_key=True)
    source_id: UUID = Field(foreign_key="sources.id")
    chapter_id: UUID = Field(foreign_key="chapters.id")
    hadith_no: int
    text_ar: str
    text_en: str

class VHadithDetails(SQLModel, table=True):
    __tablename__ = "v_hadith_details"
    
    id: UUID = Field(primary_key=True)
    source_name: str
    chapter_no: int
    chapter_name: str
    hadith_no: int
    text_en: str