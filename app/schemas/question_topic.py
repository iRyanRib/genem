from typing import Optional, List
from pydantic import BaseModel, Field


class QuestionTopicBase(BaseModel):
    """Schema base para QuestionTopic"""
    field: str = Field(..., description="Campo do tópico")
    field_code: str = Field(..., description="Código do campo")
    area: str = Field(..., description="Área do tópico")
    area_code: str = Field(..., description="Código da área")
    general_topic: str = Field(..., description="Tópico geral")
    general_topic_code: str = Field(..., description="Código do tópico geral")
    specific_topic: str = Field(..., description="Tópico específico")


class QuestionTopicCreate(QuestionTopicBase):
    """Schema para criação de QuestionTopic"""
    pass


class QuestionTopicUpdate(BaseModel):
    """Schema para atualização de QuestionTopic"""
    field: Optional[str] = None
    field_code: Optional[str] = None
    area: Optional[str] = None
    area_code: Optional[str] = None
    general_topic: Optional[str] = None
    general_topic_code: Optional[str] = None
    specific_topic: Optional[str] = None


class QuestionTopic(QuestionTopicBase):
    """Schema para retorno de QuestionTopic via API"""
    id: str = Field(..., description="ID do tópico")

    class Config:
        from_attributes = True


class QuestionTopicQuery(BaseModel):
    """Schema para parâmetros de query nas buscas de tópicos"""
    page: Optional[int] = Field(1, ge=1, description="Página")
    pageSize: Optional[int] = Field(10, ge=-1, description="Tamanho da página (-1 para todos)")
    search: Optional[str] = Field(None, description="Termo de busca")
    field: Optional[str] = Field(None, description="Filtro por campo")
    area: Optional[str] = Field(None, description="Filtro por área")
    field_code: Optional[str] = Field(None, description="Filtro por código do campo")
    area_code: Optional[str] = Field(None, description="Filtro por código da área")
    general_topic_code: Optional[str] = Field(None, description="Filtro por código do tópico geral")


class ClassifyUnusedTopicsRequest(BaseModel):
    """Schema para classificação de tópicos não utilizados"""
    limit: Optional[int] = Field(None, ge=1, description="Limite de tópicos para processar")


# Schemas de resposta
class QuestionTopicListResponse(BaseModel):
    """Schema para resposta de listagem de tópicos"""
    success: bool = True
    data: List[QuestionTopic]
    total: int
    page: int
    pageSize: int


class QuestionTopicResponse(BaseModel):
    """Schema para resposta de operação com tópico único"""
    success: bool = True
    data: QuestionTopic


class DistinctFieldsResponse(BaseModel):
    """Schema para resposta de campos distintos"""
    success: bool = True
    data: List[str]
    total: int


class DistinctAreasResponse(BaseModel):
    """Schema para resposta de áreas distintas"""
    success: bool = True
    data: List[str]
    total: int


class ClassifyUnusedTopicsResponse(BaseModel):
    """Schema para resposta de classificação de tópicos não utilizados"""
    success: bool = True
    processed: int
    classified: int
    errors: List[str] = []