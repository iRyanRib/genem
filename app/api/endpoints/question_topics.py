from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.schemas.question_topic import (
    QuestionTopic, QuestionTopicCreate, QuestionTopicUpdate, QuestionTopicQuery,
    QuestionTopicListResponse, QuestionTopicResponse,
    DistinctFieldsResponse, DistinctAreasResponse,
    ClassifyUnusedTopicsRequest, ClassifyUnusedTopicsResponse
)
from app.services.question_topic import question_topic_service
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=QuestionTopicListResponse)
async def get_question_topics(
    page: int = Query(1, ge=1, description="Página"),
    pageSize: int = Query(10, ge=-1, description="Tamanho da página"),
    search: str = Query(None, description="Termo de busca"),
    field: str = Query(None, description="Filtro por campo"),
    area: str = Query(None, description="Filtro por área"),
    field_code: str = Query(None, description="Filtro por código do campo"),
    area_code: str = Query(None, description="Filtro por código da área"),
    general_topic_code: str = Query(None, description="Filtro por código do tópico geral")
) -> QuestionTopicListResponse:
    """
    Obter lista de tópicos com paginação e filtros.
    
    Parâmetros:
    - **page**: Número da página (padrão: 1)
    - **pageSize**: Itens por página (padrão: 10, -1 para todos)
    - **search**: Termo de busca (campo, área, tópico geral, tópico específico)
    - **field**: Filtrar por campo específico
    - **area**: Filtrar por área específica
    - **field_code**: Filtrar por código do campo
    - **area_code**: Filtrar por código da área
    - **general_topic_code**: Filtrar por código do tópico geral
    """
    try:
        query = QuestionTopicQuery(
            page=page,
            pageSize=pageSize,
            search=search,
            field=field,
            area=area,
            field_code=field_code,
            area_code=area_code,
            general_topic_code=general_topic_code
        )
        
        result = question_topic_service.get_question_topics(query)
        
        return QuestionTopicListResponse(
            success=True,
            data=result["data"],
            total=result["total"],
            page=result["page"],
            pageSize=result["pageSize"]
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter tópicos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/{topic_id}", response_model=QuestionTopicResponse)
async def get_topic_by_id(topic_id: str) -> QuestionTopicResponse:
    """
    Obter tópico por ID.
    """
    try:
        topic = question_topic_service.get_topic_by_id(topic_id)
        
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tópico não encontrado com ID: {topic_id}"
            )
        
        return QuestionTopicResponse(success=True, data=topic)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter tópico {topic_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/field/{field_code}", response_model=QuestionTopicListResponse)
async def get_topics_by_field(
    field_code: str,
    page: int = Query(1, ge=1, description="Página"),
    pageSize: int = Query(10, ge=-1, description="Tamanho da página")
) -> QuestionTopicListResponse:
    """
    Obter tópicos por código do campo.
    """
    try:
        result = question_topic_service.get_topics_by_field(field_code, page, pageSize)
        
        return QuestionTopicListResponse(
            success=True,
            data=result["data"],
            total=result["total"],
            page=result["page"],
            pageSize=result["pageSize"]
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter tópicos por campo {field_code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/area/{area_code}", response_model=QuestionTopicListResponse)
async def get_topics_by_area(
    area_code: str,
    page: int = Query(1, ge=1, description="Página"),
    pageSize: int = Query(10, ge=-1, description="Tamanho da página")
) -> QuestionTopicListResponse:
    """
    Obter tópicos por código da área.
    """
    try:
        result = question_topic_service.get_topics_by_area(area_code, page, pageSize)
        
        return QuestionTopicListResponse(
            success=True,
            data=result["data"],
            total=result["total"],
            page=result["page"],
            pageSize=result["pageSize"]
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter tópicos por área {area_code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.post("/", response_model=QuestionTopicResponse)
async def create_topic(topic_in: QuestionTopicCreate) -> QuestionTopicResponse:
    """
    Criar novo tópico.
    """
    try:
        topic = question_topic_service.create_topic(topic_in)
        
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao criar tópico. Tópico específico já pode existir."
            )
        
        return QuestionTopicResponse(success=True, data=topic)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar tópico: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.put("/{topic_id}", response_model=QuestionTopicResponse)
async def update_topic(
    topic_id: str,
    topic_in: QuestionTopicUpdate
) -> QuestionTopicResponse:
    """
    Atualizar tópico existente.
    """
    try:
        # Verificar se tópico existe
        existing_topic = question_topic_service.get_topic_by_id(topic_id)
        if not existing_topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tópico não encontrado com ID: {topic_id}"
            )
        
        updated_topic = question_topic_service.update_topic(topic_id, topic_in)
        
        if not updated_topic:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao atualizar tópico"
            )
        
        return QuestionTopicResponse(success=True, data=updated_topic)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar tópico {topic_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.delete("/{topic_id}")
async def delete_topic(topic_id: str) -> Dict[str, Any]:
    """
    Excluir tópico.
    """
    try:
        # Verificar se tópico existe
        existing_topic = question_topic_service.get_topic_by_id(topic_id)
        if not existing_topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tópico não encontrado com ID: {topic_id}"
            )
        
        success = question_topic_service.delete_topic(topic_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao excluir tópico"
            )
        
        return {
            "success": True,
            "message": f"Tópico {topic_id} excluído com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao excluir tópico {topic_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/distinct/fields", response_model=DistinctFieldsResponse)
async def get_distinct_fields() -> DistinctFieldsResponse:
    """
    Obter campos distintos.
    """
    try:
        fields = question_topic_service.get_distinct_fields()
        
        return DistinctFieldsResponse(
            success=True,
            data=fields,
            total=len(fields)
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter campos distintos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/distinct/areas", response_model=DistinctAreasResponse)
async def get_distinct_areas(
    field_code: str = Query(None, description="Filtrar por código do campo")
) -> DistinctAreasResponse:
    """
    Obter áreas distintas, opcionalmente filtradas por campo.
    """
    try:
        areas = question_topic_service.get_distinct_areas(field_code)
        
        return DistinctAreasResponse(
            success=True,
            data=areas,
            total=len(areas)
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter áreas distintas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/distinct/field-codes")
async def get_distinct_field_codes() -> Dict[str, Any]:
    """
    Obter códigos de campo distintos.
    """
    try:
        field_codes = question_topic_service.get_distinct_field_codes()
        
        return {
            "success": True,
            "data": field_codes,
            "total": len(field_codes)
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter códigos de campo distintos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/distinct/area-codes")
async def get_distinct_area_codes(
    field_code: str = Query(None, description="Filtrar por código do campo")
) -> Dict[str, Any]:
    """
    Obter códigos de área distintos, opcionalmente filtrados por campo.
    """
    try:
        area_codes = question_topic_service.get_distinct_area_codes(field_code)
        
        return {
            "success": True,
            "data": area_codes,
            "total": len(area_codes)
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter códigos de área distintos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/distinct/general-topics")
async def get_distinct_general_topics(
    field_code: str = Query(None, description="Filtrar por código do campo"),
    area_code: str = Query(None, description="Filtrar por código da área")
) -> Dict[str, Any]:
    """
    Obter tópicos gerais distintos, opcionalmente filtrados por campo e/ou área.
    """
    try:
        general_topics = question_topic_service.get_distinct_general_topics(field_code, area_code)
        
        return {
            "success": True,
            "data": general_topics,
            "total": len(general_topics)
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter tópicos gerais distintos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/distinct/general-topic-codes")
async def get_distinct_general_topic_codes(
    field_code: str = Query(None, description="Filtrar por código do campo"),
    area_code: str = Query(None, description="Filtrar por código da área")
) -> Dict[str, Any]:
    """
    Obter códigos de tópicos gerais distintos, opcionalmente filtrados por campo e/ou área.
    """
    try:
        general_topic_codes = question_topic_service.get_distinct_general_topic_codes(field_code, area_code)
        
        return {
            "success": True,
            "data": general_topic_codes,
            "total": len(general_topic_codes)
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter códigos de tópicos gerais distintos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/distinct/specific-topics")
async def get_distinct_specific_topics(
    field_code: str = Query(None, description="Filtrar por código do campo"),
    area_code: str = Query(None, description="Filtrar por código da área"),
    general_topic_code: str = Query(None, description="Filtrar por código do tópico geral")
) -> Dict[str, Any]:
    """
    Obter tópicos específicos distintos, opcionalmente filtrados por campo, área e/ou tópico geral.
    """
    try:
        specific_topics = question_topic_service.get_distinct_specific_topics(
            field_code, area_code, general_topic_code
        )
        
        return {
            "success": True,
            "data": specific_topics,
            "total": len(specific_topics)
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter tópicos específicos distintos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/hierarchy")
async def get_topics_hierarchy(
    field_code: str = Query(None, description="Filtrar por código do campo"),
    area_code: str = Query(None, description="Filtrar por código da área"),
    general_topic_code: str = Query(None, description="Filtrar por código do tópico geral")
) -> Dict[str, Any]:
    """
    Obter hierarquia estruturada de campos, áreas, tópicos gerais e específicos.
    Retorna um objeto com códigos e nomes para facilitar a construção da UI.
    """
    try:
        hierarchy = question_topic_service.get_topics_hierarchy(
            field_code, area_code, general_topic_code
        )
        
        return {
            "success": True,
            "data": hierarchy
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter hierarquia de tópicos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )