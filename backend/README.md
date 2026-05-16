# Backend — Rede Solidária Pet

API REST construída com FastAPI.

## Requisitos

- Python 3.12+
- pip

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

## Executar em desenvolvimento

```bash
uvicorn app.main:app --reload
```

A API sobe em http://127.0.0.1:8000. Documentação interativa em http://127.0.0.1:8000/docs.

## Testes

```bash
pytest -v
```

Com cobertura:

```bash
pytest --cov=app --cov-report=term-missing
```

## Lint e formatação

```bash
ruff check .
black --check .
```

Para corrigir automaticamente:

```bash
ruff check --fix .
black .
```

## Estrutura

```
app/
├─ main.py              # cria a aplicação FastAPI
├─ api/health.py        # health-check (version-agnostic)
├─ api/v1/              # routers versionados (Fase 3+)
├─ models/              # modelos ORM (Fase 2)
├─ schemas/             # schemas Pydantic (Fase 2)
├─ services/            # regras de negócio (Fase 2)
├─ repositories/        # acesso a dados (Fase 2)
└─ core/                # utilidades transversais
```
