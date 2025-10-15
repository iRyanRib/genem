from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.schemas.question import (
    Question, QuestionCreate, QuestionUpdate, QuestionQuery,
    QuestionListResponse, QuestionResponse, QuestionImportResponse,
    AnalyzeImageRequest, SummarizeQuestionsRequest, QuestionImportRequest,
    DisciplineType
)
from app.services.question import question_service
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=QuestionListResponse)
async def get_questions(
    page: int = Query(1, ge=1, description="Página"),
    pageSize: int = Query(10, ge=-1, description="Tamanho da página"),
    search: str = Query(None, description="Termo de busca"),
    index: int = Query(None, gt=0, description="Índice específico"),
    discipline: DisciplineType = Query(None, description="Filtro por disciplina"),
    year: int = Query(None, gt=0, description="Filtro por ano")
) -> QuestionListResponse:
    """
    Obter lista de questões com paginação e filtros.
    
    Parâmetros:
    - **page**: Número da página (padrão: 1)
    - **pageSize**: Itens por página (padrão: 10, -1 para todos)
    - **search**: Termo de busca (título, contexto, alternativa correta)
    - **index**: Filtrar por índice específico
    - **discipline**: Filtrar por disciplina
    - **year**: Filtrar por ano
    """
    try:
        query = QuestionQuery(
            page=page,
            pageSize=pageSize,
            search=search,
            index=index,
            discipline=discipline,
            year=year
        )
        
        result = question_service.get_questions(query)
        
        return QuestionListResponse(
            success=True,
            data=result["data"],
            total=result["total"],
            page=result["page"],
            pageSize=result["pageSize"]
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter questões: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question_by_id(question_id: str) -> QuestionResponse:
    """
    Obter questão por ID.
    """
    try:
        question = question_service.get_question_by_id(question_id)
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Questão não encontrada com ID: {question_id}"
            )
        
        return QuestionResponse(success=True, data=question)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter questão {question_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.post("/", response_model=QuestionResponse)
async def create_question(question_in: QuestionCreate) -> QuestionResponse:
    """
    Criar nova questão.
    """
    try:
        question = question_service.create_question(question_in)
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao criar questão. Questão já pode existir com mesmo índice e ano."
            )
        
        return QuestionResponse(success=True, data=question)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar questão: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: str,
    question_in: QuestionUpdate
) -> QuestionResponse:
    """
    Atualizar questão existente.
    """
    try:
        # Verificar se questão existe
        existing_question = question_service.get_question_by_id(question_id)
        if not existing_question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Questão não encontrada com ID: {question_id}"
            )
        
        updated_question = question_service.update_question(question_id, question_in)
        
        if not updated_question:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao atualizar questão"
            )
        
        return QuestionResponse(success=True, data=updated_question)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar questão {question_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.delete("/{question_id}")
async def delete_question(question_id: str) -> Dict[str, Any]:
    """
    Excluir questão.
    """
    try:
        # Verificar se questão existe
        existing_question = question_service.get_question_by_id(question_id)
        if not existing_question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Questão não encontrada com ID: {question_id}"
            )
        
        success = question_service.delete_question(question_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao excluir questão"
            )
        
        return {
            "success": True,
            "message": f"Questão {question_id} excluída com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao excluir questão {question_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )

@router.get("/distinct/disciplines")
async def get_distinct_disciplines() -> Dict[str, Any]:
    """
    Obter disciplinas distintas.
    """
    try:
        disciplines = question_service.get_distinct_disciplines()
        
        return {
            "success": True,
            "data": disciplines,
            "total": len(disciplines)
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter disciplinas distintas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/distinct/years")
async def get_distinct_years() -> Dict[str, Any]:
    """
    Obter anos distintos.
    """
    try:
        years = question_service.get_distinct_years()
        
        return {
            "success": True,
            "data": sorted(years),
            "total": len(years)
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter anos distintos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )