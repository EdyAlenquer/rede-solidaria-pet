# Deploy

## Alvo definido

| Camada | Plataforma sugerida | Motivo |
| ------ | ------------------- | ------ |
| Backend | Render Web Service | Suporte simples a Dockerfile, variáveis de ambiente e health-check HTTP. |
| Banco | Render PostgreSQL | PostgreSQL gerenciado no mesmo provedor do backend. |
| Frontend | Vercel | Deploy direto de Vite, HTTPS automático e configuração simples de variável `VITE_API_BASE_URL`. |

## Variáveis de ambiente

### Backend

| Variável | Exemplo | Descrição |
| -------- | ------- | --------- |
| `APP_ENV` | `production` | Ambiente de execução. |
| `LOG_LEVEL` | `INFO` | Nível de log. |
| `DATABASE_URL` | `postgresql+psycopg://user:pass@host:5432/db` | URL SQLAlchemy do PostgreSQL. |
| `CORS_ORIGINS` | `https://rede-solidaria-pet.vercel.app` | Origens autorizadas a consumir a API. |

### Frontend

| Variável | Exemplo | Descrição |
| -------- | ------- | --------- |
| `VITE_API_BASE_URL` | `https://rede-solidaria-pet-api.onrender.com/api/v1` | Base URL pública da API. |

## Procedimento

1. Criar o PostgreSQL gerenciado e copiar a connection string.
2. Criar o serviço backend usando `/render.yaml` ou `/backend/Dockerfile`.
3. Configurar `DATABASE_URL`, `APP_ENV`, `LOG_LEVEL` e `CORS_ORIGINS` no backend.
4. Rodar `alembic upgrade head` antes de servir a aplicação.
5. Criar o projeto frontend apontando para `/frontend`.
6. Configurar `VITE_API_BASE_URL` no frontend com a URL pública do backend.
7. Validar `/health`, `/api/v1/pedidos`, fluxo principal e HTTPS.

## Smoke test de produção

Depois de publicar backend e frontend, rode:

```bash
FRONTEND_PUBLIC_URL=https://rede-solidaria-pet.vercel.app \
BACKEND_PUBLIC_URL=https://rede-solidaria-pet-api.onrender.com \
node scripts/smoke-production.mjs
```

O mesmo gate está disponível manualmente no GitHub Actions em `Production Smoke`.

## Manifests versionados

- `render.yaml`: declara o Web Service Docker do backend e o PostgreSQL gerenciado.
- `frontend/vercel.json`: declara build Vite, diretório de saída e rewrite SPA do frontend.

## Desenvolvimento com containers

```bash
docker compose up --build
```

Serviços locais:

- Backend: `http://127.0.0.1:8000`
- PostgreSQL: `127.0.0.1:5432`
