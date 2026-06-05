# Trabalho Final — Rede Solidária Pet

## Resumo

A Rede Solidária Pet é uma aplicação web para centralizar pedidos de ajuda a animais em situação de rua ou vulnerabilidade. O MVP conecta protetores, ONGs e doadores por meio de cadastro de pedidos, listagem filtrável, detalhe com contato protegido e registro de atendimentos.

## Escopo implementado

- API FastAPI com contas, pedidos, fotos, doadores, atendimentos, denúncias e estatísticas.
- Autenticação JWT (registro/login/me), autorização por autor/admin e soft-delete.
- Upload de imagens com storage injetável (`get_storage`) e localização (cidade/estado/bairro).
- Moderação (denúncias, ocultar/reexibir, resolução por admin) e LGPD (consentimento, exportação e anonimização de conta).
- Notificações ao protetor (backend `log` por padrão, `smtp` opcional), rate limiting e logging estruturado.
- Persistência SQLAlchemy com migrações Alembic (`0001`–`0007`).
- Interface React/Vite responsiva em português com contas, galeria de fotos, mini-mapa e páginas legais.
- Fluxo principal autenticado: registrar, entrar, publicar pedido, listar, detalhar, revelar contato e ajudar.
- Proteção de contato até autenticação e clique explícito.
- Testes unitários, integração, E2E e acessibilidade (Playwright + axe-core).
- Configuração de deploy por Docker, PostgreSQL e variáveis de ambiente.
- Manifests `render.yaml` e `frontend/vercel.json` para provisionamento em Render/Vercel.

## Requisitos atendidos

| Grupo | Evidência |
| ----- | --------- |
| RF01–RF08 | Endpoints e telas principais implementados. |
| RNF01–RNF05 | Layout simples, responsivo, com navegação curta e contato protegido. |
| RNF06 | Acessibilidade verificada com axe-core (WCAG 2 A/AA) nas rotas públicas e autenticáveis. |
| RNF07 | Playwright em Chromium, Firefox, WebKit e viewport mobile (Pixel 5). |
| RNF08 | Copy de interface e validação em linguagem clara em PT-BR. |

## Validação

| Verificação | Resultado |
| ----------- | --------- |
| Backend | 339 testes pytest (unitários + integração) passando. |
| Frontend | 87 testes Vitest passando. |
| E2E/A11y | 28 testes Playwright/axe passando (7 testes × 4 browsers). |

## Limitações e próximos passos

- O upload de fotos usa storage local (`/uploads`), **efêmero no free tier do Render**;
  produção real exige object storage (Cloudinary/R2/S3) plugado em `get_storage`.
- O free tier do Render não faz backup automático do PostgreSQL e hiberna (cold start);
  produção pede plano pago e/ou `pg_dump` agendado.
- O fluxo E2E autenticado roda localmente; sua execução completa em CI ainda não está
  configurada.
- Anti-abuso limita-se a rate limiting; um captcha no cadastro/criação é um próximo passo.
- URLs públicas com HTTPS validadas em Render e Vercel.
- O teste em Edge é representado pelo motor Chromium; validação manual no Microsoft Edge
  fica para o fechamento operacional do deploy.
