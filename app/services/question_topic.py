from typing import List, Optional, Dict, Any

from app.schemas.question_topic import (
    QuestionTopic, QuestionTopicCreate, QuestionTopicUpdate, QuestionTopicQuery,
    ClassifyUnusedTopicsRequest
)
from app.services.base import MongoService
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class QuestionTopicService(MongoService):
    """Serviço para operações CRUD de QuestionTopic"""
    
    def __init__(self):
        super().__init__("question_topics")
    
    def get_question_topics(self, query: QuestionTopicQuery) -> Dict[str, Any]:
        """Obter lista de tópicos com paginação e filtros"""
        try:
            # Preparar filtros
            filters = {}
            if query.field:
                filters["field"] = {"$regex": query.field, "$options": "i"}
            if query.area:
                filters["area"] = {"$regex": query.area, "$options": "i"}
            if query.field_code:
                filters["field_code"] = query.field_code
            if query.area_code:
                filters["area_code"] = query.area_code
            if query.general_topic_code:
                filters["general_topic_code"] = query.general_topic_code
            
            # Buscar tópicos
            if query.search:
                # Busca por termo
                search_fields = [
                    "field", "area", "general_topic", "specific_topic",
                    "field_code", "area_code", "general_topic_code"
                ]
                topics_data = self.search(
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
                topics_data = self.get_multi(
                    skip=(query.page - 1) * query.pageSize if query.pageSize > 0 else 0,
                    limit=query.pageSize,
                    sort_by="field",
                    sort_order=1,
                    **filters
                )
                
                # Contar total
                total = self.count(**filters)
            
            # Converter para objetos QuestionTopic
            topics = [QuestionTopic(**data) for data in topics_data]
            
            return {
                "data": topics,
                "total": total,
                "page": query.page,
                "pageSize": query.pageSize
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter tópicos: {e}")
            return {
                "data": [],
                "total": 0,
                "page": query.page,
                "pageSize": query.pageSize
            }
    
    def get_topic_by_id(self, topic_id: str) -> Optional[QuestionTopic]:
        """Obter tópico por ID"""
        data = self.get_by_id(topic_id)
        return QuestionTopic(**data) if data else None
    
    def get_topics_by_field(self, field_code: str, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """Obter tópicos por código do campo"""
        try:
            topics_data = self.get_multi(
                skip=(page - 1) * page_size if page_size > 0 else 0,
                limit=page_size,
                sort_by="area",
                sort_order=1,
                field_code=field_code
            )
            
            total = self.count(field_code=field_code)
            topics = [QuestionTopic(**data) for data in topics_data]
            
            return {
                "data": topics,
                "total": total,
                "page": page,
                "pageSize": page_size
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter tópicos por campo {field_code}: {e}")
            return {
                "data": [],
                "total": 0,
                "page": page,
                "pageSize": page_size
            }
    
    def get_topics_by_area(self, area_code: str, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """Obter tópicos por código da área"""
        try:
            topics_data = self.get_multi(
                skip=(page - 1) * page_size if page_size > 0 else 0,
                limit=page_size,
                sort_by="general_topic",
                sort_order=1,
                area_code=area_code
            )
            
            total = self.count(area_code=area_code)
            topics = [QuestionTopic(**data) for data in topics_data]
            
            return {
                "data": topics,
                "total": total,
                "page": page,
                "pageSize": page_size
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter tópicos por área {area_code}: {e}")
            return {
                "data": [],
                "total": 0,
                "page": page,
                "pageSize": page_size
            }
    
    def create_topic(self, obj_in: QuestionTopicCreate) -> Optional[QuestionTopic]:
        """Criar novo tópico"""
        try:
            # Converter schema para dict
            topic_data = obj_in.model_dump()
            
            # Verificar se já existe tópico com mesmo specific_topic
            existing = self.get_multi(
                limit=1,
                specific_topic=topic_data["specific_topic"]
            )
            
            if existing:
                logger.warning(f"Tópico já existe: {topic_data['specific_topic']}")
                return None
            
            # Criar tópico
            created_data = self.create(topic_data)
            return QuestionTopic(**created_data) if created_data else None
            
        except Exception as e:
            logger.error(f"Erro ao criar tópico: {e}")
            return None
    
    def update_topic(self, topic_id: str, obj_in: QuestionTopicUpdate) -> Optional[QuestionTopic]:
        """Atualizar tópico"""
        try:
            # Converter schema para dict, removendo campos None
            update_data = obj_in.model_dump(exclude_unset=True)
            
            # Atualizar tópico
            updated_data = self.update(topic_id, update_data)
            return QuestionTopic(**updated_data) if updated_data else None
            
        except Exception as e:
            logger.error(f"Erro ao atualizar tópico {topic_id}: {e}")
            return None
    
    def delete_topic(self, topic_id: str) -> bool:
        """Excluir tópico"""
        return self.delete(topic_id)
    
    def get_distinct_fields(self) -> List[str]:
        """Obter campos distintos"""
        return self.distinct("field")
    
    def get_distinct_areas(self, field_code: Optional[str] = None) -> List[str]:
        """Obter áreas distintas, opcionalmente filtradas por campo"""
        filters = {}
        if field_code:
            filters["field_code"] = field_code
        
        return self.distinct("area", **filters)
    
    def get_distinct_field_codes(self) -> List[str]:
        """Obter códigos de campo distintos"""
        return self.distinct("field_code")
    
    def get_distinct_area_codes(self, field_code: Optional[str] = None) -> List[str]:
        """Obter códigos de área distintos, opcionalmente filtrados por campo"""
        filters = {}
        if field_code:
            filters["field_code"] = field_code
        
        return self.distinct("area_code", **filters)
    
    def get_distinct_general_topics(self, field_code: Optional[str] = None, area_code: Optional[str] = None) -> List[str]:
        """Obter tópicos gerais distintos, opcionalmente filtrados por campo e/ou área"""
        filters = {}
        if field_code:
            filters["field_code"] = field_code
        if area_code:
            filters["area_code"] = area_code
        
        return self.distinct("general_topic", **filters)
    
    def get_distinct_general_topic_codes(self, field_code: Optional[str] = None, area_code: Optional[str] = None) -> List[str]:
        """Obter códigos de tópicos gerais distintos, opcionalmente filtrados por campo e/ou área"""
        filters = {}
        if field_code:
            filters["field_code"] = field_code
        if area_code:
            filters["area_code"] = area_code
        
        return self.distinct("general_topic_code", **filters)
    
    def get_distinct_specific_topics(
        self, 
        field_code: Optional[str] = None, 
        area_code: Optional[str] = None,
        general_topic_code: Optional[str] = None
    ) -> List[str]:
        """Obter tópicos específicos distintos, opcionalmente filtrados por campo, área e/ou tópico geral"""
        filters = {}
        if field_code:
            filters["field_code"] = field_code
        if area_code:
            filters["area_code"] = area_code
        if general_topic_code:
            filters["general_topic_code"] = general_topic_code
        
        return self.distinct("specific_topic", **filters)
    
    def get_topics_hierarchy(
        self,
        field_code: Optional[str] = None,
        area_code: Optional[str] = None,
        general_topic_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obter hierarquia estruturada de tópicos.
        Retorna campos com seus códigos, áreas com seus códigos, etc.
        """
        filters = {}
        if field_code:
            filters["field_code"] = field_code
        if area_code:
            filters["area_code"] = area_code
        if general_topic_code:
            filters["general_topic_code"] = general_topic_code
        
        # Buscar todos os tópicos com os filtros aplicados
        topics_data = self.get_multi(
            limit=-1,  # Todos os tópicos
            **filters
        )
        
        # Construir hierarquia
        hierarchy = {}
        
        for topic_data in topics_data:
            field = topic_data.get("field")
            field_code_val = topic_data.get("field_code")
            area = topic_data.get("area")
            area_code_val = topic_data.get("area_code")
            general_topic = topic_data.get("general_topic")
            general_topic_code_val = topic_data.get("general_topic_code")
            specific_topic = topic_data.get("specific_topic")
            
            # Inicializar campo se não existir
            if field_code_val not in hierarchy:
                hierarchy[field_code_val] = {
                    "name": field,
                    "code": field_code_val,
                    "areas": {}
                }
            
            # Inicializar área se não existir
            if area_code_val not in hierarchy[field_code_val]["areas"]:
                hierarchy[field_code_val]["areas"][area_code_val] = {
                    "name": area,
                    "code": area_code_val,
                    "general_topics": {}
                }
            
            # Inicializar tópico geral se não existir
            if general_topic_code_val not in hierarchy[field_code_val]["areas"][area_code_val]["general_topics"]:
                hierarchy[field_code_val]["areas"][area_code_val]["general_topics"][general_topic_code_val] = {
                    "name": general_topic,
                    "code": general_topic_code_val,
                    "specific_topics": []
                }
            
            # Adicionar tópico específico se não existir
            specific_topics_list = hierarchy[field_code_val]["areas"][area_code_val]["general_topics"][general_topic_code_val]["specific_topics"]
            if specific_topic not in specific_topics_list:
                specific_topics_list.append(specific_topic)
        
        return hierarchy


# Singleton instance
question_topic_service = QuestionTopicService()