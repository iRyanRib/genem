from typing import Optional

from pydantic import BaseModel, EmailStr


# Propriedades compartilhadas
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False


# Propriedades para receber via API na criação
class UserCreate(UserBase):
    email: EmailStr
    password: str


# Propriedades para receber via API na atualização
class UserUpdate(UserBase):
    password: Optional[str] = None


# Propriedades para retornar via API
class User(UserBase):
    id: int
    email: EmailStr 