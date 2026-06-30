# Trabalho Final — Rede Solidária Pet

## Resumo

A Rede Solidária Pet é uma aplicação web para centralizar pedidos de ajuda a animais em situação de rua ou vulnerabilidade. O MVP conecta protetores, ONGs e doadores por meio de cadastro de pedidos, listagem filtrável, detalhe com contato protegido e registro de atendimentos.

## Escopo implementado

- API FastAPI com contas, pedidos, fotos, doadores, atendimentos, denúncias e estatísticas.
- Autenticação JWT (registro/login/me), autorização por autor/admin e soft-delete.
- Upload de imagens com storage injetável (`get_storage`): object storage S3-compatível (Cloudflare R2) em produção e disco local em desenvolvimento, além de localização (cidade/estado/bairro).
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
| Backend | 364 testes pytest (unitários + integração) passando. |
| Frontend | 107 testes Vitest passando. |
| E2E/A11y | 28 testes Playwright/axe passando (7 testes × 4 browsers). |

## Limitações e próximos passos

- As fotos são servidas por object storage S3-compatível (Cloudflare R2) em produção,
  já superando o disco efêmero do free tier; um domínio/CDN próprio seria o passo seguinte.
- O free tier (API no Render, banco no Neon) hiberna (cold start) e tem retenção de backup
  limitada; produção em escala pede plano pago e/ou `pg_dump` agendado.
- O fluxo E2E autenticado roda localmente; sua execução completa em CI ainda não está
  configurada.
- Anti-abuso limita-se a rate limiting; um captcha no cadastro/criação é um próximo passo.
- URLs públicas com HTTPS validadas em Render e Vercel.
- O teste em Edge é representado pelo motor Chromium; validação manual no Microsoft Edge
  fica para o fechamento operacional do deploy.
