from typing import List, Optional
from sqlmodel import Session, select
from library.entity import Category, Library
from library.model import CategoryResponse, LibraryResponse

class LibraryService:
    
    def get_categories(self, session: Session) -> List[CategoryResponse]:
        statement = select(Category).where(Category.is_active == True).order_by(Category.name)
        results = session.exec(statement).all()
        return results
    
    def get_library_items(self, session: Session, category_id: Optional[int] = None) -> List[LibraryResponse]:
        statement = select(
            Library.id,
            Library.name,
            Library.pdf_name,
            Library.category_id,
            Category.name.label("category_name"),
            Library.storage_key,
            Library.is_active
        ).join(Category).where(Library.is_active == True)
        
        if category_id:
            statement = statement.where(Library.category_id == category_id)
            
        results = session.exec(statement).all()
        return [
            LibraryResponse(
                id=row.id,
                name=row.name,
                pdf_name=row.pdf_name,
                category_id=row.category_id,
                category_name=row.category_name,
                storage_key=row.storage_key,
                is_active=row.is_active
            ) for row in results
        ]