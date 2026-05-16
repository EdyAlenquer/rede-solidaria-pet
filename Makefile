.PHONY: help install-backend install-frontend dev dev-backend dev-frontend test test-backend test-frontend lint lint-backend lint-frontend

help:
	@echo "Targets disponíveis:"
	@echo "  install-backend   - instala dependências Python (modo editable)"
	@echo "  install-frontend  - instala dependências Node"
	@echo "  dev-backend       - sobe FastAPI com reload"
	@echo "  dev-frontend      - sobe Vite em modo dev"
	@echo "  test-backend      - executa pytest"
	@echo "  test-frontend     - executa vitest"
	@echo "  dev               - sobe backend e frontend simultaneamente"
	@echo "  lint              - executa lint em backend e frontend"

install-backend:
	cd backend && pip install -e ".[dev]"

install-frontend:
	cd frontend && npm install

dev-backend:
	cd backend && uvicorn app.main:app --reload

dev-frontend:
	cd frontend && npm run dev

test-backend:
	cd backend && pytest -v

test-frontend:
	cd frontend && npm run test

lint-backend:
	cd backend && ruff check . && black --check .

lint-frontend:
	cd frontend && npm run lint

dev: dev-backend dev-frontend
lint: lint-backend lint-frontend
test: test-backend test-frontend
