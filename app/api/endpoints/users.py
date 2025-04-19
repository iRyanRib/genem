from typing import Any, List, Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_active_superuser
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import User as UserSchema
from app.schemas.user import UserCreate, UserUpdate
from app.services.user import user_service

router = APIRouter()


@router.get("/", response_model=List[UserSchema])
def read_users(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_superuser)],
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Recuperar usuários.
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.post("/", response_model=UserSchema)
def create_user(
    *,
    db: Annotated[Session, Depends(get_db)],
    user_in: UserCreate,
    current_user: Annotated[User, Depends(get_current_active_superuser)],
) -> Any:
    """
    Criar novo usuário.
    """
    user = user_service.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um usuário com este e-mail",
        )
    user = user_service.create(db, obj_in=user_in)
    return user


@router.get("/{user_id}", response_model=UserSchema)
def read_user_by_id(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_active_superuser)],
    db: Annotated[Session, Depends(get_db)],
) -> Any:
    """
    Obter um usuário específico pelo id.
    """
    user = user_service.get(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )
    return user


@router.put("/{user_id}", response_model=UserSchema)
def update_user(
    *,
    db: Annotated[Session, Depends(get_db)],
    user_id: int,
    user_in: UserUpdate,
    current_user: Annotated[User, Depends(get_current_active_superuser)],
) -> Any:
    """
    Atualizar um usuário.
    """
    user = user_service.get(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )
    user = user_service.update(db, db_obj=user, obj_in=user_in)
    return user 