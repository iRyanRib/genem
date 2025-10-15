from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

from app.services.question import question_service
from app.services.question_topic import question_topic_service
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/disciplines")
async def get_distinct_disciplines() -> Dict[str, Any]:
    """
    Obter disciplinas distintas das questões.
    """
    try:
        disciplines = question_service.get_distinct_disciplines()
        
        return {
            "success": True,
            "data": {
                "items": disciplines,
                "total": len(disciplines)
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter disciplinas distintas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/fields")
async def get_distinct_fields() -> Dict[str, Any]:
    """
    Obter campos distintos dos tópicos.
    """
    try:
        fields = question_topic_service.get_distinct_fields()
        
        return {
            "success": True,
            "data": {
                "items": fields,
                "total": len(fields)
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter campos distintos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/all")
async def get_all_distinct() -> Dict[str, Any]:
    """
    Obter tanto disciplinas quanto campos distintos em uma única requisição.
    """
    try:
        disciplines = question_service.get_distinct_disciplines()
        fields = question_topic_service.get_distinct_fields()
        
        return {
            "success": True,
            "data": {
                "disciplines": {
                    "items": disciplines,
                    "total": len(disciplines)
                },
                "fields": {
                    "items": fields,
                    "total": len(fields)
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter dados distintos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )