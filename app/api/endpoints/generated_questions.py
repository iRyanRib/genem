from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.generated_question import (
    GeneratedQuestion, GeneratedQuestionCreate, GeneratedQuestionUpdate,
    GeneratedQuestionQuery, GeneratedQuestionListResponse,
    GeneratedQuestionResponse, GenerateQuestionRequest,
    GenerateQuestionResponse
)
from app.services.generated_question import generated_question_service
from app.services.question import question_service
from app.core.question_generator import get_question_generator
from app.core.groq_token_manager import get_groq_token_stats
from app.api.dependencies.auth import get_current_user
from app.schemas.user import User
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=GeneratedQuestionListResponse,
    summary="Listar questões geradas",
    description="Retorna lista paginada de questões geradas com filtros opcionais"
)
async def get_generated_questions(
    query: GeneratedQuestionQuery = Depends(),
    current_user: User = Depends(get_current_user)
):
    """Listar questões geradas"""
    try:
        result = generated_question_service.get_generated_questions(query)
        return GeneratedQuestionListResponse(**result)
    except Exception as e:
        logger.error(f"Erro ao listar questões geradas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.get(
    "/{question_id}",
    response_model=GeneratedQuestionResponse,
    summary="Obter questão gerada por ID",
    description="Retorna uma questão gerada específica pelo ID"
)
async def get_generated_question(
    question_id: str,
    current_user: User = Depends(get_current_user)
):
    """Obter questão gerada por ID"""
    question = generated_question_service.get_generated_question_by_id(question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Questão gerada não encontrada"
        )
    
    return GeneratedQuestionResponse(data=question)


@router.post(
    "/generate",
    response_model=GenerateQuestionResponse,
    summary="Gerar nova questão",
    description="Gera uma nova questão baseada em uma questão existente usando IA"
)
async def generate_question(
    request: GenerateQuestionRequest,
    current_user: User = Depends(get_current_user)
):
    """Gerar nova questão baseada em questão existente"""
    try:
        # Buscar questão original
        source_question = question_service.get_question_by_id(request.question_id)
        if not source_question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Questão base não encontrada"
            )
        
        # Buscar questões similares pelos mesmos tópicos
        similar_questions = []
        if source_question.questionTopics:
            # Buscar outras questões com os mesmos tópicos
            from app.services.base import MongoService
            mongo_service = MongoService("questions")
            
            # Buscar questões que compartilham pelo menos um tópico
            similar_questions_data = mongo_service.get_multi(
                limit=5,
                questionTopics={"$in": source_question.questionTopics},
                _id={"$ne": source_question.id}  # Excluir a questão original
            )
            
            from app.schemas.question import Question
            similar_questions = [Question(**data) for data in similar_questions_data]
        
        logger.info(f"Iniciando geração de questão baseada em: {source_question.id}")
        logger.info(f"Encontradas {len(similar_questions)} questões similares")
        
        # Gerar nova questão usando o agente LangGraph
        question_generator_instance = get_question_generator()
        generation_result = await question_generator_instance.generate_question(
            source_question=source_question,
            similar_questions=similar_questions,
            user_id=current_user.id,
            max_refinements=3
        )
        
        if not generation_result["success"]:
            logger.error(f"Erro na geração: {generation_result['error']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro na geração da questão: {generation_result['error']}"
            )
        
        generated_question_create = generation_result["generated_question"]
        
        # Salvar questão gerada no banco
        created_question = generated_question_service.create_generated_question(
            generated_question_create
        )
        
        if not created_question:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao salvar questão gerada"
            )
        
        logger.info(f"Questão gerada e salva com sucesso: {created_question.id}")
        
        return GenerateQuestionResponse(
            data=created_question,
            message=f"Questão gerada com sucesso após {generation_result.get('refinement_count', 0)} refinamentos"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado na geração de questão: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno na geração da questão"
        )


@router.post(
    "/",
    response_model=GeneratedQuestionResponse,
    summary="Criar questão gerada manualmente",
    description="Cria uma nova questão gerada manualmente (não pela IA)"
)
async def create_generated_question(
    question: GeneratedQuestionCreate,
    current_user: User = Depends(get_current_user)
):
    """Criar questão gerada manualmente"""
    try:
        # Definir o usuário como o atual
        question.user = current_user.id
        
        created_question = generated_question_service.create_generated_question(question)
        if not created_question:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao criar questão gerada"
            )
        
        return GeneratedQuestionResponse(data=created_question)
        
    except Exception as e:
        logger.error(f"Erro ao criar questão gerada: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.put(
    "/{question_id}",
    response_model=GeneratedQuestionResponse,
    summary="Atualizar questão gerada",
    description="Atualiza uma questão gerada existente"
)
async def update_generated_question(
    question_id: str,
    question_update: GeneratedQuestionUpdate,
    current_user: User = Depends(get_current_user)
):
    """Atualizar questão gerada"""
    # Verificar se a questão existe
    existing_question = generated_question_service.get_generated_question_by_id(question_id)
    if not existing_question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Questão gerada não encontrada"
        )
    
    # Verificar se o usuário é o dono da questão
    if existing_question.user != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para editar esta questão"
        )
    
    updated_question = generated_question_service.update_generated_question(
        question_id, question_update
    )
    
    if not updated_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao atualizar questão gerada"
        )
    
    return GeneratedQuestionResponse(data=updated_question)


@router.delete(
    "/{question_id}",
    summary="Excluir questão gerada",
    description="Exclui uma questão gerada"
)
async def delete_generated_question(
    question_id: str,
    current_user: User = Depends(get_current_user)
):
    """Excluir questão gerada"""
    # Verificar se a questão existe
    existing_question = generated_question_service.get_generated_question_by_id(question_id)
    if not existing_question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Questão gerada não encontrada"
        )
    
    # Verificar se o usuário é o dono da questão
    if existing_question.user != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para excluir esta questão"
        )
    
    success = generated_question_service.delete_generated_question(question_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao excluir questão gerada"
        )
    
    return {"message": "Questão gerada excluída com sucesso"}


@router.get(
    "/user/my-questions",
    response_model=GeneratedQuestionListResponse,
    summary="Minhas questões geradas",
    description="Retorna as questões geradas pelo usuário atual"
)
async def get_my_generated_questions(
    page: int = 1,
    page_size: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Obter questões geradas pelo usuário atual"""
    query = GeneratedQuestionQuery(
        page=page,
        pageSize=page_size,
        user=current_user.id
    )
    
    result = generated_question_service.get_generated_questions(query)
    return GeneratedQuestionListResponse(**result)


@router.get(
    "/source/{source_question_id}",
    response_model=GeneratedQuestionListResponse,
    summary="Questões geradas por fonte",
    description="Retorna todas as questões geradas baseadas em uma questão específica"
)
async def get_generated_questions_by_source(
    source_question_id: str,
    current_user: User = Depends(get_current_user)
):
    """Obter questões geradas baseadas em uma questão específica"""
    questions = generated_question_service.get_generated_questions_by_source(source_question_id)
    
    return GeneratedQuestionListResponse(
        data=questions,
        total=len(questions),
        page=1,
        pageSize=len(questions)
    )


@router.get(
    "/system/token-stats",
    summary="Estatísticas dos tokens GROQ",
    description="Retorna estatísticas de uso dos tokens GROQ"
)
async def get_token_stats(
    current_user: User = Depends(get_current_user)
):
    """Obter estatísticas de uso dos tokens GROQ"""
    try:
        stats = get_groq_token_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas dos tokens: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao obter estatísticas dos tokens"
        )