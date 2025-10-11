from fastapi import HTTPException
from typing import List
from model.surah import SurahDetails
from config.supabase import HEADERS, URL
from starlette import status
import requests

class SurahService:
    
    def get_ayahs_by_surah(surah_no: int) -> List[SurahDetails]:
        url = f"{URL}v_surah_details?select=*&surah_no=eq.{surah_no}&translator_name=eq.Ahmed Raza&order=ayah_no"
        results = requests.get(url, headers=HEADERS)
        if results.status_code != status.HTTP_200_OK:
            print(results.json())
            raise HTTPException(status_code=results.status_code, detail="Error fetching data")
        
        data = results.json()
        return [SurahDetails(**item) for item in data]
