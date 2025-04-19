from typing import List, Optional

from pydantic import BaseModel, EmailStr

from app.schemas.item import Item


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


# Propriedades adicionais para retornar via API
class UserInDBBase(UserBase):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True


# Propriedades para retornar via API
class User(UserInDBBase):
    pass


# Propriedades para retornar via API com itens
class UserWithItems(UserInDBBase):
    items: List[Item] = []


# Propriedades armazenadas no DB
class UserInDB(UserInDBBase):
    hashed_password: str 