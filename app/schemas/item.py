from typing import Optional

from pydantic import BaseModel


# Propriedades compartilhadas
class ItemBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


# Propriedades para receber via API na criação
class ItemCreate(ItemBase):
    title: str


# Propriedades para receber via API na atualização
class ItemUpdate(ItemBase):
    pass


# Propriedades adicionais para retornar via API
class ItemInDBBase(ItemBase):
    id: int
    title: str
    owner_id: int

    class Config:
        from_attributes = True


# Propriedades para retornar via API
class Item(ItemInDBBase):
    pass


# Propriedades armazenadas no DB
class ItemInDB(ItemInDBBase):
    pass 