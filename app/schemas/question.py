from typing import Optional, List, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
from bson import ObjectId

from .alternative import Alternative, AlternativeCreate


class DisciplineType(str, Enum):
    """Enum para tipos de disciplina"""
    CIENCIAS_HUMANAS = "ciencias-humanas"
    CIENCIAS_NATUREZA = "ciencias-natureza"
    LINGUAGENS = "linguagens"
    MATEMATICA = "matematica"
    ESPANHOL = "espanhol"
    INGLES = "ingles"


class QuestionBase(BaseModel):
    """Schema base para Question"""
    title: str = Field(..., min_length=1, description="Título da questão")
    index: int = Field(..., gt=0, description="Índice da questão")
    discipline: DisciplineType = Field(..., description="Disciplina da questão")
    language: Optional[str] = Field(None, description="Idioma da questão")
    year: int = Field(..., gt=0, description="Ano da prova")
    context: Optional[str] = Field(None, description="Contexto da questão")
    files: Optional[List[Any]] = Field(None, description="Arquivos relacionados")
    base64Files: Optional[List[str]] = Field(None, description="Arquivos em base64")
    correctAlternative: str = Field(..., min_length=1, description="Alternativa correta")
    alternativesIntroduction: Optional[str] = Field(None, description="Introdução das alternativas")
    alternatives: List[Alternative] = Field(..., min_items=1, description="Lista de alternativas")
    summary: Optional[str] = Field(None, description="Resumo da questão")
    keywords: Optional[List[str]] = Field(None, description="Palavras-chave")
    questionTopics: Optional[List[str]] = Field(None, description="IDs dos tópicos relacionados")

    @validator('year')
    def validate_year(cls, v):
        if v < 1998:  # ENEM começou em 1998
            raise ValueError('Ano deve ser 1998 ou posterior')
        return v

    @validator('correctAlternative')
    def validate_correct_alternative(cls, v):
        if v.upper() not in ['A', 'B', 'C', 'D', 'E']:
            raise ValueError('Alternativa correta deve ser A, B, C, D ou E')
        return v.upper()


class QuestionCreate(QuestionBase):
    """Schema para criação de Question"""
    alternatives: List[AlternativeCreate] = Field(..., min_items=1, description="Lista de alternativas para criação")


class QuestionUpdate(BaseModel):
    """Schema para atualização de Question"""
    title: Optional[str] = Field(None, min_length=1)
    index: Optional[int] = Field(None, gt=0)
    discipline: Optional[DisciplineType] = None
    language: Optional[str] = None
    year: Optional[int] = Field(None, gt=0)
    context: Optional[str] = None
    files: Optional[List[Any]] = None
    base64Files: Optional[List[str]] = None
    correctAlternative: Optional[str] = Field(None, min_length=1)
    alternativesIntroduction: Optional[str] = None
    alternatives: Optional[List[Alternative]] = None
    summary: Optional[str] = None
    keywords: Optional[List[str]] = None
    questionTopics: Optional[List[str]] = None

    @validator('year')
    def validate_year(cls, v):
        if v is not None and v < 1998:
            raise ValueError('Ano deve ser 1998 ou posterior')
        return v

    @validator('correctAlternative')
    def validate_correct_alternative(cls, v):
        if v is not None and v.upper() not in ['A', 'B', 'C', 'D', 'E']:
            raise ValueError('Alternativa correta deve ser A, B, C, D ou E')
        return v.upper() if v is not None else v


class Question(QuestionBase):
    """Schema para retorno de Question via API"""
    id: str = Field(..., description="ID da questão")

    class Config:
        from_attributes = True


class QuestionQuery(BaseModel):
    """Schema para parâmetros de query nas buscas"""
    page: Optional[int] = Field(1, ge=1, description="Página")
    pageSize: Optional[int] = Field(10, ge=-1, description="Tamanho da página (-1 para todos)")
    search: Optional[str] = Field(None, description="Termo de busca")
    index: Optional[int] = Field(None, gt=0, description="Índice específico")
    discipline: Optional[DisciplineType] = Field(None, description="Filtro por disciplina")
    year: Optional[int] = Field(None, gt=0, description="Filtro por ano")


class AnalyzeImageRequest(BaseModel):
    """Schema para análise de imagem"""
    imageUrl: str = Field(..., description="URL da imagem para análise")
    prompt: str = Field("What's in this image?", description="Prompt para análise")


class SummarizeQuestionsRequest(BaseModel):
    """Schema para sumarização de questões"""
    questionIds: List[str] = Field(..., min_items=1, description="IDs das questões para sumarizar")


class QuestionImportRequest(BaseModel):
    """Schema para importação de questões"""
    questions: List[QuestionCreate] = Field(..., min_items=1, description="Lista de questões para importar")


# Schemas de resposta
class QuestionListResponse(BaseModel):
    """Schema para resposta de listagem de questões"""
    success: bool = True
    data: List[Question]
    total: int
    page: int
    pageSize: int


class QuestionResponse(BaseModel):
    """Schema para resposta de operação com questão única"""
    success: bool = True
    data: Question


class QuestionImportResponse(BaseModel):
    """Schema para resposta de importação"""
    success: bool = True
    imported: int
    skipped: int
    errors: List[str] = []