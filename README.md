# Rede Solidária Pet

Plataforma web simples para centralizar pedidos de ajuda e doações para animais em situação de rua, conectando protetores independentes, ONGs e doadores voluntários da comunidade local.

Projeto acadêmico **concluído** e publicado: backend em produção no Render, frontend na Vercel. As 8 fases do plano estão entregues — veja o [Status do projeto](#status-do-projeto).

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

O desenvolvimento foi organizado em 8 fases — veja o [PRD completo](PRD.md). **Todas concluídas:**

| Fase | Nome                                       | Status        |
| ---- | ------------------------------------------ | ------------- |
| 1    | Estrutura do Projeto                       | ✅ Concluída  |
| 2    | Modelagem e Persistência (Backend)         | ✅ Concluída  |
| 3    | API REST — Pedidos                         | ✅ Concluída  |
| 4    | API REST — Atendimentos e Doadores         | ✅ Concluída  |
| 5    | Frontend — Fundação                        | ✅ Concluída  |
| 6    | Frontend — Telas Principais                | ✅ Concluída  |
| 7    | Qualidade, Acessibilidade e Testes         | ✅ Concluída  |
| 8    | Deploy, Auditoria e Entrega                | ✅ Concluída  |

### O que já está pronto

**Backend (`backend/`)**
- API FastAPI funcional, executável localmente.
- Modelo de dados completo: `Usuario`, `PedidoAjuda`, `DoadorVoluntario`, `AtendimentoPedido`, `ImagemPedido`, `Denuncia` (SQLAlchemy 2.0 + SQLite/PostgreSQL).
- Migrações Alembic (`0001`–`0007`).
- **Contas e autenticação:** registro, login (JWT HS256), `me`, autorização por autor/admin e soft-delete de pedidos.
- **Fotos:** upload de imagens por pedido com storage injetável (`get_storage`), limites de tamanho/quantidade e tipos aceitos.
- **Localização:** cidade, estado e bairro nos pedidos (alimentam o mapa no frontend).
- **Moderação:** denúncias de pedidos, ocultar/reexibir e resolução de denúncias por admin.
- **LGPD:** consentimento no cadastro, exportação dos dados pessoais (`/me/dados`) e anonimização/eliminação de conta.
- **Notificações:** aviso ao protetor quando um atendimento é registrado (backend `log` por padrão, `smtp` opcional).
- Endpoints REST de pedidos com paginação, filtros (status, urgência, categoria, busca textual, cidade/estado) e regras de transição de status.
- Endpoints REST de doadores e atendimentos, com transição automática do pedido para `em_andamento` no primeiro atendimento.
- Revelação de contato protegida por autenticação (`/pedidos/{id}/contato`).
- Hardening: rate limiting (slowapi), logging estruturado, CORS configurável e cache HTTP em respostas públicas.
- Tratamento de erros padronizado (RFC 7807 — `application/problem+json`).
- Liveness (`/health`) e readiness (`/ready`, com `SELECT 1`).
- 364 testes (unitários + integração) passando.

**Frontend (`frontend/`)**
- SPA Vite + React + TypeScript com roteamento principal e rotas protegidas.
- Layout base responsivo inspirado em um protótipo visual de referência.
- **Contas:** telas de cadastro e login, sessão autenticada e logout.
- Telas reais de home, lista, criação, edição e detalhe de pedidos.
- **Fotos:** envio e galeria de imagens nos pedidos.
- **Mapa/localização:** mini-mapa no detalhe e campos de cidade/estado/bairro.
- **LGPD:** consentimento no cadastro/pedido e páginas legais (privacidade, termos).
- **Quero ajudar:** registro de atendimento autenticado sem expor o doador; revelação de contato sob clique.
- Analytics privacy-first (Plausible) opcional, desativado por padrão.
- Integração com a API para auth, pedidos, imagens, doadores e atendimentos.
- Estados de carregamento, erro, vazio e validação client-side em português.
- Testes unitários (Vitest + Testing Library), E2E e acessibilidade (Playwright + axe) cobrindo o fluxo autenticado e as rotas públicas.
- Lint (ESLint) e formatação (Prettier) configurados.
- 107 testes (Vitest) passando.

**Infraestrutura**
- Workflows de CI no GitHub Actions para backend, frontend, smoke de produção e varredura de segredos.
- `Makefile` com atalhos de desenvolvimento.
- Manifests versionados: `render.yaml` (backend + banco gerenciado), `frontend/vercel.json`, `compose.yml`.
- Migrações Alembic aplicadas no start do container e health-check de readiness (`/ready`).
- **Object storage** S3-compatível (Cloudflare R2) para as fotos em produção; disco local em desenvolvimento.
- Backend publicado em https://rede-solidaria-pet-api.onrender.com.
- Frontend publicado em https://rede-solidaria-pet.vercel.app.

### Trabalho futuro (evolução para produção em escala)

O escopo acadêmico está **concluído e publicado**. Os itens abaixo ficam registrados
como evolução natural caso o projeto siga para uma operação de produção em escala:

- **Tier pago + backups:** o free tier hiberna (cold start) e tem retenção de backup
  limitada. Subir para plano pago e/ou agendar `pg_dump` próprio.
- **Captcha / anti-abuso:** complementar o rate limiting com captcha no cadastro e na
  criação de pedidos.
- **Cobertura explícita do Microsoft Edge:** o fluxo Playwright autenticado já roda em CI
  em Chromium, Firefox e WebKit; falta apenas validar o Edge explicitamente (hoje coberto
  pelo motor Chromium).
- **Notificações por e-mail em produção:** configurar `NOTIFIER_BACKEND=smtp` com um
  provedor real (hoje o default `log` apenas registra).

---

## Stack tecnológica

| Camada          | Tecnologia                                  |
| --------------- | ------------------------------------------- |
| Backend         | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic |
| Banco (dev)     | SQLite                                      |
| Banco (prod)    | PostgreSQL (Neon)                           |
| Storage (prod)  | Object storage S3-compatível (Cloudflare R2)|
| Auth            | JWT (HS256), Argon2                          |
| Frontend        | React 18, Vite, TypeScript                  |
| Testes          | pytest, Vitest, Testing Library, Playwright + axe |
| Qualidade       | ruff, black, ESLint, Prettier, gitleaks     |
| CI / Deploy     | GitHub Actions, Render, Vercel              |

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

- App em http://localhost:5173

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

## Endpoints disponíveis

A documentação interativa completa fica em `/docs` (Swagger UI) quando a API está rodando.

**Saúde**

| Método | Rota      | Descrição                                       |
| ------ | --------- | ----------------------------------------------- |
| GET    | `/health` | Liveness do serviço                             |
| GET    | `/ready`  | Readiness (valida o banco com `SELECT 1`)       |

**Autenticação e conta (LGPD)**

| Método | Rota                  | Descrição                                       |
| ------ | --------------------- | ----------------------------------------------- |
| POST   | `/api/v1/auth/registro` | Registra um novo usuário (protetor)           |
| POST   | `/api/v1/auth/login`    | Autentica e retorna um access token (JWT)     |
| GET    | `/api/v1/auth/me`       | Retorna o usuário autenticado                 |
| GET    | `/api/v1/me/dados`      | Exporta os dados pessoais do usuário (LGPD)   |
| DELETE | `/api/v1/me`            | Anonimiza e elimina a própria conta (LGPD)    |

**Pedidos**

| Método | Rota                          | Descrição                                       |
| ------ | ----------------------------- | ----------------------------------------------- |
| POST   | `/api/v1/pedidos`             | Cria um pedido de ajuda (autenticado)           |
| GET    | `/api/v1/pedidos`             | Lista pedidos (filtros + paginação)             |
| GET    | `/api/v1/pedidos/{id}`        | Detalha um pedido                               |
| GET    | `/api/v1/pedidos/{id}/contato`| Revela o contato (requer autenticação)          |
| PATCH  | `/api/v1/pedidos/{id}`        | Edita um pedido (somente autor ou admin)        |
| PATCH  | `/api/v1/pedidos/{id}/status` | Atualiza o status (somente autor ou admin)      |
| DELETE | `/api/v1/pedidos/{id}`        | Remove um pedido (soft-delete; autor ou admin)  |

**Fotos**

| Método | Rota                                | Descrição                                       |
| ------ | ----------------------------------- | ----------------------------------------------- |
| POST   | `/api/v1/pedidos/{id}/imagens`      | Envia uma imagem (somente autor ou admin)       |
| GET    | `/api/v1/pedidos/{id}/imagens`      | Lista as imagens de um pedido                   |
| DELETE | `/api/v1/pedidos/{id}/imagens/{imagemId}` | Remove uma imagem (somente autor ou admin) |

**Atendimentos, doadores e denúncias**

| Método | Rota                                  | Descrição                                       |
| ------ | ------------------------------------- | ----------------------------------------------- |
| POST   | `/api/v1/pedidos/{id}/atendimentos`   | Registra atendimento                            |
| GET    | `/api/v1/pedidos/{id}/atendimentos`   | Lista atendimentos de um pedido                 |
| POST   | `/api/v1/pedidos/{id}/denuncias`      | Denuncia um pedido (requer autenticação)        |
| POST   | `/api/v1/doadores`                    | Cadastra doador/voluntário                      |
| GET    | `/api/v1/doadores/{id}`               | Consulta doador (restrito a admin)              |

**Estatísticas e moderação (admin)**

| Método | Rota                                          | Descrição                              |
| ------ | --------------------------------------------- | -------------------------------------- |
| GET    | `/api/v1/estatisticas`                        | Estatísticas públicas agregadas        |
| GET    | `/api/v1/admin/denuncias`                     | Lista todas as denúncias (admin)       |
| PATCH  | `/api/v1/admin/pedidos/{id}/ocultar`          | Oculta um pedido (admin)               |
| PATCH  | `/api/v1/admin/pedidos/{id}/reexibir`         | Reexibe um pedido ocultado (admin)     |
| PATCH  | `/api/v1/admin/denuncias/{id}/resolver`       | Resolve uma denúncia (admin)           |
| DELETE | `/api/v1/admin/usuarios/{id}`                 | Anonimiza e elimina um usuário (admin) |

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
│  ├─ deploy.md
│  ├─ trabalho-final.md
│  ├─ ferramentas-utilizadas.md
│  └─ auditoria-de-configuracao.md
├─ backend/                     # API FastAPI
└─ frontend/                    # SPA Vite + React
```

---

## Documentação relacionada

- [PRD.md](PRD.md) — visão completa do produto e roadmap em fases
- [`docs/deploy.md`](docs/deploy.md) — alvo de deploy, variáveis e procedimento
- [`docs/trabalho-final.md`](docs/trabalho-final.md) — síntese acadêmica da entrega
- [`docs/requisitos/`](docs/requisitos/) — requisitos funcionais, não funcionais e baseline
- [`docs/diagramas/`](docs/diagramas/) — diagrama de atividades e diagrama de classes
- [`docs/auditoria-de-configuracao.md`](docs/auditoria-de-configuracao.md) — checklist de auditoria
- [`docs/ferramentas-utilizadas.md`](docs/ferramentas-utilizadas.md) — stack e justificativas
