from typing import List, Optional, Dict, Any, Type, TypeVar
from pymongo import MongoClient
from bson import ObjectId
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# TypeVar para schemas Pydantic
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ModelType = TypeVar("ModelType", bound=BaseModel)


class MongoService:
    """Serviço base para operações com MongoDB"""
    
    def __init__(self, collection_name: str):
        """Inicializar serviço MongoDB
        
        Args:
            collection_name: Nome da coleção no MongoDB
        """
        self.collection_name = collection_name
        self._client = None
        self._db = None
        self._collection = None
        
    def _get_collection(self):
        """Obter conexão com a coleção do MongoDB"""
        if self._collection is None:
            if not settings.MONGODB_CONNECTION_STRING:
                raise ValueError("MONGODB_CONNECTION_STRING não configurada")
            if not settings.DATABASE_NAME:
                raise ValueError("DATABASE_NAME não configurado")
                
            self._client = MongoClient(settings.MONGODB_CONNECTION_STRING)
            self._db = self._client[settings.DATABASE_NAME]
            self._collection = self._db[self.collection_name]
            
            # Testar conexão
            try:
                self._client.admin.command('ping')
                logger.info(f"✅ Conectado ao MongoDB: {settings.DATABASE_NAME}.{self.collection_name}")
            except Exception as e:
                logger.error(f"❌ Erro ao conectar com MongoDB: {e}")
                raise
                
        return self._collection
    
    def _object_id_to_str(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Converter ObjectId para string recursivamente"""
        if not doc:
            return doc
            
        # Converter _id principal
        if "_id" in doc:
            doc["id"] = str(doc["_id"])
            del doc["_id"]
        
        # Converter ObjectIds em todos os campos recursivamente
        for key, value in list(doc.items()):
            if isinstance(value, ObjectId):
                doc[key] = str(value)
            elif isinstance(value, list):
                new_list = []
                for item in value:
                    if isinstance(item, ObjectId):
                        new_list.append(str(item))
                    elif isinstance(item, dict):
                        new_list.append(self._object_id_to_str(item))
                    else:
                        new_list.append(item)
                doc[key] = new_list
            elif isinstance(value, dict):
                # Recursivamente processar dicionários aninhados
                doc[key] = self._object_id_to_str(value)
                
        return doc
    
    def _prepare_filter(self, **filters) -> Dict[str, Any]:
        """Preparar filtros para consulta MongoDB"""
        mongo_filter = {}
        for key, value in filters.items():
            if value is not None:
                if key == "id":
                    mongo_filter["_id"] = ObjectId(value)
                else:
                    mongo_filter[key] = value
        return mongo_filter
    
    def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Obter documento por ID"""
        try:
            collection = self._get_collection()
            doc = collection.find_one({"_id": ObjectId(id)})
            return self._object_id_to_str(doc) if doc else None
        except Exception as e:
            logger.error(f"Erro ao buscar documento por ID {id}: {e}")
            return None
    
    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "_id",
        sort_order: int = 1,
        **filters
    ) -> List[Dict[str, Any]]:
        """Obter múltiplos documentos"""
        try:
            collection = self._get_collection()
            mongo_filter = self._prepare_filter(**filters)
            
            cursor = collection.find(mongo_filter)
            
            # Aplicar ordenação
            cursor = cursor.sort(sort_by, sort_order)
            
            # Aplicar paginação
            if limit > 0:
                cursor = cursor.skip(skip).limit(limit)
            elif limit == -1:
                cursor = cursor.skip(skip)  # Sem limite
            
            docs = list(cursor)
            return [self._object_id_to_str(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Erro ao buscar documentos: {e}")
            return []
    
    def count(self, **filters) -> int:
        """Contar documentos"""
        try:
            collection = self._get_collection()
            mongo_filter = self._prepare_filter(**filters)
            return collection.count_documents(mongo_filter)
        except Exception as e:
            logger.error(f"Erro ao contar documentos: {e}")
            return 0
    
    def create(self, obj_in: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Criar novo documento"""
        try:
            collection = self._get_collection()
            
            # Remover campos None
            doc_data = {k: v for k, v in obj_in.items() if v is not None}
            
            result = collection.insert_one(doc_data)
            
            if result.inserted_id:
                return self.get_by_id(str(result.inserted_id))
            return None
            
        except Exception as e:
            logger.error(f"Erro ao criar documento: {e}")
            return None
    
    def update(self, id: str, obj_in: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Atualizar documento"""
        try:
            collection = self._get_collection()
            
            # Remover campos None do update
            update_data = {k: v for k, v in obj_in.items() if v is not None}
            
            if not update_data:
                return self.get_by_id(id)
            
            result = collection.update_one(
                {"_id": ObjectId(id)},
                {"$set": update_data}
            )
            
            # Retornar o documento atualizado se a operação foi bem-sucedida
            # (mesmo se não houve mudanças - matched_count > 0)
            if result.matched_count > 0:
                return self.get_by_id(id)
            return None
            
        except Exception as e:
            logger.error(f"Erro ao atualizar documento {id}: {e}")
            return None
    
    def delete(self, id: str) -> bool:
        """Excluir documento"""
        try:
            collection = self._get_collection()
            result = collection.delete_one({"_id": ObjectId(id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Erro ao excluir documento {id}: {e}")
            return False
    
    def search(
        self,
        search_term: str,
        search_fields: List[str],
        skip: int = 0,
        limit: int = 100,
        **additional_filters
    ) -> List[Dict[str, Any]]:
        """Buscar documentos por termo de pesquisa"""
        try:
            collection = self._get_collection()
            
            # Criar filtro de busca
            search_filters = []
            for field in search_fields:
                search_filters.append({
                    field: {"$regex": search_term, "$options": "i"}
                })
            
            mongo_filter = {"$or": search_filters}
            
            # Adicionar filtros adicionais
            additional_filter = self._prepare_filter(**additional_filters)
            if additional_filter:
                mongo_filter = {"$and": [mongo_filter, additional_filter]}
            
            cursor = collection.find(mongo_filter)
            
            # Aplicar paginação
            if limit > 0:
                cursor = cursor.skip(skip).limit(limit)
            elif limit == -1:
                cursor = cursor.skip(skip)
            
            docs = list(cursor)
            return [self._object_id_to_str(doc) for doc in docs]
            
        except Exception as e:
            logger.error(f"Erro ao buscar documentos: {e}")
            return []
    
    def distinct(self, field: str, **filters) -> List[Any]:
        """Obter valores distintos de um campo"""
        try:
            collection = self._get_collection()
            mongo_filter = self._prepare_filter(**filters)
            return collection.distinct(field, mongo_filter)
        except Exception as e:
            logger.error(f"Erro ao buscar valores distintos do campo {field}: {e}")
            return []