from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import UploadFile


class DocumentBase(BaseModel):
    """Schema base para Document"""
    url: str = Field(..., description="URL do documento")
    path: str = Field(..., description="Caminho do documento")
    name: str = Field(..., description="Nome do documento")
    extension: str = Field(..., description="Extensão do arquivo")
    size: int = Field(..., ge=0, description="Tamanho do arquivo em bytes")


class DocumentCreate(DocumentBase):
    """Schema para criação de Document"""
    pass


class DocumentUpdate(BaseModel):
    """Schema para atualização de Document"""
    url: Optional[str] = None
    path: Optional[str] = None
    name: Optional[str] = None
    extension: Optional[str] = None
    size: Optional[int] = Field(None, ge=0)


class Document(DocumentBase):
    """Schema para retorno de Document via API"""
    id: str = Field(..., description="ID do documento")

    class Config:
        from_attributes = True


class DocumentQuery(BaseModel):
    """Schema para parâmetros de query nas buscas de documentos"""
    page: Optional[int] = Field(1, ge=1, description="Página")
    pageSize: Optional[int] = Field(10, ge=-1, description="Tamanho da página (-1 para todos)")
    search: Optional[str] = Field(None, description="Termo de busca")
    extension: Optional[str] = Field(None, description="Filtro por extensão")
    name: Optional[str] = Field(None, description="Filtro por nome")


class DocumentUploadRequest(BaseModel):
    """Schema para request de upload de documentos"""
    documents: List[UploadFile] = Field(..., min_items=1, description="Lista de arquivos para upload")


class DocumentRecoverRequest(BaseModel):
    """Schema para request de recuperação de documento"""
    url: str = Field(..., description="URL do documento para download")
    name: Optional[str] = Field(None, description="Nome do arquivo")


class DocumentDeleteRequest(BaseModel):
    """Schema para request de exclusão de documento"""
    url: str = Field(..., description="URL do documento para exclusão")


# Schemas de resposta
class DocumentListResponse(BaseModel):
    """Schema para resposta de listagem de documentos"""
    success: bool = True
    data: List[Document]
    total: int
    page: int
    pageSize: int


class DocumentResponse(BaseModel):
    """Schema para resposta de operação com documento único"""
    success: bool = True
    data: Document


class DocumentUploadResponse(BaseModel):
    """Schema para resposta de upload"""
    success: bool = True
    uploaded: List[Document]
    errors: List[str] = []


class DocumentDeleteResponse(BaseModel):
    """Schema para resposta de exclusão"""
    success: bool = True
    message: str = "Documento excluído com sucesso"