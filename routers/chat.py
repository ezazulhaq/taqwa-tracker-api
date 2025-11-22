from datetime import datetime, timezone
from typing import Annotated, List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlmodel import Session

from chat.agent import IslamicAgent
from config import database
from chat.model import ConversationResponse, MessageRequest, MessageResponse
from auth.service import AuthService
from chat.service import ConversationService

user_dep = Depends(AuthService.get_current_user)
router = APIRouter(
    prefix="/chat", 
    tags=["Chatbot Services"],
    dependencies=[user_dep]
)

SessionDep = Annotated[Session, Depends(database.get_db_session)]

AgentDep = Annotated[IslamicAgent, Depends()]
ConversationDep = Annotated[ConversationService, Depends()]


def save_agent_execution_background(
    session: Session,
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    user_query: str,
    result: dict
):
    """Background task to save agent execution"""
    try:
        conversation_service = ConversationService()
        conversation_service.save_agent_execution(
            session, conversation_id, message_id, user_query, result
        )
    except Exception as e:
        print(f"Error saving agent execution in background: {str(e)}")


@router.post("/agent", response_model=MessageResponse)
async def chat_endpoint(
    request: MessageRequest,
    session: SessionDep,
    conversation: ConversationDep,
    agent: AgentDep,
    background_tasks: BackgroundTasks
):
    """Main chat endpoint with optimized performance"""
    try:
        # Get or create conversation
        conversation_id = conversation.get_or_create_conversation(
            session, request.user_id, request.conversation_id
        )
        
        # Save user message
        conversation.save_message(
            session, conversation_id, "user", request.message
        )
        
        # Get conversation history
        history = conversation.get_conversation_history(session, conversation_id)
        
        # Run agent (this is now much faster with parallel execution)
        result = await agent.chat(request.message, history)
        
        # Save assistant message
        assistant_message_id = conversation.save_message(
            session,
            conversation_id,
            "assistant",
            result["content"],
            metadata={
                "tools_used": result["tools_used"],
                "execution_time_ms": result["execution_time_ms"]
            }
        )
        
        # Save agent execution log in background (non-blocking)
        background_tasks.add_task(
            save_agent_execution_background,
            session,
            conversation_id,
            assistant_message_id,
            request.message,
            result
        )
        
        return MessageResponse(
            conversation_id=conversation_id,
            message_id=assistant_message_id,
            role="assistant",
            content=result["content"],
            metadata={
                "tools_used": result["tools_used"],
                "execution_time_ms": result["execution_time_ms"]
            },
            created_at=datetime.now(timezone.utc)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )


@router.get("/conversations/{user_id}", response_model=List[ConversationResponse])
async def get_user_conversations(
    user_id: uuid.UUID,
    session: SessionDep,
    conversation: ConversationDep
):
    """Get all conversations for a user"""
    try:
        conversations = conversation.get_user_conversations(session, user_id)
        return [ConversationResponse(**conv) for conv in conversations]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: uuid.UUID,
    session: SessionDep,
    conversation: ConversationDep
):
    """Get all messages in a conversation"""
    try:
        return conversation.get_conversation_messages(session, conversation_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: uuid.UUID, 
    user_id: uuid.UUID,
    session: SessionDep,
    conversation: ConversationDep
):
    """Delete a conversation and all its messages"""
    try:
        success = conversation.delete_conversation(session, conversation_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Conversation not found"
            )
        return {"status": "success", "message": "Conversation deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )