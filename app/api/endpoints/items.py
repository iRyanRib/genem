from typing import Any, List, Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import get_current_active_user
from app.schemas.item import Item, ItemCreate, ItemUpdate
from app.schemas.user import User
from app.services.item import item_service

router = APIRouter()


@router.get("/", response_model=List[Item])
def read_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Recuperar itens.
    """
    items = item_service.get_multi(
        skip=skip, limit=limit, owner_id=current_user.id
    )
    return items


@router.post("/", response_model=Item)
def create_item(
    *,
    item_in: ItemCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Any:
    """
    Criar novo item.
    """
    item = item_service.create(obj_in=item_in, owner_id=current_user.id)
    return item


@router.get("/{id}", response_model=Item)
def read_item(
    *,
    id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Any:
    """
    Obter item pelo ID.
    """
    item = item_service.get(id=id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item não encontrado"
        )
    # Na versão mockada, não verificamos o owner_id
    return item


@router.put("/{id}", response_model=Item)
def update_item(
    *,
    id: int,
    item_in: ItemUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Any:
    """
    Atualizar um item.
    """
    item = item_service.update(item_id=id, obj_in=item_in)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item não encontrado"
        )
    return item


@router.delete("/{id}", response_model=Item)
def delete_item(
    *,
    id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Any:
    """
    Deletar um item.
    """
    item = item_service.remove(id=id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item não encontrado"
        )
    return item 