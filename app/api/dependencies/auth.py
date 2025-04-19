from typing import Annotated, Generator

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.services.user import user_service


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
) -> User:
    # Aqui você implementaria a lógica de autenticação real
    # Este é apenas um exemplo simplificado
    user = user_service.get_by_email(db, email="admin@example.com")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado")
    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuário inativo")
    return current_user


def get_current_active_superuser(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Não tem permissões suficientes"
        )
    return current_user 