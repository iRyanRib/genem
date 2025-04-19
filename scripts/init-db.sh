#!/bin/bash

# Script para aplicar migrações e inicializar banco de dados

# Verifica se o Poetry está instalado
if ! command -v poetry &> /dev/null; then
    echo "Poetry não está instalado. Por favor, instale o Poetry primeiro."
    echo "Visite: https://python-poetry.org/docs/#installation"
    exit 1
fi

echo "Garantindo que as dependências estão instaladas..."
poetry install

echo "Verificando conexão com o banco de dados..."
# Verificar se o banco de dados está acessível
DB_CONNECTION_OK=$(poetry run python -c "import psycopg2; from app.core.config import settings; try: conn = psycopg2.connect(host=settings.POSTGRES_SERVER, port=settings.POSTGRES_PORT, dbname=settings.POSTGRES_DB, user=settings.POSTGRES_USER, password=settings.POSTGRES_PASSWORD); conn.close(); print('OK'); except Exception as e: print(str(e))")

if [ "$DB_CONNECTION_OK" != "OK" ]; then
    echo "Erro na conexão com o banco de dados: $DB_CONNECTION_OK"
    echo "Verifique se o PostgreSQL está rodando e as configurações estão corretas."
    exit 1
fi

echo "Aplicando migrações do banco de dados..."
if ! poetry run alembic upgrade head; then
    echo "Erro ao aplicar migrações. Verifique o banco de dados e a configuração do Alembic."
    exit 1
fi
echo "Migrações aplicadas com sucesso!"

echo "Criando dados iniciais..."
if ! poetry run python scripts/create-initial-data.py; then
    echo "Erro ao criar dados iniciais."
    exit 1
fi
echo "Inicialização concluída!" 