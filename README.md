# GENEM API

API REST desenvolvida com FastAPI, Pydantic e SQLAlchemy.

## Tecnologias Utilizadas

- **FastAPI**: Framework web de alta performance
- **Pydantic**: Validação de dados baseada em tipos Python
- **SQLAlchemy**: ORM para interação com o banco de dados
- **Alembic**: Sistema de migrações para o SQLAlchemy
- **PostgreSQL**: Banco de dados relacional
- **Poetry**: Gerenciamento de dependências e pacotes
- **Docker/Docker Compose**: Contêinerização e orquestração

## Estrutura do Projeto

```
genem/
│
├── app/                    # Pacote principal da aplicação
│   ├── api/                # Endpoints da API
│   │   ├── dependencies/   # Dependências da API (segurança, etc.)
│   │   └── endpoints/      # Rotas da API
│   ├── core/               # Configurações centrais da aplicação
│   ├── db/                 # Configuração do banco de dados
│   ├── models/             # Modelos SQLAlchemy
│   ├── schemas/            # Schemas Pydantic para validação
│   ├── services/           # Camada de serviço para lógica de negócios
│   └── utils/              # Utilitários gerais
│
├── migrations/             # Migrações do Alembic
├── scripts/                # Scripts utilitários
├── .env                    # Variáveis de ambiente (não versionado)
├── .env.example            # Exemplo de variáveis de ambiente
├── alembic.ini             # Configuração do Alembic
├── docker-compose.yml      # Configuração do Docker Compose
├── Dockerfile              # Configuração do Docker
├── docker-entrypoint.sh    # Script de entrada para Docker
├── main.py                 # Ponto de entrada da aplicação
├── Makefile                # Comandos úteis para desenvolvimento
├── pyproject.toml          # Configuração do Poetry
└── README.md               # Este arquivo
```

## Configuração do Ambiente de Desenvolvimento

### Usando Make e Poetry

Este projeto usa um Makefile para simplificar os comandos comuns. Para ver todos os comandos disponíveis:

```bash
make help
```

#### Configuração Rápida (recomendada)

```bash
# Configurar o ambiente, instalar dependências e executar localmente
make run-local
```

#### Configuração passo a passo

1. Instale o Poetry: https://python-poetry.org/docs/#installation
2. Clone o repositório
3. Configure o ambiente:
   ```bash
   make setup
   ```
4. Aplique as migrações no banco de dados:
   ```bash
   make migrate
   ```
5. Execute o servidor de desenvolvimento:
   ```bash
   make dev
   ```

### Usando Docker

#### Execução rápida (para desenvolvimento)

```bash
make run-docker
```

#### Execução em background

```bash
make docker-up
```

Para parar os contêineres:
```bash
make docker-down
```

## Migrações de Banco de Dados

### Criando uma nova migração

```bash
poetry run alembic revision --autogenerate -m "Descrição da migração"
```

### Aplicando migrações

```bash
make migrate
```

## Testes e Linting

Para executar os testes:

```bash
make test
```

Para executar os linters (black, isort, flake8):

```bash
make lint
```

## Documentação da API

Após iniciar o servidor, acesse:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Usuário Padrão

Para facilitar os testes, um usuário administrador é criado automaticamente:

- Email: admin@example.com
- Senha: admin123

## Resolução de Problemas

### Erro de conexão com o banco de dados

Certifique-se de que o PostgreSQL está instalado e rodando:

```bash
sudo systemctl status postgresql
```

Se não estiver instalado:

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

Para iniciar o serviço:

```bash
sudo systemctl start postgresql
```

### Falta de dependências Python

Se houver problemas com dependências:

```bash
make install
```

Isso garantirá que o arquivo `poetry.lock` esteja atualizado e todas as dependências sejam instaladas corretamente.
