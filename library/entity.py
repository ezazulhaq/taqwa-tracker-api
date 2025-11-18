from sqlmodel import SQLModel, Field
from typing import Optional

class Category(SQLModel, table=True):
    __tablename__ = "categories"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, unique=True)
    is_active: bool = Field(default=True)

class Library(SQLModel, table=True):
    __tablename__ = "library"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    pdf_name: str = Field(max_length=255)
    category_id: int = Field(foreign_key="categories.id")
    storage_key: str = Field(max_length=255)
    is_active: bool = Field(default=True)