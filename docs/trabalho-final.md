# Trabalho Final — Rede Solidária Pet

## Resumo

A Rede Solidária Pet é uma aplicação web para centralizar pedidos de ajuda a animais em situação de rua ou vulnerabilidade. O MVP conecta protetores, ONGs e doadores por meio de cadastro de pedidos, listagem filtrável, detalhe com contato protegido e registro de atendimentos.

## Escopo implementado

- API FastAPI com pedidos, doadores e atendimentos.
- Persistência SQLAlchemy com migrações Alembic.
- Interface React/Vite responsiva em português.
- Fluxo principal: cadastrar, listar, detalhar e atender pedido.
- Proteção de contato até clique explícito.
- Testes unitários, integração, E2E, axe-core e Lighthouse mobile.
- Configuração de deploy por Docker, PostgreSQL e variáveis de ambiente.
- Manifests `render.yaml` e `frontend/vercel.json` para provisionamento em Render/Vercel.

## Requisitos atendidos

| Grupo | Evidência |
| ----- | --------- |
| RF01–RF08 | Endpoints e telas principais implementados. |
| RNF01–RNF05 | Layout simples, responsivo, com navegação curta e contato protegido. |
| RNF06 | Lighthouse mobile em build de produção com performance ≥ 97 nas rotas auditadas. |
| RNF07 | Playwright em Chromium, Firefox, WebKit e viewport mobile. |
| RNF08 | Copy de interface e validação em linguagem clara em PT-BR. |

## Validação

| Verificação | Resultado |
| ----------- | --------- |
| Backend | 96 testes passando, cobertura total 99%. |
| Frontend | 23 testes Vitest passando. |
| E2E/A11y | 20 testes Playwright/axe passando. |
| Lighthouse | `/`: 100, `/pedidos`: 100, `/pedidos/novo`: 100, `/pedidos/7`: 97 em performance; acessibilidade 100. |

## Limitações

- A URL pública com HTTPS depende do provisionamento efetivo nas plataformas de deploy.
- O teste em Edge é representado pelo motor Chromium no CI; validação manual no Microsoft Edge deve ser feita no fechamento operacional do deploy.
