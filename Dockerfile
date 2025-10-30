FROM python:3.12.7-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DOCKER=true \
    ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    LOG_TO_FILE=false

# Instalar dependências do sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instalar Poetry
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir poetry==1.6.1

# Copiar arquivos de configuração do Poetry
COPY pyproject.toml poetry.lock README.md /app/

# Configurar o Poetry para não criar um ambiente virtual no contêiner
RUN poetry config virtualenvs.create false

# Instalar dependências
RUN poetry install --no-root

# Copiar o código da aplicação
COPY . /app/

# Expor a porta que o app usa
EXPOSE 8000

# Comando para iniciar a aplicação
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 