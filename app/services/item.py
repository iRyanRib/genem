from typing import List, Optional, Dict

from app.schemas.item import Item, ItemCreate, ItemUpdate


# Mock database
ITEMS_DB: Dict[int, Item] = {}
next_id = 1


class ItemService:
    def get(self, id: int) -> Optional[Item]:
        """Obter um item pelo ID"""
        if id in ITEMS_DB:
            return ITEMS_DB[id]
        return None

    def get_multi(
        self, *, skip: int = 0, limit: int = 100, owner_id: Optional[int] = None
    ) -> List[Item]:
        """Obter múltiplos itens"""
        result = list(ITEMS_DB.values())
        if owner_id is not None:
            # Esta implementação de mock considera que todos itens pertencem ao usuário atual
            pass
        
        return result[skip : skip + limit]

    def create(self, *, obj_in: ItemCreate, owner_id: int) -> Item:
        """Criar um novo item"""
        global next_id
        
        item = Item(
            id=next_id,
            title=obj_in.title,
            description=obj_in.description
        )
        
        ITEMS_DB[next_id] = item
        next_id += 1
        return item

    def update(
        self, *, item_id: int, obj_in: ItemUpdate
    ) -> Optional[Item]:
        """Atualizar um item existente"""
        if item_id not in ITEMS_DB:
            return None
            
        item = ITEMS_DB[item_id]
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field in update_data:
            setattr(item, field, update_data[field])
            
        ITEMS_DB[item_id] = item
        return item

    def remove(self, *, id: int) -> Optional[Item]:
        """Remover um item pelo ID"""
        if id not in ITEMS_DB:
            return None
            
        item = ITEMS_DB.pop(id)
        return item


# Singleton instance
item_service = ItemService() 