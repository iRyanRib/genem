from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import settings
from app.schemas.user import User
from app.services.user import user_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/users/login/access-token")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    """
    Validar token JWT e retornar o usuário atual
    """
    try:
        # Em uma implementação real, você decodificaria o JWT
        # Nesta versão mockada, apenas extraímos o ID do usuário diretamente
        user_id = int(token.replace("token_", ""))
        user = user_service.get(id=user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário não encontrado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except (ValueError, AttributeError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Verificar se o usuário está ativo
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuário inativo")
    return current_user


def get_current_active_superuser(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Verificar se o usuário é superusuário
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Não tem permissões suficientes"
        )
    return current_user 