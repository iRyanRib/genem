from typing import Any, Dict, List, Optional, Union
import os

from pydantic import AnyHttpUrl, validator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "GENEM API"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Configurações de ambiente
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # Configurações de logging
    LOG_LEVEL: str = "INFO"
    LOG_TO_FILE: bool = False
    LOG_FILE_PATH: Optional[str] = None
    
    # MongoDB
    MONGODB_CONNECTION_STRING: Optional[str] = os.getenv("MONGODB_CONNECTION_STRING", "mongodb://localhost:27017")
    DATABASE_NAME: Optional[str] = os.getenv("DATABASE_NAME", "genem")
    DATABASE_USER: Optional[str] = None
    DATABASE_PASSWORD: Optional[str] = None
    DATABASE_HOST: Optional[str] = None
    
    # Server
    SERVER_PORT: int = 8000
    
    # JWT
    JWT_PRIVATE_KEY: Optional[str] = None
    JWT_SECRET_KEY: str = "jwt_stub"  # Em produção, deve vir da variável de ambiente
    
    # Admin
    LOGIN: Optional[str] = None
    PASSWORD: Optional[str] = None
    
    # GROQ API
    GROQ_API_KEY: Optional[str] = None
    GROQ_API_TOKENS: Optional[str] = None  # Lista de tokens separados por vírgula
    GROQ_MODEL_NAME: str = "meta-llama/llama-4-scout-17b-16e-instruct" 
    
    def get_groq_tokens(self) -> List[str]:
        """Retorna a lista de tokens GROQ disponíveis"""
        tokens = []
        
        # Adiciona o token principal se existir
        if self.GROQ_API_KEY:
            tokens.append(self.GROQ_API_KEY)
        
        # Adiciona tokens adicionais se existirem
        if self.GROQ_API_TOKENS:
            additional_tokens = [token.strip() for token in self.GROQ_API_TOKENS.split(",") if token.strip()]
            tokens.extend(additional_tokens)
        
        # Remove duplicatas mantendo a ordem
        seen = set()
        unique_tokens = []
        for token in tokens:
            if token not in seen:
                seen.add(token)
                unique_tokens.append(token)
        
        return unique_tokens
    
    # Google ADK
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY", None)
    GOOGLE_MODEL_NAME: Optional[str] = os.getenv("GOOGLE_MODEL_NAME", "gemini-2.0-flash")
    APP_NAME: str = "genem_enem_agent"
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings() 