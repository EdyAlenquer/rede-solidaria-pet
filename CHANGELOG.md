# Changelog

Todas as mudanças notáveis deste projeto são documentadas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e o projeto adota [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não lançado]

## [0.2.0] - 2026-06-05

Release de "produção profissional": adiciona contas de usuário, fotos,
localização/mapa, moderação, conformidade com a LGPD, notificações e um conjunto
de medidas de robustez (rate limiting, logging estruturado, readiness, deploy
endurecido), além de testes end-to-end do fluxo autenticado.

### Adicionado

- **Contas e autenticação:** registro, login (JWT HS256), `GET /auth/me`,
  autorização por autor/admin e soft-delete de pedidos.
- **Fotos:** upload de imagens por pedido com storage injetável (`get_storage`),
  limites de tamanho/quantidade e tipos de imagem aceitos; galeria no frontend.
- **Localização e mapa:** campos de cidade, estado e bairro nos pedidos e
  mini-mapa na tela de detalhe.
- **Moderação:** denúncias de pedidos e ações de admin para ocultar, reexibir e
  resolver denúncias.
- **LGPD:** consentimento no cadastro/criação de pedido, exportação dos dados
  pessoais (`GET /me/dados`), anonimização/eliminação da própria conta
  (`DELETE /me`) e por admin, além de páginas legais (privacidade e termos).
- **Notificações:** aviso ao protetor quando um atendimento é registrado, com
  backend `log` (padrão) e `smtp` opcional.
- **Robustez:** rate limiting (slowapi), logging estruturado, cache HTTP em
  respostas públicas, liveness (`/health`) e readiness (`/ready`, com `SELECT 1`).
- **Testes E2E autenticados:** fluxo Playwright registrar → entrar → publicar →
  listar → detalhar → revelar contato → "quero ajudar", com verificações axe
  (WCAG 2 A/AA) nas rotas públicas e nas novas páginas.
- **Documentação:** runbook de operação em `docs/deploy.md` (variáveis de
  ambiente, migração em pré-deploy, rollback, backup/restore do PostgreSQL,
  object storage para fotos em produção, cold start do free tier e rotação de
  segredos).
- **Segurança de pipeline:** varredura de segredos (gitleaks) no CI.

### Modificado

- Migrações Alembic expandidas para `0001`–`0007` (hardening do modelo, campos de
  produto/imagens, status `cancelado`, autenticação, atendimento único por doador
  e moderação).
- Frontend reconstruído em torno de contas, fotos e mapa, com rotas protegidas.
- Deploy endurecido: migrações movidas para `preDeployCommand` (fora do boot do
  container), health-check de produção em `/ready` e `SECRET_KEY` gerada pelo
  provedor (nunca versionada).
- README, `docs/trabalho-final.md` e demais docs atualizados para refletir o
  estado real (contagens de teste, novas features e endpoints, roadmap honesto).

### Segurança

- A revelação de contato passou a exigir autenticação (`GET /pedidos/{id}/contato`).
- Em `APP_ENV=production`, a aplicação recusa subir com a `SECRET_KEY` default
  insegura.

## [0.1.0] - 2026-05-27

### Adicionado

- API FastAPI inicial com pedidos, doadores e atendimentos.
- Persistência SQLAlchemy 2.0 com migrações Alembic e tratamento de erros
  padronizado (RFC 7807).
- SPA React + Vite + TypeScript com telas de home, lista, criação e detalhe de
  pedidos, integrada à API.
- Testes de backend (pytest) e frontend (Vitest), workflows de CI e manifests de
  deploy (`render.yaml`, `frontend/vercel.json`, `compose.yml`).
- Publicação inicial em Render (backend) e Vercel (frontend).

[Não lançado]: https://github.com/edyalenquer/rede-solidaria-pet/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/edyalenquer/rede-solidaria-pet/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/edyalenquer/rede-solidaria-pet/releases/tag/v0.1.0
