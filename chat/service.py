import uuid

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pinecone import Pinecone
from sqlmodel import Session, select

from chat.model import MessageResponse
from config.pinecone import config as pinecone_config
from config.gemini import config as gemini_config, genai_client
from chat.entity import Conversation, Message, AgentExecution

class EmbeddingService:
    def __init__(self):
        self.client = genai_client
        self.model = gemini_config.embedding_model
        
    async def get_embedding(self, text: str) -> List[float]:
        """Generate embeddings using OpenRouter embedding model"""
        try:
            response = self.client.embed_content(
                model=self.model,
                content=text,
                task_type="retrieval_document"
            )
            
            return response["embedding"]
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            raise

class VectorStoreService:
    def __init__(self):
        self.pc = Pinecone(api_key=pinecone_config.api_key)
        self.embedding_service = EmbeddingService()
        
        # Index mappings
        # All using 768-dimension embeddings
        self.indexes = {
            "quran": self.pc.Index("quran"),
            "hadith": self.pc.Index("hadith"),
            "islam": self.pc.Index("islam")
        }
    
    async def search_quran(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search Quran knowledge base"""
        try:
            embedding = await self.embedding_service.get_embedding(query)
            results = self.indexes["quran"].query(
                vector=embedding,
                top_k=top_k,
                namespace="full_quran",
                include_metadata=True
            )
            return [
                {
                    "text": match.metadata.get("text", ""),
                    "surah": match.metadata.get("surah", ""),
                    "ayah": match.metadata.get("ayah", ""),
                    "score": match.score
                } 
                for match in results.matches
            ]
        except Exception as e:
            print(f"Error searching Quran: {str(e)}")
            return []
    
    async def search_sahih_bukhari(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search Sahih Bukhari hadiths"""
        try:
            embedding = await self.embedding_service.get_embedding(query)
            results = self.indexes["hadith"].query(
                vector=embedding,
                top_k=top_k,
                namespace="sahih_bukhari",
                include_metadata=True
            )
            return [
                {
                    "text": match.metadata.get("text", ""),
                    "reference": match.metadata.get("reference", ""),
                    "score": match.score
                } 
                for match in results.matches
            ]
        except Exception as e:
            print(f"Error searching Sahih Bukhari: {str(e)}")
            return []
    
    async def search_sahih_muslim(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search Sahih Muslim hadiths"""
        try:
            embedding = await self.embedding_service.get_embedding(query)
            results = self.indexes["hadith"].query(
                vector=embedding,
                top_k=top_k,
                namespace="sahih_muslim",
                include_metadata=True
            )
            return [
                {
                    "text": match.metadata.get("text", ""),
                    "reference": match.metadata.get("reference", ""),
                    "score": match.score
                } 
                for match in results.matches
            ]
        except Exception as e:
            print(f"Error searching Sahih Muslim: {str(e)}")
            return []
    
    async def search_riyad_us_saliheen(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search Riyad Us Saliheen"""
        try:
            embedding = await self.embedding_service.get_embedding(query)
            results = self.indexes["hadith"].query(
                vector=embedding,
                top_k=top_k,
                namespace="riyad_us_saliheen",
                include_metadata=True
            )
            return [
                {
                    "text": match.metadata.get("text", ""),
                    "reference": match.metadata.get("reference", ""),
                    "score": match.score
                } 
                for match in results.matches
            ]
        except Exception as e:
            print(f"Error searching Riyad Us Saliheen: {str(e)}")
            return []
    
    async def search_prophet_biography(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search Prophet Muhammad biography"""
        try:
            embedding = await self.embedding_service.get_embedding(query)
            results = self.indexes["islam"].query(
                vector=embedding,
                top_k=top_k,
                namespace="life_of_prophet_muhammad",
                include_metadata=True
            )
            return [
                {
                    "text": match.metadata.get("text", ""),
                    "score": match.score
                } 
                for match in results.matches
            ]
        except Exception as e:
            print(f"Error searching Prophet biography: {str(e)}")
            return []
    
    async def search_islamic_history(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search Islamic history including Shia-Sunni context"""
        try:
            embedding = await self.embedding_service.get_embedding(query)
            results = self.indexes["islam"].query(
                vector=embedding,
                top_k=top_k,
                namespace="shia_sunni",
                include_metadata=True
            )
            return [
                {
                    "text": match.metadata.get("text", ""),
                    "score": match.score
                } 
                for match in results.matches
            ]
        except Exception as e:
            print(f"Error searching Islamic history: {str(e)}")
            return []

class ConversationService:
    
    def get_or_create_conversation(
        self,
        session: Session,
        user_id: uuid.UUID,
        conversation_id: Optional[uuid.UUID] = None
    ) -> uuid.UUID:
        """Get existing conversation or create new one"""
        if conversation_id:
            # Verify conversation exists and belongs to user
            statement = select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
            conversation = session.exec(statement).first()
            if conversation:
                return conversation.id
        
        # Create new conversation
        new_conversation = Conversation(
            user_id=user_id,
            title="Islamic Guidance Chat"
        )
        session.add(new_conversation)
        session.commit()
        session.refresh(new_conversation)
        return new_conversation.id
    
    def get_conversation_history(
        self,
        session: Session,
        conversation_id: uuid.UUID,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """Retrieve recent conversation messages"""
        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = session.exec(statement).all()
        
        # Reverse to get chronological order
        return [
            {"role": msg.role, "content": msg.content} 
            for msg in reversed(messages)
        ]
    
    def save_message(
        self,
        session: Session,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> uuid.UUID:
        """Save a message to database"""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata=metadata
        )
        session.add(message)
        session.commit()
        session.refresh(message)
        
        # Update conversation's updated_at timestamp
        statement = select(Conversation).where(Conversation.id == conversation_id)
        conversation = session.exec(statement).first()
        if conversation:
            conversation.updated_at = datetime.now(timezone.utc)
            session.add(conversation)
            session.commit()
        
        return message.id
    
    def save_agent_execution(
        self,
        session: Session,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
        user_query: str,
        execution_result: Dict[str, Any]
    ):
        """Save agent execution log"""
        agent_execution = AgentExecution(
            conversation_id=conversation_id,
            message_id=message_id,
            user_query=user_query,
            execution_plan={},
            steps_executed=execution_result.get("steps_executed", []),
            tools_used=execution_result.get("tools_used", []),
            execution_time_ms=execution_result.get("execution_time_ms"),
            success=execution_result.get("success", True),
            error_message=execution_result.get("error_message")
        )
        session.add(agent_execution)
        session.commit()
    
    def get_user_conversations(
        self,
        session: Session,
        user_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Get all conversations for a user with message counts"""
        from sqlalchemy import func
        
        # Query conversations with message count
        statement = (
            select(
                Conversation,
                func.count(Message.id).label("message_count"),
                func.max(Message.created_at).label("last_message_at")
            )
            .outerjoin(Message, Message.conversation_id == Conversation.id)
            .where(Conversation.user_id == user_id)
            .group_by(Conversation.id)
            .order_by(Conversation.updated_at.desc())
        )
        
        results = session.exec(statement).all()
        
        conversations = []
        for conv, msg_count, last_msg_at in results:
            conversations.append({
                "id": conv.id,
                "user_id": conv.user_id,
                "title": conv.title,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at,
                "message_count": msg_count or 0,
                "last_message_at": last_msg_at
            })
        
        return conversations
    
    def get_conversation_messages(
        self,
        session: Session,
        conversation_id: uuid.UUID
    ) -> List[MessageResponse]:
        """Get all messages in a conversation"""
        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        messages = session.exec(statement).all()
        return [
            MessageResponse(
                conversation_id=msg.conversation_id,
                message_id=msg.id,
                role=msg.role,
                content=msg.content,
                metadata=msg.message_metadata or {},
                created_at=msg.created_at
            )
            for msg in messages
        ]
    
    def delete_conversation(
        self,
        session: Session,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        """Delete a conversation and all its messages"""
        # Verify ownership
        statement = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        )
        conversation = session.exec(statement).first()
        
        if not conversation:
            return False
        
        # Delete agent executions
        statement = select(AgentExecution).where(
            AgentExecution.conversation_id == conversation_id
        )
        executions = session.exec(statement).all()
        for execution in executions:
            session.delete(execution)
        
        # Delete messages
        statement = select(Message).where(Message.conversation_id == conversation_id)
        messages = session.exec(statement).all()
        for message in messages:
            session.delete(message)
        
        # Delete conversation
        session.delete(conversation)
        session.commit()
        
        return True
