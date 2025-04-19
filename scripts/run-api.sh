#!/bin/bash

# Script para iniciar o servidor FastAPI em desenvolvimento

# Verifica se o Poetry está instalado
if ! command -v poetry &> /dev/null; then
    echo "Poetry não está instalado. Por favor, instale o Poetry primeiro."
    echo "Visite: https://python-poetry.org/docs/#installation"
    exit 1
fi

# Ativa o ambiente virtual e inicia o servidor
echo "Iniciando servidor FastAPI..."
poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload 