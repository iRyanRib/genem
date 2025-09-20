from typing import Any, List, Dict
from datetime import datetime
import uuid
import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.schemas.conversation import (
    OpenConversationRequest,
    OpenConversationResponse, 
    AddMessageRequest,
    AddMessageResponse,
    ConversationHistoryResponse,
    MessageModel
)
from app.services.conversation import conversation_service
from app.core.agent import (
    process_enem_question,
    add_message_to_conversation,
    get_or_create_session
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/open", response_model=OpenConversationResponse)
async def open_conversation(request: OpenConversationRequest) -> OpenConversationResponse:
    """
    Start a new conversation with an ENEM question.
    
    This endpoint:
    1. Receives a question_id
    2. Searches for relevant sources in answers_data collection
    3. Sends the question and sources to the AI agent
    4. Creates a new conversation in MongoDB
    5. Returns the agent's response and conversation details
    """
    logger.info(f"🎯 Iniciando conversa - User: {request.user_id}, Question: {request.question_id}")
    
    try:
        # Generate unique session ID
        session_id = f"session_{uuid.uuid4().hex}"
        logger.info(f"🔗 Sessão gerada: {session_id}")
        
        # Process the ENEM question with the agent (will create ADK session internally)
        agent_result = await process_enem_question(
            question_id=request.question_id,
            user_id=request.user_id,
            session_id=session_id,
            use_structured_output=request.structured_output
        )
        
        # Check if there was an error processing the question
        if "error" in agent_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=agent_result["error"]
            )
        
        # Create initial system message with question context
        question_details = agent_result["question_details"]
        system_message = MessageModel(
            role="system",
            content=f"Iniciada conversa sobre a questão: {question_details.get('title', 'N/A')}",
            timestamp=datetime.utcnow(),
            metadata={
                "question_id": request.question_id,
                "discipline": question_details.get("discipline"),
                "year": question_details.get("year"),
                "sources_count": agent_result["sources_count"]
            }
        )
        
        # Create agent response message
        agent_message = MessageModel(
            role="agent",
            content=agent_result["response"],
            timestamp=datetime.utcnow(),
            metadata={
                "agent_type": "enem_agent",
                "structured_output": request.structured_output,
                "stored_output": agent_result.get("stored_output")
            }
        )
        
        # Generate conversation title from question
        title = question_details.get("title", f"Questão ENEM - {request.question_id}")
        
        # Create conversation in MongoDB
        conversation = await conversation_service.create_conversation(
            session_id=session_id,
            user_id=request.user_id,
            question_id=request.question_id,
            title=title,
            initial_message=system_message
        )
        
        # Add agent response to conversation
        await conversation_service.add_message_to_conversation(
            session_id=session_id,
            message=agent_message
        )
        
        logger.info(f"✅ Conversa criada com sucesso - Session: {session_id}, Sources: {agent_result['sources_count']}")
        
        return OpenConversationResponse(
            session_id=session_id,
            conversation_id=str(conversation.id),
            question_details=question_details,
            agent_response=agent_result["response"],
            sources_count=agent_result["sources_count"],
            created_at=conversation.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao criar conversa - User: {request.user_id}, Question: {request.question_id}, Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.post("/message", response_model=AddMessageResponse)
async def add_message(request: AddMessageRequest) -> AddMessageResponse:
    """
    Add a message to an existing conversation.
    
    This endpoint:
    1. Receives a message for an existing session
    2. Adds the user message to the conversation history
    3. Sends the message to the AI agent with conversation context
    4. Adds the agent response to the conversation
    5. Returns the agent's response
    """
    logger.info(f"💬 Nova mensagem - Session: {request.session_id}, User: {request.user_id}")
    
    try:
        # Check if conversation exists
        conversation = await conversation_service.get_conversation_by_session_id(request.session_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversa não encontrada para session_id: {request.session_id}"
            )
        
        # Verify user owns this conversation
        if conversation.user_id != request.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: você não é o proprietário desta conversa"
            )
        
        # Create user message
        user_message = MessageModel(
            role="user",
            content=request.message,
            timestamp=datetime.utcnow()
        )
        
        # Add user message to conversation
        await conversation_service.add_message_to_conversation(
            session_id=request.session_id,
            message=user_message
        )
        
        # Send message to agent (agent will have access to conversation history through ADK session)
        agent_result = await add_message_to_conversation(
            user_id=request.user_id,
            session_id=request.session_id,
            message=request.message,
            use_structured_output=request.structured_output
        )
        
        # Create agent response message
        agent_message = MessageModel(
            role="agent",
            content=agent_result["response"],
            timestamp=datetime.utcnow(),
            metadata={
                "agent_type": "enem_agent",
                "structured_output": request.structured_output
            }
        )
        
        # Add agent response to conversation
        await conversation_service.add_message_to_conversation(
            session_id=request.session_id,
            message=agent_message
        )
        
        return AddMessageResponse(
            session_id=request.session_id,
            conversation_id=str(conversation.id),
            user_message=request.message,
            agent_response=agent_result["response"],
            timestamp=agent_message.timestamp
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/history/{session_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(session_id: str, user_id: str) -> ConversationHistoryResponse:
    """
    Get the full history of a conversation.
    
    Args:
        session_id: The session ID of the conversation
        user_id: The user ID (for authorization)
    
    Returns:
        Complete conversation history with all messages
    """
    try:
        # Get conversation
        conversation = await conversation_service.get_conversation_by_session_id(session_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversa não encontrada para session_id: {session_id}"
            )
        
        # Verify user owns this conversation
        if conversation.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: você não é o proprietário desta conversa"
            )
        
        return ConversationHistoryResponse(
            conversation_id=str(conversation.id),
            session_id=conversation.session_id,
            question_id=conversation.question_id,
            title=conversation.title,
            messages=conversation.messages,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=len(conversation.messages)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/list/{user_id}")
async def list_user_conversations(user_id: str, limit: int = 50, skip: int = 0) -> Dict[str, Any]:
    """
    List all conversations for a user.
    
    Args:
        user_id: The user ID
        limit: Maximum number of conversations to return (default: 50)
        skip: Number of conversations to skip for pagination (default: 0)
    
    Returns:
        List of user's conversations with summary information
    """
    try:
        conversations = await conversation_service.get_user_conversations(
            user_id=user_id,
            limit=limit,
            skip=skip
        )
        
        # Get user stats
        stats = await conversation_service.get_conversation_stats(user_id)
        
        # Convert conversations to summary format
        conversation_summaries = []
        for conv in conversations:
            summary = {
                "conversation_id": str(conv.id),
                "session_id": conv.session_id,
                "title": conv.title,
                "question_id": conv.question_id,
                "message_count": len(conv.messages),
                "last_message": conv.messages[-1].content[:100] + "..." if conv.messages else None,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at
            }
            conversation_summaries.append(summary)
        
        return {
            "conversations": conversation_summaries,
            "total_count": len(conversation_summaries),
            "stats": stats,
            "pagination": {
                "limit": limit,
                "skip": skip,
                "returned": len(conversation_summaries)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )
