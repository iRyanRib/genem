# GENEM API

API REST desenvolvida com FastAPI e Pydantic.

## Tecnologias Utilizadas

- **FastAPI**: Framework web de alta performance
- **Pydantic**: Validação de dados baseada em tipos Python
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
│   ├── schemas/            # Schemas Pydantic para validação
│   ├── services/           # Camada de serviço para lógica de negócios
│   └── utils/              # Utilitários gerais
│
├── scripts/                # Scripts utilitários
├── .env                    # Variáveis de ambiente (não versionado)
├── .env.example            # Exemplo de variáveis de ambiente
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
4. Execute o servidor de desenvolvimento:
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

## Autenticação

Para facilitar os testes, um usuário administrador é criado automaticamente:

- Email: admin@example.com
- Senha: admin

## Resolução de Problemas

### Falta de dependências Python

Se houver problemas com dependências:

```bash
make install
```

Isso garantirá que o arquivo `poetry.lock` esteja atualizado e todas as dependências sejam instaladas corretamente.
