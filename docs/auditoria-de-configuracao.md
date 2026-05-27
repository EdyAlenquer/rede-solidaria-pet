# Auditoria de Configuração

| Descrição                                         | Ação            |
| ------------------------------------------------- | --------------- |
| As versões dos artefatos estão identificadas?     | (X) sim ( ) não |
| O projeto utiliza controle de versão?             | (X) sim ( ) não |
| Os requisitos funcionais foram revisados?         | (X) sim ( ) não |
| Os requisitos não funcionais estão coerentes?     | (X) sim ( ) não |
| Os diagramas representam corretamente a proposta? | (X) sim ( ) não |
| As ferramentas utilizadas estão documentadas?     | (X) sim ( ) não |
| O documento final foi revisado?                   | (X) sim ( ) não |
| Testes E2E do fluxo principal estão automatizados? | (X) sim ( ) não |
| Auditoria axe-core está automatizada?             | (X) sim ( ) não |
| Lighthouse mobile atende às metas do PRD?         | (X) sim ( ) não |
| Cobertura backend está acima de 80%?              | (X) sim ( ) não |
| Dockerfile do backend está versionado?            | (X) sim ( ) não |
| Compose local com PostgreSQL está versionado?     | (X) sim ( ) não |
| Alvo de deploy e variáveis estão documentados?    | (X) sim ( ) não |
| Smoke test de URLs públicas está automatizado?    | (X) sim ( ) não |

## Evidências de Qualidade — Fase 7

| Verificação                | Comando                                  | Resultado em 27/05/2026                                      |
| -------------------------- | ---------------------------------------- | ------------------------------------------------------------- |
| Testes unitários frontend  | `npm test -- --run`                      | 23 testes passando                                            |
| E2E + axe-core             | `npx playwright test`                    | 20 testes passando em Chromium, Firefox, WebKit e mobile      |
| Lighthouse mobile          | `npm run qa:lighthouse`                  | `/`: 100/100, `/pedidos`: 100/100, `/pedidos/novo`: 100/100, `/pedidos/7`: 97/100 em performance/acessibilidade 100 |
| Cobertura backend          | `uv run pytest --cov=app --cov-report=term-missing` | 96 testes passando, cobertura total 99%                       |
| Deploy versionável         | Revisão de arquivos                     | `backend/Dockerfile`, `compose.yml`, `docs/deploy.md` e `docs/trabalho-final.md` versionados |
| Docker backend             | `docker build -t rede-solidaria-pet-backend:test backend` | Imagem construída com sucesso |
| Manifests de deploy        | `uv run --extra dev pytest tests/integration/test_deploy_manifests.py -q` | `render.yaml` e `frontend/vercel.json` validados |
| Smoke produção             | `FRONTEND_PUBLIC_URL=https://frontend-edyalenquers-projects.vercel.app BACKEND_PUBLIC_URL=https://rede-solidaria-pet-api.onrender.com node scripts/smoke-production.mjs` | `Smoke OK` em 27/05/2026 |
| CORS produção              | `curl -i -X OPTIONS https://rede-solidaria-pet-api.onrender.com/api/v1/pedidos -H 'Origin: https://frontend-edyalenquers-projects.vercel.app' -H 'Access-Control-Request-Method: POST'` | HTTP 200 com `access-control-allow-origin` correto |
