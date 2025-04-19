from typing import Any, List, Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.item import Item, ItemCreate, ItemUpdate
from app.services.item import item_service

router = APIRouter()


@router.get("/", response_model=List[Item])
def read_items(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Recuperar itens.
    """
    items = item_service.get_multi(
        db, skip=skip, limit=limit, owner_id=current_user.id
    )
    return items


@router.post("/", response_model=Item)
def create_item(
    *,
    db: Annotated[Session, Depends(get_db)],
    item_in: ItemCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Any:
    """
    Criar novo item.
    """
    item = item_service.create(db=db, obj_in=item_in, owner_id=current_user.id)
    return item


@router.get("/{id}", response_model=Item)
def read_item(
    *,
    db: Annotated[Session, Depends(get_db)],
    id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Any:
    """
    Obter item pelo ID.
    """
    item = item_service.get(db=db, id=id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item não encontrado"
        )
    if item.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão suficiente"
        )
    return item


@router.put("/{id}", response_model=Item)
def update_item(
    *,
    db: Annotated[Session, Depends(get_db)],
    id: int,
    item_in: ItemUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Any:
    """
    Atualizar um item.
    """
    item = item_service.get(db=db, id=id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item não encontrado"
        )
    if item.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão suficiente"
        )
    item = item_service.update(db=db, db_obj=item, obj_in=item_in)
    return item


@router.delete("/{id}", response_model=Item)
def delete_item(
    *,
    db: Annotated[Session, Depends(get_db)],
    id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Any:
    """
    Deletar um item.
    """
    item = item_service.get(db=db, id=id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item não encontrado"
        )
    if item.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão suficiente"
        )
    item = item_service.remove(db=db, id=id)
    return item 