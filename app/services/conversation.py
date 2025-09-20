from typing import List, Optional, Dict, Any
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv

from app.schemas.conversation import ConversationModel, MessageModel
from app.core.logging_config import get_logger
from app.core.config import settings
from app.utils.serializers import serialize_mongodb_doc

load_dotenv()
logger = get_logger(__name__)

class ConversationService:
    def __init__(self):
        # MongoDB Configuration
        self.connection_string = settings.MONGODB_CONNECTION_STRING
        self.database_name = settings.DATABASE_NAME
        self.conversations_collection = 'conversations'
        
        # MongoDB Client
        logger.info(f"🗄️ Conectando ao MongoDB: {self.database_name}")
        logger.info(f"Connection String: {self.connection_string[:50]}..." if len(self.connection_string) > 50 else self.connection_string)
        self.client = MongoClient(self.connection_string)
        self.db = self.client[self.database_name]
        self.collection = self.db[self.conversations_collection]
        
        # Test connection
        try:
            self.client.admin.command('ping')
            logger.info("✅ Conexão com MongoDB estabelecida com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar com MongoDB: {e}")
            raise
    
    async def create_conversation(
        self, 
        session_id: str, 
        user_id: str, 
        question_id: Optional[str] = None,
        title: Optional[str] = None,
        initial_message: Optional[MessageModel] = None
    ) -> ConversationModel:
        """
        Create a new conversation.
        
        Args:
            session_id: Unique session identifier
            user_id: User identifier
            question_id: Optional ENEM question ID if conversation started from a question
            title: Optional conversation title
            initial_message: Optional initial message to add to conversation
        
        Returns:
            ConversationModel: The created conversation
        """
        messages = []
        if initial_message:
            messages.append(initial_message)
        
        conversation = ConversationModel(
            session_id=session_id,
            user_id=user_id,
            question_id=question_id,
            title=title,
            messages=messages,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Insert into MongoDB
        conversation_dict = conversation.dict(by_alias=True, exclude={"id"})
        result = self.collection.insert_one(conversation_dict)
        conversation.id = result.inserted_id
        
        logger.info(f"📝 Conversa criada - ID: {conversation.id}, Session: {session_id}, User: {user_id}")
        
        return conversation
    
    async def get_conversation_by_session_id(self, session_id: str) -> Optional[ConversationModel]:
        """
        Get conversation by session ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Optional[ConversationModel]: The conversation if found
        """
        doc = self.collection.find_one({"session_id": session_id})
        if doc:
            # Serialize ObjectIds before creating model
            serialized_doc = serialize_mongodb_doc(doc)
            return ConversationModel(**serialized_doc)
        return None
    
    async def get_conversation_by_id(self, conversation_id: str) -> Optional[ConversationModel]:
        """
        Get conversation by MongoDB ObjectId.
        
        Args:
            conversation_id: MongoDB ObjectId as string
            
        Returns:
            Optional[ConversationModel]: The conversation if found
        """
        try:
            doc = self.collection.find_one({"_id": ObjectId(conversation_id)})
            if doc:
                # Serialize ObjectIds before creating model
                serialized_doc = serialize_mongodb_doc(doc)
                return ConversationModel(**serialized_doc)
        except Exception as e:
            logger.error(f"Erro ao buscar conversa por ID {conversation_id}: {e}")
        return None
    
    async def add_message_to_conversation(
        self, 
        session_id: str, 
        message: MessageModel
    ) -> bool:
        """
        Add a message to an existing conversation.
        
        Args:
            session_id: Session identifier
            message: Message to add
            
        Returns:
            bool: True if message was added successfully
        """
        try:
            result = self.collection.update_one(
                {"session_id": session_id},
                {
                    "$push": {"messages": message.dict()},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Erro ao adicionar mensagem à conversa {session_id}: {e}")
            return False
    
    async def get_conversation_history(
        self, 
        session_id: str, 
        limit: Optional[int] = None
    ) -> List[MessageModel]:
        """
        Get conversation message history.
        
        Args:
            session_id: Session identifier
            limit: Optional limit on number of messages to return
            
        Returns:
            List[MessageModel]: List of messages in chronological order
        """
        conversation = await self.get_conversation_by_session_id(session_id)
        if not conversation:
            return []
        
        messages = conversation.messages
        if limit:
            messages = messages[-limit:]  # Get last N messages
        
        return messages
    
    async def get_user_conversations(
        self, 
        user_id: str, 
        limit: int = 50,
        skip: int = 0
    ) -> List[ConversationModel]:
        """
        Get all conversations for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of conversations to return
            skip: Number of conversations to skip (for pagination)
            
        Returns:
            List[ConversationModel]: List of user's conversations
        """
        cursor = self.collection.find(
            {"user_id": user_id, "is_active": True}
        ).sort("updated_at", -1).skip(skip).limit(limit)
        
        conversations = []
        for doc in cursor:
            # Serialize ObjectIds before creating model
            serialized_doc = serialize_mongodb_doc(doc)
            conversations.append(ConversationModel(**serialized_doc))
        
        return conversations
    
    async def update_conversation_title(self, session_id: str, title: str) -> bool:
        """
        Update conversation title.
        
        Args:
            session_id: Session identifier
            title: New title for the conversation
            
        Returns:
            bool: True if title was updated successfully
        """
        try:
            result = self.collection.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "title": title,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Erro ao atualizar título da conversa {session_id}: {e}")
            return False
    
    async def deactivate_conversation(self, session_id: str) -> bool:
        """
        Mark conversation as inactive (soft delete).
        
        Args:
            session_id: Session identifier
            
        Returns:
            bool: True if conversation was deactivated successfully
        """
        try:
            result = self.collection.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "is_active": False,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Erro ao desativar conversa {session_id}: {e}")
            return False
    
    async def get_conversation_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get conversation statistics for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict with conversation statistics
        """
        try:
            pipeline = [
                {"$match": {"user_id": user_id, "is_active": True}},
                {
                    "$group": {
                        "_id": None,
                        "total_conversations": {"$sum": 1},
                        "total_messages": {"$sum": {"$size": "$messages"}},
                        "avg_messages_per_conversation": {"$avg": {"$size": "$messages"}},
                        "last_conversation": {"$max": "$updated_at"}
                    }
                }
            ]
            
            result = list(self.collection.aggregate(pipeline))
            if result:
                stats = result[0]
                del stats["_id"]
                return stats
            else:
                return {
                    "total_conversations": 0,
                    "total_messages": 0,
                    "avg_messages_per_conversation": 0,
                    "last_conversation": None
                }
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas de conversa do usuário {user_id}: {e}")
            return {}
    
    def close_connection(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
    
    def __del__(self):
        """Cleanup when service is destroyed."""
        self.close_connection()


# Global service instance
conversation_service = ConversationService()
