from sqlmodel import Session, select
from entity.surah import VSurahDetails
from model.surah import SurahDetails

class SurahService:
    
    def get_surahs(surah_no: int, session: Session = None):
        statement = select(VSurahDetails).where(VSurahDetails.translator_name == 'Ahmed Raza').where(VSurahDetails.surah_no == surah_no)
        results = session.exec(statement).all()
        session.close()
        return list(map(SurahService.map_surah_details, results))
