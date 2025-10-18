from typing import List, Optional, Union, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator
from bson import ObjectId


class ExamStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


class ExamQuestion(BaseModel):
    """Questão dentro de um exame com resposta do usuário"""
    question_id: str  # ObjectId as string
    user_answer: Optional[str] = None  # A, B, C, D, E
    correct_answer: str  # A, B, C, D, E
    is_correct: Optional[bool] = None
    
    class Config:
        json_encoders = {
            ObjectId: str
        }


class ExamBase(BaseModel):
    """Campos base do exame"""
    user_id: str  # ObjectId do usuário no MongoDB como string
    total_questions: int
    status: ExamStatus = ExamStatus.NOT_STARTED
    
    @validator('user_id', pre=True)
    def validate_user_id(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str) and ObjectId.is_valid(v):
            return v
        raise ValueError(f"Invalid ObjectId: {v}")
    
    class Config:
        arbitrary_types_allowed = True


class ExamCreate(BaseModel):
    """Dados para criação do exame"""
    user_id: str  # ObjectId do usuário no MongoDB como string
    topics: Optional[List[str]] = None
    years: Optional[List[int]] = None
    question_count: int = Field(default=25, ge=1, le=100)
    
    @validator('user_id', pre=True)
    def validate_user_id(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str) and ObjectId.is_valid(v):
            return v
        raise ValueError(f"Invalid ObjectId: {v}")
    
    class Config:
        arbitrary_types_allowed = True


class ExamUpdate(BaseModel):
    """Atualização de resposta no exame"""
    question_id: str
    user_answer: str  # A, B, C, D, E


class ExamFinalize(BaseModel):
    """Finalização do exame"""
    exam_id: str


class Exam(ExamBase):
    """Modelo completo do exame"""
    id: str
    questions: List[ExamQuestion]
    total_correct_answers: int = 0
    total_wrong_answers: int = 0
    created_at: datetime
    updated_at: datetime
    finished_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class ExamSummary(BaseModel):
    """Resumo do exame para listagem"""
    id: str
    user_id: str  # ObjectId do usuário no MongoDB como string
    total_questions: int
    total_correct_answers: int
    total_wrong_answers: int
    status: ExamStatus
    created_at: datetime
    updated_at: datetime
    finished_at: Optional[datetime] = None
    
    @validator('user_id', pre=True)
    def validate_user_id(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str) and ObjectId.is_valid(v):
            return v
        raise ValueError(f"Invalid ObjectId: {v}")
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class ExamDetails(Exam):
    """Exame com detalhes completos (gabarito + respostas)"""
    pass


class ExamResponse(BaseModel):
    """Resposta de criação/atualização do exame"""
    exam_id: str
    status: ExamStatus
    message: str


class QuestionForExam(BaseModel):
    """Questão formatada para exibição no exame (sem gabarito)"""
    id: str
    year: int
    discipline: str
    context: str
    alternatives_introduction: Optional[str] = None
    alternatives: List[dict]  # Inclui base64File de cada alternativa, mas sem isCorrect
    
    class Config:
        json_encoders = {
            ObjectId: str
        }


class ExamForUser(BaseModel):
    """Exame para ser respondido pelo usuário"""
    id: str
    status: ExamStatus
    total_questions: int
    answered_questions: int
    questions: List[QuestionForExam]
    created_at: datetime
    
    class Config:
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }