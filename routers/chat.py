from datetime import datetime, timezone
from typing import Annotated, List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
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

@router.post("/agent", response_model=MessageResponse)
async def chat_endpoint(
    request: MessageRequest,
    session: SessionDep,
    conversation: ConversationDep,
    agent: AgentDep
):
    """Main chat endpoint"""
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
        
        # Run agent
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
        
        # Save agent execution log
        conversation.save_agent_execution(
            session, conversation_id, assistant_message_id, request.message, result
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
            created_at = datetime.now(timezone.utc)
        )
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        return {"status": "success", "message": "Conversation deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
