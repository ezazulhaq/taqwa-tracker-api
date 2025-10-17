import logging
import uuid
from typing import Annotated, Optional
from fastapi import FastAPI, HTTPException, Header, Depends, status
from sqlmodel import Session, text
from model.chat import ChatRequest, ChatResponse
from services.agent_service import AgentService
from services.chat_service import ChatService
from config.database import get_db_session
from routers import quran

SessionDep = Annotated[Session, Depends(get_db_session)]

app = FastAPI()

app.include_router(quran.router)

@app.get("/")
async def status_check():
    return {"status": "OK"}

@app.get("/health/db")
def test_db_connection(session: SessionDep):
    try:
        session.exec(text("SELECT 1"))
        return {"status": "OK", "message": "Database connection successful ✅"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database connection failed: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
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
        raise HTTPException(status_code=500, detail="Failed to process agent request")
