from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.user import User
from app.schemas.item import ItemCreate, ItemUpdate


class ItemService:
    def get(self, db: Session, id: int) -> Optional[Item]:
        return db.query(Item).filter(Item.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100, owner_id: Optional[int] = None
    ) -> List[Item]:
        query = db.query(Item)
        if owner_id is not None:
            query = query.filter(Item.owner_id == owner_id)
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: ItemCreate, owner_id: int) -> Item:
        db_obj = Item(
            title=obj_in.title,
            description=obj_in.description,
            owner_id=owner_id,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: Item, obj_in: ItemUpdate
    ) -> Item:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> Item:
        obj = db.query(Item).get(id)
        db.delete(obj)
        db.commit()
        return obj


item_service = ItemService() 