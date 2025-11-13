from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from config import database
from feedback.model import FeedbackRequest, FeedbackResponse
from feedback.service import FeedbackService

router = APIRouter(prefix="/support", tags=["Support Services"])

SessionDep = Annotated[Session, Depends(database.get_db_session)]

FeedbackDep = Annotated[FeedbackService, Depends()]

@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    session: SessionDep,
    feedback: FeedbackDep,
    feedback_request: FeedbackRequest
    ):
    """Submit user feedback"""
    try:
        return await feedback.create_feedback(feedback_request, session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")