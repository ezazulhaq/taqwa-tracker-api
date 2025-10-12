from sqlmodel import Session, select
from entity.surah import VSurahDetails
from model.surah import SurahDetails

class SurahService:
    
    def get_surahs(self, surah_no: int, session: Session):
        statement = select(VSurahDetails).where(VSurahDetails.translator_name == 'Ahmed Raza').where(VSurahDetails.surah_no == surah_no)
        results = session.exec(statement).all()
        return [SurahDetails.model_validate(result.model_dump()) for result in results]
