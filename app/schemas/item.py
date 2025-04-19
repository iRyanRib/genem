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


# Propriedades para retornar via API
class Item(ItemBase):
    id: int
    title: str 