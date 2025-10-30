import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import api_router
from app.core.config import settings
from app.core.logging_config import setup_production_logging, setup_development_logging, get_logger

# Configurar logging baseado no ambiente
if os.getenv("ENVIRONMENT", "development") == "production" or os.getenv("DOCKER", "false").lower() == "true":
    # Configuração para produção/Docker
    setup_production_logging()
else:
    # Configuração para desenvolvimento
    setup_development_logging()

logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

@app.on_event("startup")
async def startup_event():
    """Evento executado na inicialização da aplicação."""
    logger.info(f"🚀 Iniciando {settings.PROJECT_NAME}")
    logger.info(f"📊 Ambiente: {settings.ENVIRONMENT}")
    logger.info(f"🔧 Debug: {settings.DEBUG}")
    logger.info(f"📝 Log Level: {settings.LOG_LEVEL}")
    logger.info(f"🤖 Google Model: {settings.GOOGLE_MODEL_NAME}")
    logger.info(f"🗄️ Database: {settings.DATABASE_NAME}")

@app.on_event("shutdown")
async def shutdown_event():
    """Evento executado no encerramento da aplicação."""
    logger.info(f"🛑 Encerrando {settings.PROJECT_NAME}")

# Configurar CORS - Modo permissivo para desenvolvimento
logger.info("🌐 Configurando CORS em modo permissivo para desenvolvimento")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todas as origens em desenvolvimento
    allow_credentials=True,  # Permitir credentials para autenticação
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
)

# Incluir rotas da API
app.include_router(api_router, prefix=settings.API_V1_STR)
logger.info(f"📡 Rotas da API registradas em {settings.API_V1_STR}")
