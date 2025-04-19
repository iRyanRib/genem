#!/bin/bash
set -e

# Esperar o banco de dados estar pronto
echo "Esperando o banco de dados iniciar..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_SERVER -U $POSTGRES_USER -d $POSTGRES_DB -c '\q'; do
  echo "Banco de dados ainda não está disponível - aguardando..."
  sleep 2
done
echo "Banco de dados está disponível!"

# Executar migrações
echo "Executando migrações do banco de dados..."
alembic upgrade head

# Criar dados iniciais
echo "Criando dados iniciais..."
python scripts/create-initial-data.py

echo "Tudo pronto! Iniciando aplicação..."
exec "$@" 