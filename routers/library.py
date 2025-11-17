from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from config.database import get_db_session
from library.model import CategoryResponse, LibraryResponse
from library.service import LibraryService

router = APIRouter(
    prefix="/library", 
    tags=["Islamic Library"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Access forbidden"}
    }
)

SessionDep = Annotated[Session, Depends(get_db_session)]
LibraryDep = Annotated[LibraryService, Depends()]

@router.get(
    "/categories",
    status_code=status.HTTP_200_OK,
    response_model=list[CategoryResponse],
    summary="Get All Categories",
    description="Retrieve all active categories for Islamic library resources."
)
def get_categories(
    session: SessionDep,
    library: LibraryDep
):
    try:
        categories = library.get_categories(session)
        return categories
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching categories")

@router.get(
    "/items",
    status_code=status.HTTP_200_OK,
    response_model=list[LibraryResponse],
    summary="Get Library Items",
    description="Retrieve Islamic library items, optionally filtered by category."
)
def get_library_items(
    session: SessionDep,
    library: LibraryDep,
    category_id: Annotated[
        Optional[int],
        Query(description="Filter by category ID")
    ] = None
):
    try:
        items = library.get_library_items(session, category_id)
        return items
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching library items")