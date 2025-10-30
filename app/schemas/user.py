from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# Propriedades compartilhadas
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False


# Propriedades para receber via API na criação
class UserCreate(UserBase):
    email: EmailStr
    name: str
    password: str


# Propriedades para receber via API na atualização
class UserUpdate(UserBase):
    password: Optional[str] = None


# Propriedades para retornar via API
class User(UserBase):
    id: str = Field(..., description="ObjectId do usuário")
    email: EmailStr
    name: str


# Schema para resposta de login
class Token(BaseModel):
    access_token: str
    token_type: str


# Schema para dados do token
class TokenData(BaseModel):
    user_id: Optional[str] = None 