#!/bin/bash

# Script para iniciar o ambiente Docker

# Verifica se o Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "Docker não está instalado. Por favor, instale o Docker primeiro."
    exit 1
fi

# Verifica se o Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose não está instalado. Por favor, instale o Docker Compose primeiro."
    exit 1
fi

echo "Iniciando o ambiente Docker..."
docker-compose up -d

echo "Verificando se os serviços estão rodando..."
docker-compose ps

echo "Ambiente Docker iniciado com sucesso!"
echo "Acesse a API em: http://localhost:8000"
echo "Documentação disponível em: http://localhost:8000/docs" 