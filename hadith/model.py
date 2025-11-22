from typing import Optional
from pydantic import BaseModel
from uuid import UUID

class SourceResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Sahih Bukhari",
                "description": "The most authentic hadith collection",
                "is_active": True
            }
        }
    }

class ChapterResponse(BaseModel):
    id: UUID
    source_id: UUID
    chapter_no: int
    chapter_name: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "source_id": "550e8400-e29b-41d4-a716-446655440000",
                "chapter_no": 1,
                "chapter_name": "Revelation"
            }
        }
    }

class HadithDetails(BaseModel):
    id: UUID
    source_name: str
    chapter_no: int
    chapter_name: str
    hadith_no: int
    text_en: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "source_name": "Sahih Bukhari",
                "chapter_no": 1,
                "chapter_name": "Revelation",
                "hadith_no": 1,
                "text_en": "Actions are according to intentions..."
            }
        }
    }