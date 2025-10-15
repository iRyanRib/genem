from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import FileResponse

from app.schemas.document import (
    Document, DocumentCreate, DocumentUpdate, DocumentQuery,
    DocumentListResponse, DocumentResponse, DocumentUploadResponse,
    DocumentDeleteResponse, DocumentRecoverRequest, DocumentDeleteRequest
)
from app.services.document import document_service
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=DocumentListResponse)
async def get_documents(
    page: int = Query(1, ge=1, description="Página"),
    pageSize: int = Query(10, ge=-1, description="Tamanho da página"),
    search: str = Query(None, description="Termo de busca"),
    extension: str = Query(None, description="Filtro por extensão"),
    name: str = Query(None, description="Filtro por nome")
) -> DocumentListResponse:
    """
    Obter lista de documentos com paginação e filtros.
    
    Parâmetros:
    - **page**: Número da página (padrão: 1)
    - **pageSize**: Itens por página (padrão: 10, -1 para todos)
    - **search**: Termo de busca (nome, caminho, extensão)
    - **extension**: Filtrar por extensão específica
    - **name**: Filtrar por nome (busca parcial)
    """
    try:
        query = DocumentQuery(
            page=page,
            pageSize=pageSize,
            search=search,
            extension=extension,
            name=name
        )
        
        result = document_service.get_documents(query)
        
        return DocumentListResponse(
            success=True,
            data=result["data"],
            total=result["total"],
            page=result["page"],
            pageSize=result["pageSize"]
        )
        
    except Exception as e:
        logger.error(f"Erro ao obter documentos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document_by_id(document_id: str) -> DocumentResponse:
    """
    Obter documento por ID.
    """
    try:
        document = document_service.get_document_by_id(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documento não encontrado com ID: {document_id}"
            )
        
        return DocumentResponse(success=True, data=document)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter documento {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.post("/", response_model=DocumentResponse)
async def create_document(document_in: DocumentCreate) -> DocumentResponse:
    """
    Criar novo documento (registro).
    """
    try:
        document = document_service.create_document(document_in)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao criar documento"
            )
        
        return DocumentResponse(success=True, data=document)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar documento: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    document_in: DocumentUpdate
) -> DocumentResponse:
    """
    Atualizar documento existente.
    """
    try:
        # Verificar se documento existe
        existing_document = document_service.get_document_by_id(document_id)
        if not existing_document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documento não encontrado com ID: {document_id}"
            )
        
        updated_document = document_service.update_document(document_id, document_in)
        
        if not updated_document:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao atualizar documento"
            )
        
        return DocumentResponse(success=True, data=updated_document)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar documento {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.delete("/{document_id}")
async def delete_document(document_id: str) -> Dict[str, Any]:
    """
    Excluir documento.
    """
    try:
        # Verificar se documento existe
        existing_document = document_service.get_document_by_id(document_id)
        if not existing_document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documento não encontrado com ID: {document_id}"
            )
        
        success = document_service.delete_document(document_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao excluir documento"
            )
        
        return {
            "success": True,
            "message": f"Documento {document_id} excluído com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao excluir documento {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_documents(
    documents: List[UploadFile] = File(..., description="Lista de arquivos para upload")
) -> DocumentUploadResponse:
    """
    Fazer upload de múltiplos documentos.
    """
    try:
        if not documents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nenhum arquivo foi enviado"
            )
        
        result = document_service.upload_documents(documents)
        
        return DocumentUploadResponse(
            success=True,
            uploaded=result["uploaded"],
            errors=result["errors"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao fazer upload de documentos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.get("/download")
async def download_document(
    url: str = Query(..., description="URL do documento para download"),
    name: str = Query(None, description="Nome do arquivo")
):
    """
    Baixar documento por URL.
    """
    try:
        request = DocumentRecoverRequest(url=url, name=name)
        file_path = document_service.recover_document(request)
        
        if not file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documento não encontrado para URL: {url}"
            )
        
        # Retornar arquivo para download
        filename = name or url.split('/')[-1]
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao baixar documento: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )


@router.delete("/")
async def delete_document_by_url(
    url: str = Query(..., description="URL do documento para exclusão")
) -> DocumentDeleteResponse:
    """
    Excluir documento por URL.
    """
    try:
        request = DocumentDeleteRequest(url=url)
        success = document_service.delete_document_by_url(request)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documento não encontrado para URL: {url}"
            )
        
        return DocumentDeleteResponse(
            success=True,
            message="Documento excluído com sucesso"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao excluir documento por URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )