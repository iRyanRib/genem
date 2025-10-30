from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

from .question import QuestionBase, Question, DisciplineType
from .alternative import Alternative, AlternativeCreate


class GeneratedQuestionBase(QuestionBase):
    """Schema base para GeneratedQuestion que herda de Question"""
    user: str = Field(..., description="ObjectId do usuário que gerou a questão")
    rationale: str = Field(..., min_length=1, description="Rationale da resposta correta")
    source_question_id: str = Field(..., description="ID da questão original usada como base")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Data de criação")


class GeneratedQuestionCreate(GeneratedQuestionBase):
    """Schema para criação de GeneratedQuestion"""
    alternatives: List[AlternativeCreate] = Field(..., min_items=5, max_items=5, description="Exatamente 5 alternativas")


class GeneratedQuestionUpdate(BaseModel):
    """Schema para atualização de GeneratedQuestion"""
    title: Optional[str] = Field(None, min_length=1)
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
    rationale: Optional[str] = Field(None, min_length=1)

    @field_validator('year')
    @classmethod
    def validate_year(cls, v):
        if v is not None and v < 1998:
            raise ValueError('Ano deve ser 1998 ou posterior')
        return v

    @field_validator('correctAlternative')
    @classmethod
    def validate_correct_alternative(cls, v):
        if v is not None and v.upper() not in ['A', 'B', 'C', 'D', 'E']:
            raise ValueError('Alternativa correta deve ser A, B, C, D ou E')
        return v.upper() if v is not None else v


class GeneratedQuestion(GeneratedQuestionBase):
    """Schema para retorno de GeneratedQuestion via API"""
    id: str = Field(..., description="ID da questão gerada")

    class Config:
        from_attributes = True


class GeneratedQuestionQuery(BaseModel):
    """Schema para parâmetros de query nas buscas de questões geradas"""
    page: Optional[int] = Field(1, ge=1, description="Página")
    pageSize: Optional[int] = Field(10, ge=-1, description="Tamanho da página (-1 para todos)")
    search: Optional[str] = Field(None, description="Termo de busca")
    user: Optional[str] = Field(None, description="Filtro por usuário")
    discipline: Optional[DisciplineType] = Field(None, description="Filtro por disciplina")
    year: Optional[int] = Field(None, gt=0, description="Filtro por ano")
    source_question_id: Optional[str] = Field(None, description="Filtro por questão original")


class GenerateQuestionRequest(BaseModel):
    """Schema para solicitação de geração de questão"""
    question_id: str = Field(..., description="ID da questão base para geração")


# Schemas de resposta
class GeneratedQuestionListResponse(BaseModel):
    """Schema para resposta de listagem de questões geradas"""
    success: bool = True
    data: List[GeneratedQuestion]
    total: int
    page: int
    pageSize: int


class GeneratedQuestionResponse(BaseModel):
    """Schema para resposta de operação com questão gerada única"""
    success: bool = True
    data: GeneratedQuestion


class GenerateQuestionResponse(BaseModel):
    """Schema para resposta de geração de questão"""
    success: bool = True
    data: GeneratedQuestion
    message: str = "Questão gerada com sucesso"