from typing import List, Optional, Dict, Any
from bson import ObjectId

from app.schemas.question import (
    Question, QuestionCreate, QuestionUpdate, QuestionQuery,
    AnalyzeImageRequest, SummarizeQuestionsRequest, QuestionImportRequest
)
from app.services.base import MongoService
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class QuestionService(MongoService):
    """Serviço para operações CRUD de Question"""
    
    def __init__(self):
        super().__init__("questions")
    
    def get_questions(self, query: QuestionQuery) -> Dict[str, Any]:
        """Obter lista de questões com paginação e filtros"""
        try:
            # Preparar filtros
            filters = {}
            if query.discipline:
                filters["discipline"] = query.discipline.value
            if query.year:
                filters["year"] = query.year
            if query.index:
                filters["index"] = query.index
            
            # Buscar questões
            if query.search:
                # Busca por termo
                search_fields = ["title", "context", "correctAlternative"]
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
                    sort_by="index",
                    sort_order=1,
                    **filters
                )
                
                # Contar total
                total = self.count(**filters)
            
            # Converter para objetos Question
            questions = [Question(**data) for data in questions_data]
            
            return {
                "data": questions,
                "total": total,
                "page": query.page,
                "pageSize": query.pageSize
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter questões: {e}")
            return {
                "data": [],
                "total": 0,
                "page": query.page,
                "pageSize": query.pageSize
            }
    
    def get_question_by_id(self, question_id: str) -> Optional[Question]:
        """Obter questão por ID"""
        data = self.get_by_id(question_id)
        return Question(**data) if data else None
    
    def create_question(self, obj_in: QuestionCreate) -> Optional[Question]:
        """Criar nova questão"""
        try:
            # Converter schema para dict
            question_data = obj_in.model_dump()
            
            # Verificar se já existe questão com mesmo index e year
            existing = self.get_multi(
                limit=1,
                index=question_data["index"],
                year=question_data["year"]
            )
            
            if existing:
                logger.warning(f"Questão já existe: index {question_data['index']}, year {question_data['year']}")
                return None
            
            # Criar questão
            created_data = self.create(question_data)
            return Question(**created_data) if created_data else None
            
        except Exception as e:
            logger.error(f"Erro ao criar questão: {e}")
            return None
    
    def update_question(self, question_id: str, obj_in: QuestionUpdate) -> Optional[Question]:
        """Atualizar questão"""
        try:
            # Converter schema para dict, removendo campos None
            update_data = obj_in.model_dump(exclude_unset=True)
            
            # Atualizar questão
            updated_data = self.update(question_id, update_data)
            return Question(**updated_data) if updated_data else None
            
        except Exception as e:
            logger.error(f"Erro ao atualizar questão {question_id}: {e}")
            return None
    
    def delete_question(self, question_id: str) -> bool:
        """Excluir questão"""
        return self.delete(question_id)
   
    def get_distinct_disciplines(self) -> List[str]:
        """Obter disciplinas distintas"""
        return self.distinct("discipline")
    
    def get_distinct_years(self) -> List[int]:
        """Obter anos distintos"""
        return self.distinct("year")


# Singleton instance
question_service = QuestionService()