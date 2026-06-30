# PRD — Rede Solidária Pet

| Campo                | Valor                                                                 |
| -------------------- | --------------------------------------------------------------------- |
| Produto              | Rede Solidária Pet                                                    |
| Versão do documento  | 1.0                                                                   |
| Data                 | 16/05/2026                                                            |
| Responsável          | Equipe do projeto                                                     |
| Status               | Concluído                                                             |
| Repositório          | rede-solidaria-pet                                                    |

## 1. Visão Geral

A Rede Solidária Pet é uma plataforma web simples cujo objetivo é centralizar pedidos de ajuda e doações para animais em situação de rua, conectando protetores independentes, ONGs e doadores voluntários da comunidade local.

A solução prioriza simplicidade, acessibilidade e responsividade em dispositivos móveis, de modo a permitir que pessoas com pouca familiaridade com tecnologia possam registrar e atender pedidos com poucos passos.

## 2. Objetivos

- Disponibilizar um canal público para cadastro e visualização de pedidos de ajuda a animais.
- Reduzir a fricção entre quem precisa de ajuda (protetor) e quem pode oferecer (doador/voluntário).
- Servir como base de aprendizado e entrega acadêmica, com artefatos auditáveis (requisitos, diagramas, checklist).

## 3. Alinhamento com ODS

| ODS | Tema                                       | Como o projeto contribui                                                  |
| --- | ------------------------------------------ | ------------------------------------------------------------------------- |
| 3   | Saúde e Bem-estar                          | Reduzindo sofrimento animal e riscos sanitários associados                |
| 11  | Cidades e Comunidades Sustentáveis         | Fortalecendo redes locais de cuidado                                      |
| 15  | Vida Terrestre                             | Promovendo proteção de espécies e bem-estar animal                        |

## 4. Público-alvo

- Protetores independentes que precisam divulgar casos pontuais.
- ONGs que organizam campanhas e doações.
- Doadores e voluntários da comunidade local.

## 5. Escopo

### 5.1 Dentro do escopo (MVP)

- Cadastro de pedidos de ajuda (categoria, descrição, urgência, contato).
- Listagem pública e filtrável de pedidos.
- Detalhamento do pedido com forma de contato.
- Atualização de status do pedido (aberto, em andamento, concluído).
- Registro de atendimentos por doadores/voluntários.

### 5.2 Fora do escopo (não-MVP)

- Autenticação social/OAuth.
- Sistema de pagamento integrado.
- Notificações em tempo real (push/SMS).
- Aplicativo mobile nativo.
- Moderação assistida por IA.

## 6. Requisitos

### 6.1 Requisitos Funcionais

| Código | Requisito                                                  |
| ------ | ---------------------------------------------------------- |
| RF01   | Permitir cadastrar pedidos de ajuda                        |
| RF02   | Permitir informar categoria, descrição, urgência e contato |
| RF03   | Exibir lista pública de pedidos                            |
| RF04   | Permitir filtrar pedidos                                   |
| RF05   | Exibir detalhes do pedido                                  |
| RF06   | Permitir atualizar o status do pedido                      |
| RF07   | Permitir marcar como aberto, em andamento ou concluído     |
| RF08   | Permitir visualizar a forma de contato do responsável      |

### 6.2 Requisitos Não Funcionais

| Código | Requisito                                              |
| ------ | ------------------------------------------------------ |
| RNF01  | Interface simples e intuitiva                          |
| RNF02  | Responsivo para celular                                |
| RNF03  | Bom contraste e legibilidade                           |
| RNF04  | Preservação da privacidade dos dados                   |
| RNF05  | Navegação com poucos passos                            |
| RNF06  | Carregamento adequado em rede móvel                    |
| RNF07  | Compatibilidade com navegadores modernos               |
| RNF08  | Linguagem clara e acessível                            |

## 7. Modelo de Domínio

Resumido do diagrama de classes (`docs/diagramas/diagrama-classes.mermaid`):

- **PedidoAjuda**: `id`, `titulo`, `descricao`, `urgencia`, `status`, `dataCriacao`
- **DoadorVoluntario**: `id`, `nome`, `telefone`, `email`
- **AtendimentoPedido**: `id`, `dataContato`, `tipoAjuda`, `observacao`

Relacionamentos:

- `PedidoAjuda 1 — 0..* AtendimentoPedido` (recebe)
- `DoadorVoluntario 1 — 0..* AtendimentoPedido` (realiza)

## 8. Métricas de Sucesso

| Métrica                                | Meta inicial                  |
| -------------------------------------- | ----------------------------- |
| Tempo médio para cadastrar um pedido   | ≤ 2 minutos                   |
| Pedidos atendidos / pedidos abertos    | ≥ 50% em 30 dias              |
| Lighthouse Mobile — Performance        | ≥ 80                          |
| Lighthouse Mobile — Acessibilidade     | ≥ 90                          |
| Compatibilidade de navegadores         | Últimas 2 versões major       |

---

# Roadmap em Fases

O desenvolvimento é dividido em 8 fases sequenciais. Cada fase tem entregáveis, critérios de aceite e dependências explícitas.

| Fase | Nome                                       | Duração estimada |
| ---- | ------------------------------------------ | ----------------:|
| 1    | Estrutura do Projeto                       | 2 dias           |
| 2    | Modelagem e Persistência (Backend)         | 3 dias           |
| 3    | API REST — Pedidos                         | 4 dias           |
| 4    | API REST — Atendimentos e Doadores         | 3 dias           |
| 5    | Frontend — Fundação                        | 3 dias           |
| 6    | Frontend — Telas Principais                | 5 dias           |
| 7    | Qualidade, Acessibilidade e Testes         | 4 dias           |
| 8    | Deploy, Auditoria e Entrega                | 3 dias           |

---

## Fase 1 — Estrutura do Projeto

> **Pré-requisito de todas as demais fases.** Nenhum código de produto deve ser escrito antes desta fase estar concluída.

### 1.1 Objetivo

Estabelecer a base do repositório, definir a arquitetura, escolher as versões das tecnologias e criar a estrutura de pastas que servirá tanto ao backend (FastAPI) quanto ao frontend (React).

### 1.2 Stack tecnológica

Baseada em `docs/ferramentas-utilizadas.md`:

| Camada           | Tecnologia      | Versão alvo  | Observação                                       |
| ---------------- | --------------- | ------------ | ------------------------------------------------ |
| Backend          | Python          | 3.12+        | Linguagem do backend                             |
| Backend          | FastAPI         | 0.110+       | Framework HTTP                                   |
| Backend          | Uvicorn         | 0.29+        | Servidor ASGI                                    |
| Backend          | SQLAlchemy      | 2.0+         | ORM                                              |
| Backend          | Pydantic        | 2.x          | Validação de dados                               |
| Backend          | Alembic         | 1.13+        | Migrações de banco                               |
| Banco (dev)      | SQLite          | 3.x          | Simplicidade no ambiente local                   |
| Banco (prod)     | PostgreSQL      | 15+          | Opcional para deploy                             |
| Frontend         | React           | 18+          | Biblioteca de UI                                 |
| Frontend         | Vite            | 5+           | Build e dev server                               |
| Frontend         | React Router    | 6+           | Roteamento client-side                           |
| Frontend         | Axios           | 1.x          | Cliente HTTP                                     |
| Estilo           | CSS Modules     | nativo       | Sem dependência adicional para o MVP             |
| Testes (back)    | pytest          | 8.x          | Testes unitários e de integração                 |
| Testes (front)   | Vitest + RTL    | última       | Testes de componentes                            |
| Qualidade        | ruff, black     | última       | Lint e formatação (Python)                       |
| Qualidade        | eslint, prettier| última       | Lint e formatação (JS)                           |
| Versionamento    | Git + GitHub    | —            | Workflow trunk-based                             |
| Gestão           | Trello          | —            | Kanban                                           |
| Diagramas        | Mermaid, draw.io| —            | Diagramas de classes e atividades                |
| CI               | GitHub Actions  | —            | Lint, testes e build                             |

### 1.3 Arquitetura

Padrão **monorepo** com dois aplicativos independentes que se comunicam via HTTP/JSON:

```
┌────────────────────────────┐         HTTP/JSON        ┌────────────────────────────┐
│   Frontend (React/Vite)    │ ───────────────────────▶ │   Backend (FastAPI)        │
│   - SPA                    │                          │   - REST API               │
│   - Camada de serviços     │ ◀─────────────────────── │   - Camada service/repo    │
└────────────────────────────┘                          │   - SQLAlchemy + SQLite    │
                                                        └────────────────────────────┘
```

Backend segue arquitetura em camadas:

```
HTTP (routers) → Schemas (Pydantic) → Services (regra de negócio) → Repositories → ORM (SQLAlchemy) → DB
```

Frontend segue separação por feature:

```
pages → components → hooks → services (API) → utils
```

### 1.4 Estrutura de pastas

```
rede-solidaria-pet/
├─ README.md
├─ PRD.md
├─ .gitignore
├─ .editorconfig
├─ .github/
│  └─ workflows/
│     ├─ backend-ci.yml
│     └─ frontend-ci.yml
├─ docs/
│  ├─ auditoria-de-configuracao.md
│  ├─ ferramentas-utilizadas.md
│  ├─ checklists/
│  ├─ diagramas/
│  └─ requisitos/
├─ backend/
│  ├─ pyproject.toml
│  ├─ README.md
│  ├─ .env.example
│  ├─ alembic.ini
│  ├─ alembic/
│  │  └─ versions/
│  ├─ app/
│  │  ├─ __init__.py
│  │  ├─ main.py
│  │  ├─ config.py
│  │  ├─ database.py
│  │  ├─ api/
│  │  │  ├─ __init__.py
│  │  │  ├─ deps.py
│  │  │  └─ v1/
│  │  │     ├─ __init__.py
│  │  │     ├─ pedidos.py
│  │  │     ├─ atendimentos.py
│  │  │     └─ doadores.py
│  │  ├─ models/
│  │  │  ├─ __init__.py
│  │  │  ├─ pedido.py
│  │  │  ├─ atendimento.py
│  │  │  └─ doador.py
│  │  ├─ schemas/
│  │  │  ├─ __init__.py
│  │  │  ├─ pedido.py
│  │  │  ├─ atendimento.py
│  │  │  └─ doador.py
│  │  ├─ services/
│  │  │  ├─ __init__.py
│  │  │  ├─ pedido_service.py
│  │  │  ├─ atendimento_service.py
│  │  │  └─ doador_service.py
│  │  ├─ repositories/
│  │  │  ├─ __init__.py
│  │  │  ├─ pedido_repository.py
│  │  │  ├─ atendimento_repository.py
│  │  │  └─ doador_repository.py
│  │  └─ core/
│  │     ├─ __init__.py
│  │     ├─ logging.py
│  │     └─ errors.py
│  └─ tests/
│     ├─ conftest.py
│     ├─ unit/
│     └─ integration/
└─ frontend/
   ├─ package.json
   ├─ vite.config.ts
   ├─ tsconfig.json
   ├─ README.md
   ├─ .env.example
   ├─ index.html
   ├─ public/
   └─ src/
      ├─ main.tsx
      ├─ App.tsx
      ├─ router.tsx
      ├─ pages/
      │  ├─ HomePage/
      │  ├─ PedidoNovoPage/
      │  ├─ PedidoListaPage/
      │  └─ PedidoDetalhePage/
      ├─ components/
      │  ├─ layout/
      │  ├─ form/
      │  └─ pedido/
      ├─ hooks/
      ├─ services/
      │  └─ api/
      │     ├─ client.ts
      │     ├─ pedidos.ts
      │     ├─ atendimentos.ts
      │     └─ doadores.ts
      ├─ types/
      ├─ styles/
      └─ utils/
```

### 1.5 Tarefas

| ID    | Tarefa                                                                              |
| ----- | ----------------------------------------------------------------------------------- |
| T1.1  | Criar estrutura de pastas `backend/` e `frontend/` conforme item 1.4                |
| T1.2  | Inicializar `pyproject.toml` com dependências do backend                            |
| T1.3  | Inicializar `package.json` (Vite + React + TS) no frontend                          |
| T1.4  | Configurar `.editorconfig`, `.gitignore` e arquivos `.env.example`                  |
| T1.5  | Configurar ruff, black, eslint e prettier                                           |
| T1.6  | Criar workflows GitHub Actions (lint, testes, build) para back e front              |
| T1.7  | Adicionar READMEs específicos em `backend/` e `frontend/` com instruções de setup   |
| T1.8  | Validar que `make dev` (ou equivalente) sobe back e front localmente sem erros      |

### 1.6 Critérios de aceite

- [x] Estrutura de pastas criada e versionada.
- [x] `uvicorn app.main:app --reload` sobe um endpoint `/health` retornando 200.
- [x] `npm run dev` sobe o Vite com a tela inicial vazia.
- [x] CI passa em PR de exemplo (lint + build).
- [x] Documentação de setup no README do backend e do frontend.

---

## Fase 2 — Modelagem e Persistência (Backend)

### 2.1 Objetivo

Implementar o modelo de dados conforme diagrama de classes, com persistência via SQLAlchemy + migrações Alembic.

### 2.2 Entregáveis

- Modelos ORM: `PedidoAjuda`, `AtendimentoPedido`, `DoadorVoluntario`.
- Schemas Pydantic correspondentes (Create, Update, Read).
- Configuração de sessão de banco e injeção de dependência.
- Migração inicial gerada por Alembic.
- Camada de repositório com operações CRUD básicas.

### 2.3 Tarefas

| ID    | Tarefa                                                                              |
| ----- | ----------------------------------------------------------------------------------- |
| T2.1  | Definir `Base` declarativa e sessão (`SessionLocal`, `get_db`)                      |
| T2.2  | Criar modelos `PedidoAjuda`, `AtendimentoPedido`, `DoadorVoluntario`                |
| T2.3  | Criar enums para `urgencia` (baixa, media, alta) e `status`                         |
| T2.4  | Criar schemas Pydantic Create/Update/Read                                           |
| T2.5  | Configurar Alembic e gerar migração inicial                                         |
| T2.6  | Implementar repositórios com testes unitários                                       |

### 2.4 Critérios de aceite

- [x] `alembic upgrade head` cria o schema sem erros em SQLite.
- [x] Cobertura de testes dos repositórios ≥ 80%.
- [x] Constraints de integridade (FKs, NOT NULL) validadas.
- [x] Atende RF02 a nível de dados.

### 2.5 Dependências

Fase 1 concluída.

---

## Fase 3 — API REST: Pedidos

### 3.1 Objetivo

Expor endpoints REST que cobrem o ciclo de vida de um pedido de ajuda.

### 3.2 Endpoints

| Método | Rota                              | Requisito |
| ------ | --------------------------------- | --------- |
| POST   | `/api/v1/pedidos`                 | RF01, RF02|
| GET    | `/api/v1/pedidos`                 | RF03, RF04|
| GET    | `/api/v1/pedidos/{id}`            | RF05, RF08|
| PATCH  | `/api/v1/pedidos/{id}/status`     | RF06, RF07|

Filtros suportados em `GET /pedidos`: `categoria`, `urgencia`, `status`, `q` (texto livre), `page`, `page_size`.

### 3.3 Tarefas

| ID    | Tarefa                                                                              |
| ----- | ----------------------------------------------------------------------------------- |
| T3.1  | Implementar `pedido_service` com regras de transição de status                      |
| T3.2  | Implementar router `pedidos.py` com validação de entrada                            |
| T3.3  | Implementar paginação e filtros                                                     |
| T3.4  | Tratamento de erros padronizado (`ProblemDetails` ou similar)                       |
| T3.5  | Testes de integração cobrindo todos os endpoints                                    |
| T3.6  | Documentação automática via OpenAPI (verificar `/docs`)                             |

### 3.4 Critérios de aceite

- [x] Todos os endpoints cobrem RF01 a RF08 quando aplicável.
- [x] Transições inválidas de status retornam 409.
- [x] Filtros combinados retornam resultados corretos em testes.
- [x] Documentação OpenAPI gerada sem warnings.

### 3.5 Dependências

Fase 2 concluída.

---

## Fase 4 — API REST: Atendimentos e Doadores

### 4.1 Objetivo

Suportar o registro de atendimentos a pedidos por parte de doadores/voluntários.

### 4.2 Endpoints

| Método | Rota                                              | Descrição                                |
| ------ | ------------------------------------------------- | ---------------------------------------- |
| POST   | `/api/v1/doadores`                                | Cadastra doador/voluntário               |
| GET    | `/api/v1/doadores/{id}`                           | Consulta doador (uso administrativo)     |
| POST   | `/api/v1/pedidos/{pedido_id}/atendimentos`        | Registra atendimento                     |
| GET    | `/api/v1/pedidos/{pedido_id}/atendimentos`        | Lista atendimentos de um pedido          |

### 4.3 Tarefas

| ID    | Tarefa                                                                              |
| ----- | ----------------------------------------------------------------------------------- |
| T4.1  | Implementar `doador_service` e router correspondente                                |
| T4.2  | Implementar `atendimento_service` com vínculo a pedido e doador                     |
| T4.3  | Regra: ao registrar atendimento, mover pedido para "em andamento" se "aberto"       |
| T4.4  | Testes de integração para fluxo completo (pedido → atendimento → status)            |
| T4.5  | Política mínima de privacidade: ocultar e-mail/telefone em rotas públicas (RNF04)   |

### 4.4 Critérios de aceite

- [x] Atendimento só pode ser criado para pedido existente e não concluído.
- [x] Pedido transita de "aberto" para "em andamento" no primeiro atendimento.
- [x] Doadores não são listados publicamente.

### 4.5 Dependências

Fase 3 concluída.

---

## Fase 5 — Frontend: Fundação

### 5.1 Objetivo

Preparar o aplicativo React para receber as telas principais com base sólida de roteamento, estilo e cliente HTTP.

### 5.2 Tarefas

| ID    | Tarefa                                                                              |
| ----- | ----------------------------------------------------------------------------------- |
| T5.1  | Configurar React Router com rotas placeholder para todas as páginas                 |
| T5.2  | Criar layout base (header, footer, container responsivo)                            |
| T5.3  | Configurar Axios com `baseURL` por variável de ambiente                             |
| T5.4  | Tipar contratos de API em `src/types/`                                              |
| T5.5  | Criar tema CSS com paleta acessível (contraste ≥ 4.5:1 — RNF03)                     |
| T5.6  | Componentes base: `Button`, `Input`, `Select`, `Card`, `Badge`                      |
| T5.7  | Hook `useApi` para padronizar loading/erro                                          |

### 5.3 Critérios de aceite

- [x] Navegação entre rotas placeholder funciona sem recarregar página.
- [x] Layout responsivo verificado em 320px, 768px e 1280px (RNF02).
- [x] Componentes base têm exemplos no Storybook ou em uma página `__playground__`.

### 5.4 Dependências

Fase 1 concluída. Pode ser desenvolvida em paralelo com Fases 2–4.

---

## Fase 6 — Frontend: Telas Principais

### 6.1 Páginas

| Página                | Rota                          | Requisitos cobertos       |
| --------------------- | ----------------------------- | ------------------------- |
| Home                  | `/`                           | RNF01, RNF08              |
| Novo Pedido           | `/pedidos/novo`               | RF01, RF02                |
| Lista de Pedidos      | `/pedidos`                    | RF03, RF04                |
| Detalhe do Pedido     | `/pedidos/:id`                | RF05, RF06, RF07, RF08    |

### 6.2 Tarefas

| ID    | Tarefa                                                                              |
| ----- | ----------------------------------------------------------------------------------- |
| T6.1  | Implementar formulário de novo pedido com validação client-side                     |
| T6.2  | Implementar lista paginada com filtros (categoria, urgência, status, busca)         |
| T6.3  | Implementar página de detalhe com bloco de contato e histórico de atendimentos      |
| T6.4  | Implementar ação de "Quero ajudar" que cria atendimento                             |
| T6.5  | Mensagens de erro e estados vazios em linguagem clara (RNF08)                       |
| T6.6  | Skeleton/placeholder para evitar layout shift (RNF06)                               |

### 6.3 Critérios de aceite

- [x] Fluxo "cadastrar → listar → detalhar → atender" funciona ponta a ponta.
- [x] Filtros são refletidos na URL (compartilháveis).
- [x] Nenhum dado sensível (e-mail/telefone bruto) aparece sem clique explícito.

### 6.4 Dependências

Fases 4 e 5 concluídas.

---

## Fase 7 — Qualidade, Acessibilidade e Testes

### 7.1 Objetivo

Garantir que o produto atenda aos requisitos não funcionais e a um padrão mínimo de qualidade técnica.

### 7.2 Tarefas

| ID    | Tarefa                                                                              |
| ----- | ----------------------------------------------------------------------------------- |
| T7.1  | Auditoria Lighthouse mobile em todas as páginas (meta no item 8 do PRD)             |
| T7.2  | Revisão A11y com axe-core (foco, labels, contraste, ordem de tabulação)             |
| T7.3  | Testes E2E com Playwright cobrindo o fluxo principal                                |
| T7.4  | Cobertura backend ≥ 80% (services e routers)                                        |
| T7.5  | Revisão de copy: linguagem clara e acessível (RNF08)                                |
| T7.6  | Teste de uso em rede 3G simulada (Chrome devtools) — RNF06                          |
| T7.7  | Testes em últimas 2 versões de Chrome, Firefox, Safari e Edge — RNF07               |

### 7.3 Critérios de aceite

- [x] Lighthouse mobile ≥ 80 (perf) e ≥ 90 (a11y).
- [x] Sem erros críticos no axe-core.
- [x] E2E principal verde no CI.
- [x] Checklist de auditoria de configuração (`docs/auditoria-de-configuracao.md`) atualizado.

### 7.4 Dependências

Fase 6 concluída.

---

## Fase 8 — Deploy, Auditoria e Entrega

### 8.1 Objetivo

Publicar a aplicação, formalizar a entrega e fechar a documentação para o trabalho final.

### 8.2 Tarefas

| ID    | Tarefa                                                                              |
| ----- | ----------------------------------------------------------------------------------- |
| T8.1  | Configurar build de produção do frontend (Vite)                                     |
| T8.2  | Containerizar backend (Dockerfile) e definir `compose` para dev                     |
| T8.3  | Definir alvo de deploy (Render/Fly/Railway para back; Vercel/Netlify para front)    |
| T8.4  | Provisionar banco PostgreSQL gerenciado para produção                               |
| T8.5  | Configurar variáveis de ambiente, segredos e CORS                                   |
| T8.6  | Rodar checklist `docs/auditoria-de-configuracao.md` e arquivar evidências           |
| T8.7  | Atualizar `docs/requisitos/baseline.md` com versões pós-deploy                      |
| T8.8  | Escrita do Trabalho Final (relatório acadêmico) a partir do PRD e da execução       |

### 8.3 Critérios de aceite

- [x] URL pública acessível, com HTTPS.
- [x] Backend e frontend automatizados via CI/CD em push para `main`.
- [x] Auditoria de configuração 100% "sim".
- [x] Documentos finais versionados e referenciados no README.

### 8.4 Dependências

Fase 7 concluída.

---

## Anexos

### A. Cronograma macro

Reflete o diagrama de atividades (`docs/diagramas/diagrama-atividades.png`):

| Etapa                                          | Duração   | Fase do PRD |
| ---------------------------------------------- | --------- | ----------- |
| Levantamento de necessidades                   | 7 dias    | Pré-PRD     |
| Definição de escopo e requisitos               | 4 dias    | Pré-PRD     |
| Protótipo de telas                             | 3 dias    | Fase 5/6    |
| Validação com protetor + doador                | 3 dias    | Fase 6/7    |
| Desenvolvimento do MVP                         | 14 dias   | Fases 1–6   |
| Testes e ajustes                               | 5 dias    | Fase 7      |
| Revisão de acessibilidade e linguagem          | 3 dias    | Fase 7      |
| Deploy/Entrega do sistema                      | 7 dias    | Fase 8      |
| Escrita do Trabalho Final                      | 10 dias   | Fase 8      |

### B. Referências internas

- `README.md` — visão geral
- `docs/ferramentas-utilizadas.md` — stack
- `docs/auditoria-de-configuracao.md` — checklist de auditoria
- `docs/requisitos/baseline.md` — versões dos artefatos
- `docs/requisitos/requisitos-funcionais.md`
- `docs/requisitos/requisitos-nao-funcionais.md`
- `docs/diagramas/diagrama-atividades.png`
- `docs/diagramas/diagrama-classes.png`
- `docs/diagramas/diagrama-classes.mermaid`

### C. Riscos e mitigações

| Risco                                              | Impacto | Mitigação                                                  |
| -------------------------------------------------- | ------- | ---------------------------------------------------------- |
| Dados de contato expostos publicamente             | Alto    | Mascarar e exigir clique para revelar (RNF04)              |
| Spam de pedidos                                    | Médio   | Rate limit por IP e validação de campos obrigatórios       |
| Curva de aprendizado do FastAPI/React              | Médio   | Fase 1 dedicada à fundação + READMEs de setup              |
| Indisponibilidade do banco em deploy gratuito      | Médio   | Healthcheck + retry simples + plano de migração documentado|
| Acessibilidade aquém da meta                       | Médio   | Auditoria contínua já a partir da Fase 5                   |

### D. Glossário

- **Pedido de ajuda**: registro público criado por um protetor descrevendo uma necessidade pontual.
- **Atendimento**: ação registrada por um doador/voluntário em resposta a um pedido.
- **Doador/voluntário**: pessoa que oferece algum tipo de ajuda (transporte, ração, abrigo, recursos).
- **MVP**: versão mínima viável que cobre RF01–RF08.
