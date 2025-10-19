from typing import Optional, Any
from pydantic import BaseModel, Field


class AlternativeBase(BaseModel):
    """Schema base para Alternative"""
    letter: str = Field(..., min_length=1, description="Letra da alternativa (A, B, C, D, E)")
    text: Optional[str] = Field(None, description="Texto da alternativa")
    file: Optional[Any] = Field(None, description="Arquivo relacionado à alternativa")
    isCorrect: bool = Field(..., description="Se é a alternativa correta")
    base64File: Optional[str] = Field(None, description="Arquivo em base64")


class AlternativeCreate(AlternativeBase):
    """Schema para criação de Alternative"""
    text: str = Field(..., min_length=1, description="Texto da alternativa é obrigatório na criação")


class AlternativeUpdate(AlternativeBase):
    """Schema para atualização de Alternative"""
    letter: Optional[str] = Field(None, min_length=1)
    isCorrect: Optional[bool] = None


class Alternative(AlternativeBase):
    """Schema para retorno de Alternative via API"""
    pass

    class Config:
        from_attributes = True