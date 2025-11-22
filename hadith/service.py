from typing import List, Optional
from sqlmodel import Session, select
from hadith.entity import Source, Chapter, VHadithDetails
from hadith.model import SourceResponse, ChapterResponse, HadithDetails

class HadithService:
    
    def get_sources(self, session: Session) -> List[SourceResponse]:
        """Get all active hadith sources"""
        statement = select(Source).where(Source.is_active == True).order_by(Source.name)
        results = session.exec(statement).all()
        return results
    
    def get_chapters_by_source(self, source_name: str, session: Session) -> List[ChapterResponse]:
        """Get all chapters for a specific source"""
        statement = (
            select(Chapter)
            .join(Source)
            .where(Source.name == source_name)
            .where(Source.is_active == True)
            .order_by(Chapter.chapter_no)
        )
        results = session.exec(statement).all()
        return results
    
    def get_hadiths(
        self, 
        source_name: str, 
        chapter_no: int, 
        hadith_no: Optional[int],
        session: Session
    ) -> List[HadithDetails]:
        """Get hadiths from the view table with optional filtering"""
        statement = (
            select(VHadithDetails)
            .where(VHadithDetails.source_name == source_name)
            .where(VHadithDetails.chapter_no == chapter_no)
        )
        
        if hadith_no is not None:
            statement = statement.where(VHadithDetails.hadith_no == hadith_no)
        
        statement = statement.order_by(VHadithDetails.chapter_no, VHadithDetails.hadith_no)
        results = session.exec(statement).all()
        return results