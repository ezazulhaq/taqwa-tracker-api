import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import HTTPException
from sqlmodel import Session, insert, select, update

from chat.entity import Conversation, Message


class ChatService:
    
    def create_conversation(self, user_id: Optional[str] = None, session: Session = None) -> str:
        """Create a new conversation"""
        if not session:
            raise ValueError("Database session is required")
            
        try:
            conversation_id = str(uuid.uuid4())
            conversation_data = {
                "id": conversation_id,
                "user_id": user_id,
                "title": "Islamic AI Agent Chat",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            statement = insert(Conversation).values(**conversation_data)
            session.exec(statement)
            session.commit()
            
            return conversation_id
        except Exception as e:
            session.rollback()
            logging.error(f"Error creating conversation for user {user_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to create conversation")

    def save_message(self, conversation_id: str, role: str, content: str, metadata: Dict = None, session: Session = None) -> str:
        """Save a message with optional metadata"""
        if not session:
            raise ValueError("Database session is required")
        if not conversation_id or not role or not content:
            raise ValueError("conversation_id, role, and content are required")
            
        try:
            message_id = str(uuid.uuid4())
            message_data = {
                "id": message_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "message_metadata": metadata if metadata else None,
                "created_at": datetime.now(timezone.utc)
            }
            statement = insert(Message).values(**message_data)
            session.exec(statement)
            
            # Update conversation timestamp
            update_stmt = update(Conversation).where(
                Conversation.id == conversation_id
                ).values(
                    updated_at=datetime.now(timezone.utc)
                    )
            session.exec(update_stmt)
            session.commit()
            
            return message_id
        except Exception as e:
            session.rollback()
            logging.error(f"Error saving message for conversation {conversation_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to save message")

    def get_conversation_history(self, conversation_id: str, user_id: Optional[str] = None, session: Session = None) -> List[Message]:
        """Get conversation history"""
        if not session:
            raise ValueError("Database session is required")
        if not conversation_id:
            raise ValueError("conversation_id is required")
            
        try:
            # If user is authenticated, verify they own the conversation
            if user_id:
                conv_stmt = select(Conversation).where(
                    (Conversation.id == conversation_id) & (Conversation.user_id == user_id)
                )
                conv_result = session.exec(conv_stmt).first()
                if not conv_result:
                    raise HTTPException(status_code=403, detail="Access denied to conversation")
            
            statement = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)            
            messages = session.exec(statement).all()
            return messages
        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"Error getting conversation history for {conversation_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to retrieve conversation history")