import logging
import uuid
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, delete, select
from starlette import status

from auth.entity import User
from config import database
from chat.entity import Conversation, Message
from chat.model import ChatRequest, ChatResponse
from shared.agent import AgentService
from auth.service import AuthService
from chat.service import ChatService

router = APIRouter(prefix="/chat", tags=["Chatbot Services"])

SessionDep = Annotated[Session, Depends(database.get_db_session)]

user_dep = Depends(AuthService.get_current_user)
UserDep = Annotated[User, user_dep]

ChatDep = Annotated[ChatService, Depends()]

AgentDep = Annotated[AgentService, Depends()]

@router.post("/agent", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: UserDep,
    session: SessionDep,
    agent: AgentDep,
    chat: ChatDep
):
    """Main Agentic chat endpoint"""
    # Create new conversation if not provided or invalid UUID
    if not request.conversation_id:
        conversation_id = chat.create_conversation(user_id=current_user.id, session=session)
    else:
        try:
            # Validate UUID format
            uuid.UUID(request.conversation_id)
            conversation_id = request.conversation_id
        except ValueError:
            # Invalid UUID, create new conversation
            conversation_id = chat.create_conversation(user_id=current_user.id, session=session)
    
    try:
        # Update user profile if location provided
        if request.location:
            agent.user_profile.location = request.location
        if request.timezone:
            agent.user_profile.timezone = request.timezone
        
        # Save user message
        user_message_id = chat.save_message(conversation_id, "user", request.message, metadata=None, session=session)
        
        # Get conversation history for context
        history = chat.get_conversation_history(conversation_id, current_user.id, session=session)
        
        # Agent planning and execution
        agent_result = await agent.plan_and_execute(request.message, history)
        
        # Save agent response with metadata
        bot_message_id = chat.save_message(
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


@router.get("/agent/tools", dependencies=[user_dep])
async def get_available_tools(
    agent: AgentDep
):
    """Get list of available agent tools"""
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
    current_user: UserDep,
    session: SessionDep,
    chat: ChatDep
):
    """Get conversation history"""        
    try:
        statement = select(Conversation).where(Conversation.id == conversation_id and Conversation.user_id == current_user.id)
        # conv_result = supabase.table("conversations").select("*").eq("id", conversation_id).single().execute()
        conversation = session.exec(statement).first()
        
        if not conversation.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
                
        #if current_user.id and conversation["user_id"] and conversation["user_id"] != current_user.id:
        #    raise HTTPException(status_code=403, detail="Access denied to conversation")
        
        messages = chat.get_conversation_history(conversation_id, current_user.id, session)
        
        return {
            "conversation_id": conversation_id,
            "messages": messages,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation")

@router.get("/conversations")
async def get_user_conversations(
    current_user: UserDep,
    session: SessionDep
):
    """Get user's conversation list"""
    try:
        #result = supabase.table("conversations").select("*").eq("user_id", user_id).order("updated_at", desc=True).execute()
        statement = select(Conversation).where(Conversation.user_id == current_user.id).order_by(Conversation.updated_at.desc())
        result = session.exec(statement).all()
        return {"conversations": result}
    except Exception as e:
        print(f"Error getting user conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve conversations")

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: UserDep,
    session: SessionDep
):
    """Delete a conversation"""
    try:
        #conv_result = supabase.table("conversations").select("user_id").eq("id", conversation_id).single().execute()
        statement=select(Conversation).where(Conversation.id == conversation_id and Conversation.user_id == current_user.id)
        conv_result = session.exec(statement).first()
        
        if not conv_result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        
        #supabase.table("messages").delete().eq("conversation_id", conversation_id).execute()
        session.exec(delete(Message).where(Message.conversation_id == conversation_id))
        #supabase.table("conversations").delete().eq("id", conversation_id).execute()
        session.exec(delete(Conversation).where(Conversation.id == conversation_id))
        session.commit()
        
        return {"message": "Conversation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete conversation")
