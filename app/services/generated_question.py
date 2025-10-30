from typing import List, Optional, Dict, Any
from bson import ObjectId

from app.schemas.generated_question import (
    GeneratedQuestion, GeneratedQuestionCreate, GeneratedQuestionUpdate, 
    GeneratedQuestionQuery
)
from app.services.base import MongoService
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class GeneratedQuestionService(MongoService):
    """Serviço para operações CRUD de GeneratedQuestion"""
    
    def __init__(self):
        super().__init__("generated_questions")
    
    def get_generated_questions(self, query: GeneratedQuestionQuery) -> Dict[str, Any]:
        """Obter lista de questões geradas com paginação e filtros"""
        try:
            # Preparar filtros
            filters = {}
            if query.discipline:
                filters["discipline"] = query.discipline.value
            if query.year:
                filters["year"] = query.year
            if query.user:
                filters["user"] = query.user
            if query.source_question_id:
                filters["source_question_id"] = query.source_question_id
            
            # Buscar questões geradas
            if query.search:
                # Busca por termo
                search_fields = ["title", "context", "rationale"]
                questions_data = self.search(
                    search_term=query.search,
                    search_fields=search_fields,
                    skip=(query.page - 1) * query.pageSize if query.pageSize > 0 else 0,
                    limit=query.pageSize,
                    **filters
                )
                
                # Contar total com busca
                total = len(self.search(
                    search_term=query.search,
                    search_fields=search_fields,
                    skip=0,
                    limit=-1,
                    **filters
                ))
            else:
                # Busca sem termo
                questions_data = self.get_multi(
                    skip=(query.page - 1) * query.pageSize if query.pageSize > 0 else 0,
                    limit=query.pageSize,
                    sort_by="created_at",
                    sort_order=-1,  # Mais recentes primeiro
                    **filters
                )
                
                # Contar total
                total = self.count(**filters)
            
            # Converter para objetos GeneratedQuestion
            questions = [GeneratedQuestion(**data) for data in questions_data]
            
            return {
                "data": questions,
                "total": total,
                "page": query.page,
                "pageSize": query.pageSize
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter questões geradas: {e}")
            return {
                "data": [],
                "total": 0,
                "page": query.page,
                "pageSize": query.pageSize
            }
    
    def get_generated_question_by_id(self, question_id: str) -> Optional[GeneratedQuestion]:
        """Obter questão gerada por ID"""
        data = self.get_by_id(question_id)
        return GeneratedQuestion(**data) if data else None
    
    def create_generated_question(self, obj_in: GeneratedQuestionCreate) -> Optional[GeneratedQuestion]:
        """Criar nova questão gerada"""
        try:
            # Converter schema para dict
            question_data = obj_in.model_dump()
            
            # Criar questão gerada
            created_data = self.create(question_data)
            return GeneratedQuestion(**created_data) if created_data else None
            
        except Exception as e:
            logger.error(f"Erro ao criar questão gerada: {e}")
            return None
    
    def update_generated_question(
        self, question_id: str, obj_in: GeneratedQuestionUpdate
    ) -> Optional[GeneratedQuestion]:
        """Atualizar questão gerada"""
        try:
            # Converter schema para dict, removendo campos None
            update_data = obj_in.model_dump(exclude_unset=True)
            
            # Atualizar questão gerada
            updated_data = self.update(question_id, update_data)
            return GeneratedQuestion(**updated_data) if updated_data else None
            
        except Exception as e:
            logger.error(f"Erro ao atualizar questão gerada {question_id}: {e}")
            return None
    
    def delete_generated_question(self, question_id: str) -> bool:
        """Excluir questão gerada"""
        return self.delete(question_id)
    
    def get_generated_questions_by_user(self, user_id: str, limit: int = 10) -> List[GeneratedQuestion]:
        """Obter questões geradas por usuário"""
        try:
            questions_data = self.get_multi(
                limit=limit,
                sort_by="created_at",
                sort_order=-1,
                user=user_id
            )
            return [GeneratedQuestion(**data) for data in questions_data]
        except Exception as e:
            logger.error(f"Erro ao obter questões geradas por usuário {user_id}: {e}")
            return []
    
    def get_generated_questions_by_source(self, source_question_id: str) -> List[GeneratedQuestion]:
        """Obter questões geradas por questão original"""
        try:
            questions_data = self.get_multi(
                sort_by="created_at",
                sort_order=-1,
                source_question_id=source_question_id
            )
            return [GeneratedQuestion(**data) for data in questions_data]
        except Exception as e:
            logger.error(f"Erro ao obter questões geradas por fonte {source_question_id}: {e}")
            return []


# Singleton instance
generated_question_service = GeneratedQuestionService()