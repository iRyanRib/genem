.PHONY: install dev docker-up docker-down test lint migrate setup run-local run-docker clean help

# Instalar dependências
install:
	poetry lock
	poetry install

# Configurar ambiente
setup: install
	cp -n .env.example .env || true
	@echo "Configuração concluída! Ajuste o arquivo .env conforme necessário."

# Iniciar servidor de desenvolvimento
dev:
	poetry run python main.py

# Executar localmente sem Docker
run-local: setup migrate
	poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Iniciar contêineres Docker
docker-up:
	./scripts/docker-start.sh

# Executar via Docker
run-docker:
	docker-compose down -v || true
	docker-compose build
	docker-compose up

# Parar contêineres Docker
docker-down:
	docker-compose down

# Rodar testes
test:
	poetry run pytest

# Rodar linters
lint:
	poetry run black .
	poetry run isort .
	poetry run flake8 .

# Aplicar migrações
migrate:
	./scripts/init-db.sh

# Limpar arquivos temporários
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/

# Ajuda
help:
	@echo "Comandos disponíveis:"
	@echo "  make install     - Instalar dependências"
	@echo "  make setup       - Configurar ambiente inicial"
	@echo "  make dev         - Iniciar servidor de desenvolvimento"
	@echo "  make run-local   - Executar localmente (instala deps, aplica migrações e executa)"
	@echo "  make docker-up   - Iniciar contêineres Docker e deixar rodando em background"
	@echo "  make run-docker  - Reconstruir e executar Docker em primeiro plano (útil para debug)"
	@echo "  make docker-down - Parar contêineres Docker"
	@echo "  make test        - Executar testes"
	@echo "  make lint        - Executar linters"
	@echo "  make migrate     - Aplicar migrações"
	@echo "  make clean       - Limpar arquivos temporários" 