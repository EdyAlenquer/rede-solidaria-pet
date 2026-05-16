# Rede Solidária Pet

> ⚠️ **Trabalho em andamento.** Este repositório contém um projeto acadêmico em desenvolvimento. As partes prontas e as pendentes estão listadas em [Status do projeto](#status-do-projeto) abaixo.

Plataforma web simples para centralizar pedidos de ajuda e doações para animais em situação de rua, conectando protetores independentes, ONGs e doadores voluntários da comunidade local.

## Objetivo

Reduzir a fricção entre quem precisa de ajuda (protetor) e quem pode oferecer (doador/voluntário), com uma interface acessível e responsiva.

## Setor de aplicação

Comunidade local, protetores independentes e ONGs de proteção animal.

## ODS atendidos

- ODS 3 – Saúde e Bem-estar
- ODS 11 – Cidades e Comunidades Sustentáveis
- ODS 15 – Vida Terrestre

---

## Status do projeto

O desenvolvimento está organizado em 8 fases — veja o [PRD completo](PRD.md). Estado atual:

| Fase | Nome                                       | Status        |
| ---- | ------------------------------------------ | ------------- |
| 1    | Estrutura do Projeto                       | ✅ Concluída  |
| 2    | Modelagem e Persistência (Backend)         | ✅ Concluída  |
| 3    | API REST — Pedidos                         | ✅ Concluída  |
| 4    | API REST — Atendimentos e Doadores         | ⏳ Pendente   |
| 5    | Frontend — Fundação                        | ⏳ Pendente   |
| 6    | Frontend — Telas Principais                | ⏳ Pendente   |
| 7    | Qualidade, Acessibilidade e Testes         | ⏳ Pendente   |
| 8    | Deploy, Auditoria e Entrega                | ⏳ Pendente   |

### O que já está pronto

**Backend (`backend/`)**
- API FastAPI funcional, executável localmente.
- Modelo de dados completo: `PedidoAjuda`, `DoadorVoluntario`, `AtendimentoPedido` (SQLAlchemy 2.0 + SQLite/PostgreSQL).
- Migrações Alembic.
- Endpoints REST de pedidos com paginação, filtros (status, urgência, categoria, busca textual) e regras de transição de status.
- Tratamento de erros padronizado (RFC 7807 — `application/problem+json`).
- 75 testes (unitários + integração) passando.

**Frontend (`frontend/`)**
- Scaffold Vite + React + TypeScript com tela placeholder.
- Lint (ESLint) e formatação (Prettier) configurados.
- Telas reais e integração com a API ainda não foram desenvolvidas.

**Infraestrutura**
- Workflows de CI no GitHub Actions para backend e frontend.
- `Makefile` com atalhos de desenvolvimento.

### O que ainda falta

- Endpoints REST de atendimentos e doadores (Fase 4).
- Toda a interface de usuário e integração frontend ↔ backend (Fases 5 e 6).
- Acessibilidade, testes E2E, auditorias de performance (Fase 7).
- Deploy em ambiente público e fechamento do relatório acadêmico (Fase 8).

---

## Stack tecnológica

| Camada          | Tecnologia                                  |
| --------------- | ------------------------------------------- |
| Backend         | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic |
| Banco (dev)     | SQLite                                      |
| Banco (prod)    | PostgreSQL (planejado)                      |
| Frontend        | React 18, Vite, TypeScript                  |
| Testes          | pytest, Vitest, React Testing Library       |
| Qualidade       | ruff, black, ESLint, Prettier               |
| CI              | GitHub Actions                              |

Lista completa em [`docs/ferramentas-utilizadas.md`](docs/ferramentas-utilizadas.md).

---

## Como executar localmente

**Pré-requisitos:** Python 3.12+, Node 20+, npm 10+.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

- API disponível em http://127.0.0.1:8000
- Documentação interativa em http://127.0.0.1:8000/docs

Mais detalhes em [`backend/README.md`](backend/README.md).

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

- App em http://localhost:5173 (atualmente exibe apenas placeholder)

Mais detalhes em [`frontend/README.md`](frontend/README.md).

### Atalhos via Makefile

```bash
make help            # lista todos os targets
make dev-backend     # sobe a API
make dev-frontend    # sobe o Vite
make test            # roda testes back + front
make lint            # roda lint back + front
```

---

## Endpoints disponíveis (Fase 3)

| Método | Rota                                  | Descrição                                       |
| ------ | ------------------------------------- | ----------------------------------------------- |
| GET    | `/health`                             | Health-check do serviço                         |
| POST   | `/api/v1/pedidos`                     | Cria um pedido de ajuda                         |
| GET    | `/api/v1/pedidos`                     | Lista pedidos (filtros + paginação)             |
| GET    | `/api/v1/pedidos/{id}`                | Detalha um pedido                               |
| PATCH  | `/api/v1/pedidos/{id}/status`         | Atualiza o status (com regras de transição)     |

---

## Estrutura do repositório

```
rede-solidaria-pet/
├─ PRD.md                       # documento de requisitos completo
├─ Makefile
├─ README.md
├─ docs/                        # diagramas, requisitos, ferramentas, auditoria
│  ├─ diagramas/
│  ├─ requisitos/
│  ├─ superpowers/plans/        # planos de implementação por fase
│  ├─ ferramentas-utilizadas.md
│  └─ auditoria-de-configuracao.md
├─ backend/                     # API FastAPI (em uso)
└─ frontend/                    # SPA Vite + React (scaffold)
```

---

## Documentação relacionada

- [PRD.md](PRD.md) — visão completa do produto e roadmap em fases
- [`docs/requisitos/`](docs/requisitos/) — requisitos funcionais, não funcionais e baseline
- [`docs/diagramas/`](docs/diagramas/) — diagrama de atividades e diagrama de classes
- [`docs/auditoria-de-configuracao.md`](docs/auditoria-de-configuracao.md) — checklist de auditoria
- [`docs/ferramentas-utilizadas.md`](docs/ferramentas-utilizadas.md) — stack e justificativas
