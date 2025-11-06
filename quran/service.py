from typing import List
from sqlmodel import Session, select
from quran.entity import VSurahDetails, Surah
from quran.model import AyahDetails, SurahResponse

class QuranService:
    
    def get_surahs(self, session: Session) -> List[SurahResponse]:
        statement = select(Surah).order_by(Surah.surah_id)
        results = session.exec(statement).all()
        return results
    
    def get_ayahs(self, surah_no: int, translator:str, session: Session) -> List[AyahDetails]:
        statement = select(VSurahDetails).where(VSurahDetails.translator_name == translator).where(VSurahDetails.surah_no == surah_no)
        results = session.exec(statement).all()
        return results
