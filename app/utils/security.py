from datetime import datetime, timedelta
from typing import Any, Union

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    # Aqui você implementaria a geração de tokens JWT
    # Este é apenas um stub simplificado
    return f"token_{subject}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password) 