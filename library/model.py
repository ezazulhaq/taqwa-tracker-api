from pydantic import BaseModel
from typing import Optional

class CategoryResponse(BaseModel):
    id: int
    name: str
    is_active: bool

class LibraryResponse(BaseModel):
    id: int
    name: str
    pdf_name: str
    category_id: int
    category_name: str
    storage_key: str
    is_active: bool

class LibraryWithCategory(BaseModel):
    id: int
    name: str
    pdf_name: str
    category: CategoryResponse
    storage_key: str
    is_active: bool