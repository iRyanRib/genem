from typing import Any, List, Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies.auth import get_current_active_user, get_current_active_superuser
from app.schemas.user import User, UserCreate, UserUpdate, Token
from app.services.user import user_service
from app.utils.security import create_access_token

router = APIRouter()


@router.post("/register", response_model=User)
def register(user_in: UserCreate) -> Any:
    """
    Registrar novo usuário (rota pública)
    """
    user = user_service.get_by_email(email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="Já existe um usuário com este email.",
        )
    
    user = user_service.create(obj_in=user_in)
    return user


@router.post("/login/access-token", response_model=Token)
def login_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Any:
    """
    OAuth2 login para obter token JWT
    """
    user = user_service.authenticate(email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
        )
    
    access_token = create_access_token(subject=user.id)
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=User)
def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> Any:
    """
    Obter usuário atual
    """
    return current_user


@router.put("/me", response_model=User)
def update_user_me(
    *,
    user_in: UserUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> Any:
    """
    Atualizar usuário atual
    """
    user = user_service.update(user_id=current_user.id, obj_in=user_in)
    return user


@router.get("/", response_model=List[User])
def read_users(
    current_user: Annotated[User, Depends(get_current_active_superuser)],
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Recuperar usuários (apenas superusuários)
    """
    users = user_service.get_multi(skip=skip, limit=limit)
    return users


@router.post("/", response_model=User)
def create_user(
    *,
    user_in: UserCreate,
    current_user: Annotated[User, Depends(get_current_active_superuser)]
) -> Any:
    """
    Criar novo usuário (apenas superusuários)
    """
    user = user_service.get_by_email(email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="Já existe um usuário com este email.",
        )
    
    user = user_service.create(obj_in=user_in)
    return user


@router.get("/{user_id}", response_model=User)
def read_user_by_id(
    user_id: str,
    current_user: Annotated[User, Depends(get_current_active_superuser)]
) -> Any:
    """
    Obter um usuário específico pelo id (apenas superusuários)
    """
    user = user_service.get(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )
    return user


@router.put("/{user_id}", response_model=User)
def update_user(
    *,
    user_id: str,
    user_in: UserUpdate,
    current_user: Annotated[User, Depends(get_current_active_superuser)]
) -> Any:
    """
    Atualizar um usuário (apenas superusuários)
    """
    user = user_service.get(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )
    
    user = user_service.update(user_id=user_id, obj_in=user_in)
    return user 