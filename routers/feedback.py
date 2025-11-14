from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session
from config import database
from feedback.model import FeedbackRequest, FeedbackResponse
from feedback.service import FeedbackService
from shared.security import SecurityService

router = APIRouter(prefix="/support", tags=["Support Services"])

SessionDep = Annotated[Session, Depends(database.get_db_session)]
SecurityDep = Annotated[SecurityService, Depends()]
FeedbackDep = Annotated[FeedbackService, Depends()]

@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    session: SessionDep,
    feedback: FeedbackDep,
    rate_limit: SecurityDep,
    request: Request,
    feedback_request: FeedbackRequest
    ):
    """Submit user feedback"""
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limit.check_rate_limit(f"signup_{client_ip}", max_requests=3):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many signup attempts. Please try again later."
        )
    
    try:
        return await feedback.create_feedback(feedback_request, session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")