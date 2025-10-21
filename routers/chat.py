import logging
import uuid
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlmodel import Session, select
from starlette import status

from config import database
from entity.chat import Conversation, Message
from model.chat import ChatRequest, ChatResponse
from services.agent_service import AgentService
from services.chat_service import ChatService
from services.user_service import UserService

router = APIRouter(prefix="/chat")

SessionDep = Annotated[Session, Depends(database.get_db_session)]

@router.post("/agent", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session: SessionDep,
    authorization: Annotated[Optional[str], Header()] = None
):
    """Main Agentic chat endpoint"""
    user_id = "51d39d36-bed6-4adf-9ce0-851e17a4e6de" #get_user_from_token(authorization)
    
    chat_service = ChatService()
    # Create new conversation if not provided or invalid UUID
    if not request.conversation_id:
        conversation_id = chat_service.create_conversation(user_id=user_id, session=session)
    else:
        try:
            # Validate UUID format
            uuid.UUID(request.conversation_id)
            conversation_id = request.conversation_id
        except ValueError:
            # Invalid UUID, create new conversation
            conversation_id = chat_service.create_conversation(user_id=user_id, session=session)
    
    try:
        # Initialize agent
        agent = AgentService()
        
        # Update user profile if location provided
        if request.location:
            agent.user_profile.location = request.location
        if request.timezone:
            agent.user_profile.timezone = request.timezone
        
        # Save user message
        user_message_id = chat_service.save_message(conversation_id, "user", request.message, metadata=None, session=session)
        
        # Get conversation history for context
        history = chat_service.get_conversation_history(conversation_id, user_id, session=session)
        
        # Agent planning and execution
        agent_result = await agent.plan_and_execute(request.message, history)
        
        # Save agent response with metadata
        bot_message_id = chat_service.save_message(
            conversation_id, 
            "assistant", 
            agent_result["response"],
            metadata={
                "agent_steps": [step.dict() for step in agent_result["agent_steps"]],
                "tools_used": agent_result["tools_used"]
            },
            session=session
        )
        
        return ChatResponse(
            response=agent_result["response"],
            conversation_id=conversation_id,
            message_id=bot_message_id,
            agent_steps=agent_result["agent_steps"],
            tools_used=agent_result["tools_used"]
        )
        
    except Exception as e:
        logging.error(f"Error in agent chat endpoint: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process agent request")


@router.get("/agent/tools")
async def get_available_tools():
    """Get list of available agent tools"""
    agent = AgentService()
    tools_info = {}
    for name, tool in agent.tools.items():
        tools_info[name] = {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters
        }
    return {"tools": tools_info}


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    session: SessionDep,
    authorization: Optional[str] = Header(None)
):
    """Get conversation history"""
    user_service = UserService()
    user_id = user_service.get_user_from_token(authorization)
        
    chat_service = ChatService()
    
    try:
        statement = select(Conversation).where(Conversation.id == conversation_id)
        # conv_result = supabase.table("conversations").select("*").eq("id", conversation_id).single().execute()
        conv_result = session.exec(statement).first()
        
        if not conv_result.data:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conversation = conv_result.data
        
        if user_id and conversation.get("user_id") and conversation["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Access denied to conversation")
        
        messages = chat_service.get_conversation_history(conversation_id, user_id, session)
        
        return {
            "conversation_id": conversation_id,
            "messages": messages,
            "created_at": conversation["created_at"],
            "updated_at": conversation["updated_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation")

@router.get("/conversations")
async def get_user_conversations(
    session: SessionDep,
    authorization: Optional[str] = Header(None)
):
    """Get user's conversation list"""
    user_service = UserService()
    user_id = user_service.get_user_from_token(authorization)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        #result = supabase.table("conversations").select("*").eq("user_id", user_id).order("updated_at", desc=True).execute()
        statement = select(Conversation).where(Conversation.user_id == user_id).order_by(Conversation.updated_at.desc())
        result = session.exec(statement).all()
        return {"conversations": result.data}
    except Exception as e:
        print(f"Error getting user conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversations")

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    session: SessionDep,
    authorization: Optional[str] = Header(None),
):
    """Delete a conversation"""
    user_service = UserService()
    user_id = user_service.get_user_from_token(authorization)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        #conv_result = supabase.table("conversations").select("user_id").eq("id", conversation_id).single().execute()
        conv_stm=select(Conversation).where(Conversation.id == conversation_id)
        conv_result = session.exec(conv_stm).first()
        
        if not conv_result.data or conv_result.data.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        #supabase.table("messages").delete().eq("conversation_id", conversation_id).execute()
        session.exec(select(Message).where(Message.conversation_id == conversation_id)).delete()
        #supabase.table("conversations").delete().eq("id", conversation_id).execute()
        session.exec(select(Conversation).where(Conversation.id == conversation_id)).delete()
        
        return {"message": "Conversation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete conversation")
