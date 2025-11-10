from typing import Any, List, Dict, Optional, Annotated
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Query, Depends
from fastapi.responses import JSONResponse

from app.api.dependencies.auth import get_current_active_user
from app.schemas.user import User
from app.schemas.exam import (
    ExamCreate, ExamUpdate, ExamFinalize, ExamResponse,
    ExamForUser, ExamDetails, ExamSummary
)
from app.services.exam import exam_service
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/create", response_model=ExamResponse)
async def create_exam(
    exam_data: ExamCreate,
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> ExamResponse:
    """
    Criar um novo exame.
    
    O usuário pode passar:
    - topics: lista de tópicos específicos (filtra pelo array questionTopics)
    - years: lista de anos das questões
    - question_count: quantidade de questões (padrão: 25, máximo: 100)
    - exam_replic_id: ID do exame para replicar questões exatas
    
    Se nenhum filtro for passado, seleciona questões aleatórias do banco.
    A seleção é otimizada e feita diretamente no MongoDB usando agregação.
    """
    logger.info(f"📨 Request de criação de exame recebido")
    logger.info(f"📋 ExamData raw: topics={exam_data.topics}, years={exam_data.years}, disciplines={exam_data.disciplines}, count={exam_data.question_count}")
    logger.info(f"🔄 ExamReplicId recebido: {exam_data.exam_replic_id}")
    logger.info(f"📝 ExamData dict: {exam_data.model_dump()}")
    logger.info(f"🔍 HasAttr exam_replic_id: {hasattr(exam_data, 'exam_replic_id')}")
    
    # Criar novo objeto com user_id do token
    exam_create_data = ExamCreate(
        user_id=current_user.id,
        topics=exam_data.topics,
        exam_replic_id=exam_data.exam_replic_id,
        years=exam_data.years,
        disciplines=exam_data.disciplines,
        question_count=exam_data.question_count
    )
    
    logger.info(f"🎯 Criando exame - User: {exam_create_data.user_id}, Questões: {exam_create_data.question_count}")
    logger.info(f"🔄 ExamReplicId processado: {exam_create_data.exam_replic_id}")
    logger.info(f"📝 ExamCreateData dict: {exam_create_data.model_dump()}")
    
    try:
        exam = exam_service.create_exam(exam_create_data)
        
        return ExamResponse(
            exam_id=exam.id,
            status=exam.status,
            message=f"Exame criado com sucesso com {exam.total_questions} questões"
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar exame - User: {exam_create_data.user_id}, Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/{exam_id}", response_model=ExamForUser)
async def get_exam(
    exam_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> ExamForUser:
    """
    Obter exame por ID para responder.
    
    Retorna as questões sem o gabarito, apenas com:
    - year, discipline, context, alternativesIntroduction
    - alternatives (sem isCorrect)
    
    Args:
        exam_id: ID do exame
    """
    user_id = current_user.id
    logger.info(f"📖 Buscando exame - ID: {exam_id}, User: {user_id}")
    
    try:
        exam = exam_service.get_exam_for_user(exam_id, user_id)
        
        if not exam:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exame não encontrado ou você não tem acesso a ele"
            )
        
        return exam
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao buscar exame - ID: {exam_id}, User: {user_id}, Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/{exam_id}/details", response_model=ExamDetails)
async def get_exam_details(
    exam_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> ExamDetails:
    """
    Obter exame com detalhes completos.
    
    Retorna questões + respostas do usuário + gabarito + isCorrect.
    Útil para revisar o exame após finalização.
    
    Args:
        exam_id: ID do exame
    """
    user_id = current_user.id
    logger.info(f"🔍 Buscando detalhes do exame - ID: {exam_id}, User: {user_id}")
    
    try:
        exam_details = exam_service.get_exam_details(exam_id, user_id)
        
        if not exam_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exame não encontrado ou você não tem acesso a ele"
            )
        
        return exam_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao buscar detalhes do exame - ID: {exam_id}, User: {user_id}, Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.patch("/{exam_id}/answer", response_model=ExamResponse)
async def update_answer(
    exam_id: str,
    update_data: ExamUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> ExamResponse:
    """
    Salvar resposta do usuário para uma questão.
    
    Esta rota:
    1. Recebe questionId + userAnswer
    2. Atualiza os campos updatedAt e isCorrect
    3. Muda status para "in_progress" se for a primeira resposta
    
    Args:
        exam_id: ID do exame
        update_data: dados da resposta (question_id + user_answer)
    """
    user_id = current_user.id
    logger.info(f"📝 Atualizando resposta - Exame: {exam_id}, User: {user_id}, Questão: {update_data.question_id}")
    
    try:
        exam = exam_service.update_answer(exam_id, user_id, update_data)
        
        if not exam:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exame não encontrado ou você não tem acesso a ele"
            )
        
        return ExamResponse(
            exam_id=exam.id,
            status=exam.status,
            message=f"Resposta salva para a questão {update_data.question_id}"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar resposta - Exame: {exam_id}, User: {user_id}, Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.post("/{exam_id}/finalize", response_model=ExamResponse)
async def finalize_exam(
    exam_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> ExamResponse:
    """
    Finalizar exame e calcular métricas.
    
    Esta rota:
    1. Verifica se todas as questões foram respondidas
    2. Calcula total_correct_answers e total_wrong_answers
    3. Atualiza status para "finished"
    4. Define finished_at timestamp
    
    Só é possível finalizar com todas as respostas feitas.
    
    Args:
        exam_id: ID do exame
    """
    user_id = current_user.id
    logger.info(f"🏁 Finalizando exame - ID: {exam_id}, User: {user_id}")
    
    try:
        exam = exam_service.finalize_exam(exam_id, user_id)
        
        if not exam:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exame não encontrado ou você não tem acesso a ele"
            )
        
        return ExamResponse(
            exam_id=exam.id,
            status=exam.status,
            message=f"Exame finalizado! Você acertou {exam.total_correct_answers} de {exam.total_questions} questões"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao finalizar exame - ID: {exam_id}, User: {user_id}, Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.delete("/{exam_id}")
async def delete_exam(
    exam_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> Dict[str, Any]:
    """
    Deletar exame.
    
    Args:
        exam_id: ID do exame
    """
    user_id = current_user.id
    logger.info(f"🗑️ Deletando exame - ID: {exam_id}, User: {user_id}")
    
    try:
        success = exam_service.delete_exam(exam_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exame não encontrado ou você não tem acesso a ele"
            )
        
        return {
            "message": "Exame deletado com sucesso",
            "exam_id": exam_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao deletar exame - ID: {exam_id}, User: {user_id}, Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/user/me", response_model=Dict[str, Any])
async def list_user_exams(
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = Query(0, ge=0, description="Número de exames a pular"),
    limit: int = Query(50, ge=1, le=100, description="Limite de exames por página"),
    status: Optional[str] = Query(None, description="Filtrar por status do exame (not_started, in_progress, finished)"),
    created_after: Optional[str] = Query(None, description="Filtrar exames criados após esta data (ISO 8601: YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS)"),
    created_before: Optional[str] = Query(None, description="Filtrar exames criados antes desta data (ISO 8601: YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS)")
) -> Dict[str, Any]:
    """
    Listar todos os exames do usuário autenticado com filtros de data e status.
    
    Args:
        skip: Número de exames a pular para paginação
        limit: Limite de exames por página (máximo 100)
        status: Status do exame (not_started, in_progress, finished)
        created_after: Data mínima de criação (ISO 8601)
        created_before: Data máxima de criação (ISO 8601)
    
    Returns:
        Lista de exames do usuário com informações resumidas
    """
    user_id = current_user.id
    logger.info(f"📋 Listando exames - User: {user_id}, Skip: {skip}, Limit: {limit}, Status: {status}, After: {created_after}, Before: {created_before}")
    
    try:
        # Processar filtros de data
        date_filters = {}
        
        if created_after:
            try:
                # Tentar parsear data ISO
                if 'T' in created_after:
                    parsed_date = datetime.fromisoformat(created_after.replace('Z', '+00:00'))
                else:
                    parsed_date = datetime.fromisoformat(created_after + 'T00:00:00')
                date_filters['created_after'] = parsed_date
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Data 'created_after' inválida: {created_after}. Use formato ISO 8601 (YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS)"
                )
        
        if created_before:
            try:
                # Tentar parsear data ISO  
                if 'T' in created_before:
                    parsed_date = datetime.fromisoformat(created_before.replace('Z', '+00:00'))
                else:
                    parsed_date = datetime.fromisoformat(created_before + 'T23:59:59')
                date_filters['created_before'] = parsed_date
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Data 'created_before' inválida: {created_before}. Use formato ISO 8601 (YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS)"
                )
        
        # Validar status se fornecido
        valid_statuses = ["not_started", "in_progress", "finished"]
        if status and status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Status inválido: {status}. Use um dos valores: {', '.join(valid_statuses)}"
            )
        
        # Preparar todos os filtros
        filters = {**date_filters}
        if status:
            filters['status'] = status
        
        # Buscar exames com todos os filtros
        exams = exam_service.get_user_exams(user_id, skip, limit, **filters)
        
        # Calcular estatísticas básicas APENAS da página atual (não todo o histórico)
        total_exams = exam_service.count_user_exams(user_id, **filters)
        finished_exams = [e for e in exams if e.status == "finished"]
        total_questions_answered = sum(e.total_questions for e in finished_exams)
        total_correct = sum(e.total_correct_answers for e in finished_exams)
        
        return {
            "exams": exams,
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total_exams,
                "returned": len(exams)
            },
            "stats": {
                "total_exams": total_exams,
                "finished_exams": len(finished_exams),
                "total_questions_answered": total_questions_answered,
                "total_correct_answers": total_correct,
                "average_score": round(total_correct / total_questions_answered * 100, 1) if total_questions_answered > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar exames - User: {user_id}, Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/totalizers/me", response_model=Dict[str, Any])
async def get_user_totalizers(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> Dict[str, Any]:
    """
    Obter totalizadores/estatísticas completas de todos os exames do usuário autenticado.
    
    Esta rota retorna métricas agregadas considerando TODOS os exames do usuário,
    independente de paginação. Útil para dashboards e visão geral de desempenho.
    
    Returns:
        Estatísticas completas do usuário:
        - total_exams: Total de exames criados
        - finished_exams: Exames finalizados
        - in_progress_exams: Exames em progresso
        - not_started_exams: Exames não iniciados
        - total_questions_answered: Total de questões respondidas
        - total_correct_answers: Total de acertos
        - total_wrong_answers: Total de erros
        - average_score: Média geral de acerto (%)
    """
    user_id = current_user.id
    logger.info(f"📊 Buscando totalizadores - User: {user_id}")
    
    try:
        totalizers = exam_service.get_user_totalizers(user_id)
        return totalizers
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar totalizadores - User: {user_id}, Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )