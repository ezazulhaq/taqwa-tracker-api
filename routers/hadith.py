from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from config.database import get_db_session
from hadith.model import SourceResponse, ChapterResponse, HadithDetails
from hadith.service import HadithService
from starlette import status

router = APIRouter(
    prefix="/hadith", 
    tags=["Hadith Services"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Access forbidden"}
    }
)

SessionDep = Annotated[Session, Depends(get_db_session)]
HadithDep = Annotated[HadithService, Depends()]

@router.get(
    "/sources",
    status_code=status.HTTP_200_OK,
    response_model=list[SourceResponse],
    summary="Get All Hadith Sources",
    description="Retrieve a complete list of all active hadith sources (collections) with their basic information.",
    responses={
        200: {
            "description": "Successfully retrieved all hadith sources",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "name": "Sahih Bukhari",
                            "description": "The most authentic hadith collection",
                            "is_active": True
                        },
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440001",
                            "name": "Sahih Muslim",
                            "description": "Second most authentic hadith collection",
                            "is_active": True
                        }
                    ]
                }
            }
        },
        404: {"description": "No hadith sources found in database"},
        500: {"description": "Internal server error while fetching sources"}
    }
)
def get_hadith_sources(
    session: SessionDep,
    hadith: HadithDep
):
    try:
        sources: list[SourceResponse] = hadith.get_sources(session)
        if not sources:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="No hadith sources found"
            )
        return sources
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Error fetching hadith sources"
        )

@router.get(
    "/chapters",
    status_code=status.HTTP_200_OK,
    response_model=list[ChapterResponse],
    summary="Get Chapters by Source",
    description="Retrieve all chapters from a specific hadith source/collection.",
    responses={
        200: {
            "description": "Successfully retrieved chapters for the specified source",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440002",
                            "source_id": "550e8400-e29b-41d4-a716-446655440000",
                            "chapter_no": 1,
                            "chapter_name": "Revelation"
                        },
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440003",
                            "source_id": "550e8400-e29b-41d4-a716-446655440000",
                            "chapter_no": 2,
                            "chapter_name": "Belief"
                        }
                    ]
                }
            }
        },
        404: {"description": "No chapters found for the specified source"},
        500: {"description": "Internal server error while fetching chapters"}
    }
)
def get_chapters_by_source(
    session: SessionDep,
    hadith: HadithDep,
    source_name: Annotated[
        Optional[str],
        Query(
            title="Source Name",
            description="The name of the hadith source/collection (e.g., 'Sahih Bukhari', 'Sahih Muslim')",
            example="Sahih Bukhari"
        )
    ] = "Sahih Bukhari"
):
    try:
        chapters: list[ChapterResponse] = hadith.get_chapters_by_source(source_name, session)
        if not chapters:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"No chapters found for source: {source_name}"
            )
        return chapters
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Error fetching chapters"
        )

@router.get(
    "/hadiths",
    status_code=status.HTTP_200_OK,
    response_model=list[HadithDetails],
    summary="Get Hadiths by Source",
    description="Retrieve hadiths from a specific source with optional filtering by chapter and hadith number.",
    responses={
        200: {
            "description": "Successfully retrieved hadiths",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440004",
                            "source_name": "Sahih Bukhari",
                            "chapter_no": 1,
                            "chapter_name": "Revelation",
                            "hadith_no": 1,
                            "text_en": "Actions are according to intentions, and everyone will get what was intended..."
                        },
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440005",
                            "source_name": "Sahih Bukhari",
                            "chapter_no": 1,
                            "chapter_name": "Revelation",
                            "hadith_no": 2,
                            "text_en": "While we were sitting with the Prophet..."
                        }
                    ]
                }
            }
        },
        404: {"description": "No hadiths found for the specified criteria"},
        500: {"description": "Internal server error while fetching hadiths"}
    }
)
def get_hadiths(
    session: SessionDep,
    hadith: HadithDep,
    chapter_no: Annotated[
        int,
        Query(
            ge=1,
            title="Chapter Number",
            description="Chapter number to filter hadiths.",
            example=1
        )
    ],
    source_name: Annotated[
        Optional[str],
        Query(
            title="Source Name",
            description="Optional name of the hadith source/collection (e.g., 'Sahih Bukhari', 'Sahih Muslim')",
            example="Sahih Bukhari"
        )
    ] = "Sahih Bukhari",
    hadith_no: Annotated[
        Optional[int],
        Query(
            ge=1,
            title="Hadith Number",
            description="Optional specific hadith number to retrieve. Requires chapter_no to be specified.",
            example=1
        )
    ] = None
):
    try:
        hadith_details: list[HadithDetails] = hadith.get_hadiths(
            source_name,
            chapter_no,
            hadith_no,
            session
        )
        
        if not hadith_details:
            detail_msg = f"No hadiths found for source: {source_name}"
            if chapter_no:
                detail_msg += f", chapter: {chapter_no}"
            if hadith_no:
                detail_msg += f", hadith: {hadith_no}"
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=detail_msg
            )
        
        return hadith_details
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error fetching hadiths: {str(e)}"
        )