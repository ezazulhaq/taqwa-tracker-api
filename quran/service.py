from typing import List
from sqlmodel import Session, select
from quran.entity import VSurahDetails, Surah, Language, Translator
from quran.model import AyahDetails, SurahResponse, LanguageResponse, TranslatorResponse

class QuranService:
    
    def get_surahs(self, session: Session) -> List[SurahResponse]:
        statement = select(Surah).order_by(Surah.surah_id)
        results = session.exec(statement).all()
        return results
    
    def get_ayahs(self, surah_no: int, translator:str, session: Session) -> List[AyahDetails]:
        statement = select(VSurahDetails).where(VSurahDetails.translator_name == translator).where(VSurahDetails.surah_no == surah_no)
        results = session.exec(statement).all()
        return results
    
    def get_languages(self, session: Session) -> List[LanguageResponse]:
        statement = select(Language).order_by(Language.language_name)
        results = session.exec(statement).all()
        return results
    
    def get_translators(self, session: Session, language_code: str = None, active_only: bool = True) -> List[TranslatorResponse]:
        statement = select(Translator)
        
        if active_only:
            statement = statement.where(Translator.is_active == True)
        
        if language_code:
            statement = statement.where(Translator.language_code == language_code)
        
        statement = statement.order_by(Translator.name)
        results = session.exec(statement).all()
        return results
