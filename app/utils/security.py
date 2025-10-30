from datetime import datetime, timedelta
from typing import Any, Union
import hashlib

from jose import jwt

from app.core.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 8  # 8 dias


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """
    Criar um token de acesso JWT
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verificar se a senha fornecida corresponde ao hash
    Usando hash simples por enquanto para evitar problemas de compatibilidade
    """
    return get_password_hash(plain_password) == hashed_password


def get_password_hash(password: str) -> str:
    """
    Gerar hash da senha
    Usando hash simples por enquanto para evitar problemas de compatibilidade
    """
    # Usar SHA256 com salt por enquanto (não ideal para produção)
    salt = "genem_salt_2024"
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest() 