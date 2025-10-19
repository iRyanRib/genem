from typing import List, Optional, Dict, Any
import os
import uuid
from fastapi import UploadFile

from app.schemas.document import (
    Document, DocumentCreate, DocumentUpdate, DocumentQuery,
    DocumentUploadRequest, DocumentRecoverRequest, DocumentDeleteRequest
)
from app.services.base import MongoService
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class DocumentService(MongoService):
    """Serviço para operações CRUD de Document"""
    
    def __init__(self):
        super().__init__("documents")
        # Diretório para armazenamento de arquivos (em produção, usar cloud storage)
        self.upload_dir = "uploads"
        self._ensure_upload_dir()
    
    def _ensure_upload_dir(self):
        """Garantir que o diretório de upload existe"""
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)
    
    def get_documents(self, query: DocumentQuery) -> Dict[str, Any]:
        """Obter lista de documentos com paginação e filtros"""
        try:
            # Preparar filtros
            filters = {}
            if query.extension:
                filters["extension"] = query.extension
            if query.name:
                filters["name"] = {"$regex": query.name, "$options": "i"}
            
            # Buscar documentos
            if query.search:
                # Busca por termo
                search_fields = ["name", "path", "extension"]
                documents_data = self.search(
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
                documents_data = self.get_multi(
                    skip=(query.page - 1) * query.pageSize if query.pageSize > 0 else 0,
                    limit=query.pageSize,
                    sort_by="name",
                    sort_order=1,
                    **filters
                )
                
                # Contar total
                total = self.count(**filters)
            
            # Converter para objetos Document
            documents = [Document(**data) for data in documents_data]
            
            return {
                "data": documents,
                "total": total,
                "page": query.page,
                "pageSize": query.pageSize
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter documentos: {e}")
            return {
                "data": [],
                "total": 0,
                "page": query.page,
                "pageSize": query.pageSize
            }
    
    def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """Obter documento por ID"""
        data = self.get_by_id(document_id)
        return Document(**data) if data else None
    
    def create_document(self, obj_in: DocumentCreate) -> Optional[Document]:
        """Criar novo documento"""
        try:
            # Converter schema para dict
            document_data = obj_in.model_dump()
            
            # Criar documento
            created_data = self.create(document_data)
            return Document(**created_data) if created_data else None
            
        except Exception as e:
            logger.error(f"Erro ao criar documento: {e}")
            return None
    
    def update_document(self, document_id: str, obj_in: DocumentUpdate) -> Optional[Document]:
        """Atualizar documento"""
        try:
            # Converter schema para dict, removendo campos None
            update_data = obj_in.model_dump(exclude_unset=True)
            
            # Atualizar documento
            updated_data = self.update(document_id, update_data)
            return Document(**updated_data) if updated_data else None
            
        except Exception as e:
            logger.error(f"Erro ao atualizar documento {document_id}: {e}")
            return None
    
    def delete_document(self, document_id: str) -> bool:
        """Excluir documento"""
        try:
            # Obter documento antes de excluir para remover arquivo físico
            document = self.get_document_by_id(document_id)
            if document:
                # Tentar remover arquivo físico
                try:
                    if os.path.exists(document.path):
                        os.remove(document.path)
                        logger.info(f"Arquivo removido: {document.path}")
                except Exception as e:
                    logger.warning(f"Erro ao remover arquivo físico {document.path}: {e}")
            
            # Excluir registro do banco
            return self.delete(document_id)
            
        except Exception as e:
            logger.error(f"Erro ao excluir documento {document_id}: {e}")
            return False
    
    def upload_documents(self, files: List[UploadFile]) -> Dict[str, Any]:
        """Fazer upload de múltiplos documentos"""
        uploaded = []
        errors = []
        
        for file in files:
            try:
                # Gerar nome único para o arquivo
                file_id = str(uuid.uuid4())
                file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
                safe_filename = f"{file_id}{file_extension}"
                file_path = os.path.join(self.upload_dir, safe_filename)
                
                # Salvar arquivo físico
                with open(file_path, "wb") as buffer:
                    content = file.file.read()
                    buffer.write(content)
                
                # Criar URL do arquivo (em produção, usar URL do cloud storage)
                file_url = f"/uploads/{safe_filename}"
                
                # Criar registro no banco
                document_data = DocumentCreate(
                    url=file_url,
                    path=file_path,
                    name=file.filename or safe_filename,
                    extension=file_extension.lstrip('.') if file_extension else "",
                    size=len(content)
                )
                
                created_document = self.create_document(document_data)
                if created_document:
                    uploaded.append(created_document)
                    logger.info(f"Documento uploaded: {file.filename}")
                else:
                    errors.append(f"Erro ao salvar registro do arquivo: {file.filename}")
                    # Remover arquivo físico se falhou ao salvar no banco
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        
            except Exception as e:
                errors.append(f"Erro ao fazer upload de {file.filename}: {str(e)}")
                logger.error(f"Erro ao fazer upload de {file.filename}: {e}")
        
        return {
            "uploaded": uploaded,
            "errors": errors
        }
    
    def recover_document(self, request: DocumentRecoverRequest) -> Optional[str]:
        """Recuperar/baixar documento por URL"""
        try:
            # Buscar documento por URL
            documents = self.get_multi(limit=1, url=request.url)
            
            if not documents:
                logger.warning(f"Documento não encontrado para URL: {request.url}")
                return None
            
            document_data = documents[0]
            file_path = document_data.get("path")
            
            if not file_path or not os.path.exists(file_path):
                logger.warning(f"Arquivo físico não encontrado: {file_path}")
                return None
            
            return file_path
            
        except Exception as e:
            logger.error(f"Erro ao recuperar documento: {e}")
            return None
    
    def delete_document_by_url(self, request: DocumentDeleteRequest) -> bool:
        """Excluir documento por URL"""
        try:
            # Buscar documento por URL
            documents = self.get_multi(limit=1, url=request.url)
            
            if not documents:
                logger.warning(f"Documento não encontrado para URL: {request.url}")
                return False
            
            document_data = documents[0]
            document_id = document_data.get("id")
            
            if document_id:
                return self.delete_document(document_id)
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao excluir documento por URL: {e}")
            return False


# Singleton instance
document_service = DocumentService()