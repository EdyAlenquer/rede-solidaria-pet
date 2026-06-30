# Deploy

## Alvo definido

| Camada | Plataforma sugerida | Motivo |
| ------ | ------------------- | ------ |
| Backend | Render Web Service | Suporte simples a Dockerfile, variáveis de ambiente e health-check HTTP. |
| Banco | Neon Postgres (serverless) | PostgreSQL gerenciado, free tier permanente. A API segue no Render e aponta o `DATABASE_URL` para o Neon (endpoint direto, sem `-pooler`). |
| Frontend | Vercel | Deploy direto de Vite, HTTPS automático e configuração simples de variável `VITE_API_BASE_URL`. |

## URLs publicadas

| Camada | URL |
| ------ | --- |
| Backend | `https://rede-solidaria-pet-api.onrender.com` |
| Frontend | `https://rede-solidaria-pet.vercel.app` |

## Variáveis de ambiente

### Backend

| Variável | Obrigatória | Exemplo | Descrição |
| -------- | ----------- | ------- | --------- |
| `APP_ENV` | Sim | `production` | Ambiente de execução. Em `production`, o app recusa subir com a `SECRET_KEY` default insegura. |
| `LOG_LEVEL` | Não (default `INFO`) | `INFO` | Nível de log estruturado. |
| `DATABASE_URL` | Sim | `postgresql+psycopg://user:pass@host:5432/db` | URL SQLAlchemy do PostgreSQL. Use o driver `psycopg` (v3). |
| `CORS_ORIGINS` | Sim (em prod) | `https://rede-solidaria-pet.vercel.app` | Origens autorizadas a consumir a API (lista separada por vírgulas). |
| `SECRET_KEY` | Sim (em prod) | `<32+ bytes aleatórios>` | Chave de assinatura JWT (HS256). No Render use `generateValue: true`; nunca versione. |
| `WEB_CONCURRENCY` | Não (default `2`) | `2` | Número de workers do Uvicorn. Ajuste conforme as CPUs do plano. |
| `JWT_ALGORITHM` | Não (default `HS256`) | `HS256` | Algoritmo de assinatura JWT. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Não (default `1440`) | `1440` | Validade do access token em minutos. |
| `RATE_LIMIT_ENABLED` | Não (default `true`) | `true` | Liga/desliga o rate limiting (slowapi). |
| `RATE_LIMIT_AUTH` | Não (default `5/minute`) | `5/minute` | Limite das rotas de autenticação. |
| `RATE_LIMIT_CREATE` | Não (default `30/minute`) | `30/minute` | Limite das rotas de criação (pedidos, imagens, atendimentos, denúncias). |
| `RATE_LIMIT_CONTATO` | Não (default `30/minute`) | `30/minute` | Limite da revelação de contato. |
| `NOTIFIER_BACKEND` | Não (default `log`) | `smtp` | Backend de notificação ao protetor. `log` apenas registra no logging; `smtp` envia e-mail real. |
| `SMTP_HOST` | Quando `smtp` | `smtp.exemplo.com` | Host do servidor SMTP. |
| `SMTP_PORT` | Não (default `587`) | `587` | Porta SMTP (submissão com STARTTLS). |
| `SMTP_USER` | Não | `no-reply@exemplo.com` | Usuário de autenticação SMTP. |
| `SMTP_PASSWORD` | Não | `<segredo>` | Senha de autenticação SMTP. |
| `SMTP_FROM` | Quando `smtp` | `Rede Solidária Pet <no-reply@exemplo.com>` | Remetente dos e-mails. |
| `SMTP_TLS` | Não (default `true`) | `true` | Usa STARTTLS na conexão SMTP. |
| `STORAGE_BACKEND` | Não (default `local`) | `s3` | Backend de storage das imagens. `local` grava em disco (**efêmero no Render**); `s3` grava em object storage S3-compatível (veja Object storage). |
| `S3_BUCKET` | Quando `s3` | `rede-solidaria-pet` | Nome do bucket de destino. |
| `S3_ENDPOINT_URL` | Quando `s3` em R2/MinIO/Supabase | `https://<ACCOUNT_ID>.r2.cloudflarestorage.com` | Endpoint do serviço S3-compatível. Vazio usa a AWS. |
| `S3_REGION` | Não (default `auto`) | `auto` | Região do bucket. `auto` no R2; região real na AWS (ex.: `us-east-1`). |
| `S3_ACCESS_KEY_ID` | Quando `s3` | `<token>` | Access key id do token S3. **Segredo** — defina no dashboard, nunca versione. |
| `S3_SECRET_ACCESS_KEY` | Quando `s3` | `<segredo>` | Secret access key do token S3. **Segredo** — defina no dashboard, nunca versione. |
| `S3_PUBLIC_BASE_URL` | Quando `s3` | `https://pub-xxxxxxxx.r2.dev` | Base pública/CDN onde os objetos são servidos (prefixo das URLs salvas). |
| `S3_PREFIX` | Não (default `pedidos`) | `pedidos` | Prefixo (pseudo-pasta) das chaves dos objetos no bucket. |
| `UPLOAD_DIR` | Não (default `uploads`) | `uploads` | Diretório do `LocalStorageBackend` (só quando `STORAGE_BACKEND=local`). **Efêmero no Render** (veja Object storage). |
| `PUBLIC_UPLOAD_PATH` | Não (default `/uploads`) | `/uploads` | Prefixo público sob o qual as imagens locais são servidas. |
| `MAX_UPLOAD_BYTES` | Não (default `5242880`) | `5242880` | Tamanho máximo por imagem em bytes (5 MiB). |
| `MAX_IMAGENS_POR_PEDIDO` | Não (default `6`) | `6` | Número máximo de imagens por pedido. |

### Frontend

| Variável | Obrigatória | Exemplo | Descrição |
| -------- | ----------- | ------- | --------- |
| `VITE_API_BASE_URL` | Sim | `https://rede-solidaria-pet-api.onrender.com/api/v1` | Base URL pública da API. |
| `VITE_PLAUSIBLE_DOMAIN` | Não | `redesolidariapet.com.br` | Domínio registrado no Plausible. Vazio/ausente desativa o tracking (privacy-first, sem cookies, LGPD). |

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

- `render.yaml`: declara o Web Service Docker do backend. O `DATABASE_URL` é definido como
  segredo no dashboard (aponta para o Neon), e não por um banco gerenciado pelo Render.
- `frontend/vercel.json`: declara build Vite, diretório de saída e rewrite SPA do frontend.

## Armazenamento de fotos em produção

O backend grava as imagens enviadas através de uma abstração de storage
(`app/core/storage.py`), selecionável por `STORAGE_BACKEND`:

- `local` (default): `LocalStorageBackend` grava em disco (`UPLOAD_DIR`) e serve
  via `StaticFiles`. **No Render free o disco é efêmero**: as fotos somem a cada
  deploy/restart e não são compartilhadas entre workers. Bom para desenvolvimento,
  inadequado para produção.
- `s3`: `S3StorageBackend` grava em object storage S3-compatível (Cloudflare R2,
  AWS S3, Supabase Storage, MinIO). Durável e compartilhado entre instâncias.

### Cloudflare R2 (recomendado)

R2 é S3-compatível, tem franquia gratuita generosa e **não cobra egress**.

1. **Criar o bucket.** No painel da Cloudflare → R2 → *Create bucket* (ex.:
   `rede-solidaria-pet`). Anote o **Account ID** (aparece na URL e no painel R2).
2. **Habilitar acesso público.** No bucket → *Settings* → *Public access*:
   - Opção simples: habilite o subdomínio **r2.dev** (gera uma base pública
     `https://pub-<HASH>.r2.dev`). Use essa URL em `S3_PUBLIC_BASE_URL`.
   - Opção com domínio próprio: conecte um *Custom Domain* (ex.:
     `https://fotos.seudominio.com.br`) e use-o em `S3_PUBLIC_BASE_URL`.
   - O app **não** aplica ACL `public-read` no upload (o R2 não suporta ACLs); a
     visibilidade pública vem exclusivamente desse acesso público do bucket.
3. **Criar um API token S3.** R2 → *Manage R2 API Tokens* → *Create API token*
   com permissão *Object Read & Write* no bucket. Guarde o **Access Key ID** e o
   **Secret Access Key** (o secret só aparece uma vez).
4. **Endpoint S3 do R2:** `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`.
5. **Configurar as variáveis** (no dashboard do Render; segredos **nunca**
   versionados — em `render.yaml` ficam como `sync: false`):

   ```
   STORAGE_BACKEND=s3
   S3_BUCKET=rede-solidaria-pet
   S3_ENDPOINT_URL=https://<ACCOUNT_ID>.r2.cloudflarestorage.com
   S3_REGION=auto
   S3_ACCESS_KEY_ID=<access key id do token>
   S3_SECRET_ACCESS_KEY=<secret access key do token>
   S3_PUBLIC_BASE_URL=https://pub-<HASH>.r2.dev   # ou o domínio próprio
   S3_PREFIX=pedidos
   ```

6. **Redeploy** e validar um upload: a URL retornada deve começar por
   `S3_PUBLIC_BASE_URL` e a imagem deve abrir publicamente nessa URL.

> AWS S3 / MinIO / Supabase Storage seguem o mesmo esquema: ajuste
> `S3_ENDPOINT_URL` (vazio para AWS), `S3_REGION` (região real na AWS) e a base
> pública/CDN em `S3_PUBLIC_BASE_URL`.

### Alternativa: Cloudinary

[Cloudinary](https://cloudinary.com/) é um SaaS de mídia (não é S3-compatível;
exige um backend de storage próprio, ainda não implementado). Oferece um plano
gratuito, CDN, transformações on-the-fly (resize/crop/otimização) e entrega em
formatos modernos. É uma opção quando além de armazenar você quer processamento
de imagem gerenciado; para apenas armazenar de forma durável, o R2 acima é mais
simples e já suportado pelo `S3StorageBackend`.

## Desenvolvimento com containers

```bash
docker compose up --build
```

Serviços locais:

- Backend: `http://127.0.0.1:8000`
- PostgreSQL: `127.0.0.1:5432`

---

# Runbook de operação

## Migrações em pré-deploy

As migrações Alembic (`0001`–`0007`) são aplicadas **antes de o servidor atender
requisições**. Onde isso acontece depende do plano:

- **Render free tier:** o `preDeployCommand` **não roda em planos gratuitos**, então o
  `Dockerfile` aplica `alembic upgrade head` no **start do container** (uma vez, antes do
  Uvicorn forkar os workers — sem corrida em instância única).
- **Render plano pago:** `preDeployCommand: alembic upgrade head` (declarado em
  `render.yaml`) roda contra o `DATABASE_URL` da release antes de promover a instância; o
  `alembic upgrade head` do start vira no-op (idempotente). Em escala (múltiplas
  instâncias), prefira o preDeploy para evitar migrações concorrentes.
- **Docker Compose / outro host:** rode a migração explicitamente antes de subir o
  servidor:

  ```bash
  DATABASE_URL=postgresql+psycopg://user:pass@host:5432/db \
    alembic upgrade head
  ```

- **Verificação:** o health-check de produção é `/ready`, que executa `SELECT 1`. O
  Render só roteia tráfego depois que `/ready` responde `200`, garantindo que o banco
  migrado está acessível.

Boas práticas:

- Sempre escreva migrações compatíveis com a versão anterior do código (expand/contract)
  para permitir rollback sem perda de dados.
- Nunca edite uma migração já aplicada em produção; crie uma nova.
- Teste a migração localmente contra um banco descartável antes de promover:

  ```bash
  rm -f /tmp/mig_check.db && \
    DATABASE_URL=sqlite:////tmp/mig_check.db alembic upgrade head
  ```

## Rollback

Reverter uma release problemática tem duas partes — **código** e **esquema** — que devem
ser revertidas na ordem correta.

1. **Reverter o esquema** (somente se a release subiu uma migração nova):

   ```bash
   # Volta uma revisão (use o id da revisão anterior para alvo explícito):
   DATABASE_URL=postgresql+psycopg://user:pass@host:5432/db \
     alembic downgrade -1
   # ou para uma revisão específica:
   DATABASE_URL=... alembic downgrade 0006
   ```

   > Só faça downgrade se a migração da release for destrutiva ou incompatível com a
   > versão anterior do código. Migrações expand-only (apenas adição) normalmente podem
   > ficar no lugar, e o código antigo as ignora.

2. **Redeployar a versão anterior do código:**
   - **Render:** no painel, abra a aba **Deploys**, selecione o deploy anterior bom e
     use **Redeploy** / **Rollback to this deploy**. Como `autoDeploy: true` está ligado,
     desabilite-o temporariamente ou faça `git revert` do commit problemático e empurre,
     para evitar que o Render reaplique a versão ruim.
   - **Frontend (Vercel):** use **Instant Rollback** no painel para promover o build
     anterior.

3. **Confirmar:** rode o smoke test de produção (seção abaixo) e valide `/ready`,
   `/api/v1/pedidos` e o fluxo principal.

## Backup e restore do PostgreSQL

> **Limitação do free tier:** o banco usado em produção é o **Neon Postgres** (free tier
> permanente, mas com retenção de backup/PITR limitada e *scale-to-zero* após inatividade).
> Para produção real, suba para um plano pago (PITR/backups estendidos) ou exporte backups
> regularmente por conta própria. (O setup original usava o PostgreSQL free do Render, que
> expirava após ~30 dias — por isso a migração para o Neon.)

**Backup lógico (pg_dump):**

```bash
# Use a External Connection String do banco no Render.
pg_dump --no-owner --no-privileges --format=custom \
  "postgresql://user:pass@host:5432/rede_solidaria_pet" \
  --file "backup-$(date +%Y%m%d-%H%M%S).dump"
```

**Restore (pg_restore) em um banco vazio:**

```bash
pg_restore --no-owner --no-privileges --clean --if-exists \
  --dbname "postgresql://user:pass@host:5432/rede_solidaria_pet" \
  backup-AAAAMMDD-HHMMSS.dump
```

Boas práticas:

- Agende `pg_dump` periódico (cron local, GitHub Action agendada ou similar) já que o
  free tier não cobre isso.
- Guarde os dumps fora do Render (object storage, repositório privado de backups).
- Teste o restore num banco descartável de tempos em tempos — backup não testado não é
  backup.
- Combine a versão do dump com a revisão Alembic correspondente para um restore coerente.

## Object storage para fotos em produção

O object storage **já está implementado** e em uso em produção. O backend grava as
imagens através da abstração `StorageBackend` (`backend/app/core/storage.py`), e
`get_storage(settings)` seleciona o backend por `STORAGE_BACKEND`:

- `local` (default): `LocalStorageBackend` grava em `UPLOAD_DIR` e serve sob
  `PUBLIC_UPLOAD_PATH` via `StaticFiles`. **Efêmero no Render free** — bom só para
  desenvolvimento.
- `s3`: `S3StorageBackend` grava em object storage S3-compatível (Cloudflare R2, AWS S3,
  Supabase Storage, MinIO), durável e compartilhado entre instâncias.

A produção usa **Cloudflare R2** (`STORAGE_BACKEND=s3`). O passo a passo completo de
configuração — criar bucket, habilitar acesso público, gerar o token S3 e definir as
variáveis `S3_*` — está na seção [**Armazenamento de fotos em produção**](#armazenamento-de-fotos-em-produção)
acima. Não é preciso escrever código: basta configurar as variáveis de ambiente.

> A única opção ainda **não** implementada é o Cloudinary (SaaS de mídia, não
> S3-compatível); exigiria uma subclasse `StorageBackend` própria. Para apenas armazenar
> de forma durável, o R2 já suportado é mais simples.

## Cold start do free tier

O Web Service free do Render **hiberna após ~15 minutos de inatividade**. A primeira
requisição depois disso sofre um **cold start de ~30–60 s** enquanto o container sobe e o
`/ready` passa.

Mitigações:

- Um ping periódico em `/health` (liveness, sem tocar o banco) mantém a instância
  acordada — mas isso na prática anula a economia do free tier; use só se aceitável.
- Comunique a latência inicial na UI (estado de carregamento já existe nas telas).
- Para eliminar o cold start, suba para um plano pago (sem hibernação).
- O frontend (Vercel) não hiberna; só o backend é afetado.

## Rotação de segredos

**`SECRET_KEY` (assinatura JWT):**

1. Gere uma nova chave forte (≥32 bytes), ex.: `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
2. Atualize a env `SECRET_KEY` no Render (ou regenere com `generateValue`) e redeploye.
3. **Efeito:** todos os access tokens existentes são invalidados — os usuários precisarão
   logar de novo. Faça em janela de baixo uso e comunique se necessário.

**Credenciais SMTP (`SMTP_PASSWORD` etc.):** rotacione no provedor de e-mail, atualize as
envs (`sync: false`) e redeploye. Não há sessão dependente delas.

**`DATABASE_URL`:** ao rotacionar a senha do banco, atualize a connection string e
redeploye; rode um `/ready` para confirmar a reconexão.

**Segredos de object storage:** rotacione as chaves no provedor, atualize as envs e
redeploye.

Boas práticas:

- Nunca versione segredos (o repositório tem `.gitleaks.toml` + workflow `secret-scan`
  para barrar vazamentos).
- Prefira `sync: false`/`generateValue: true` no `render.yaml` para que os valores nunca
  apareçam no git.
- Rotacione imediatamente qualquer segredo que tenha aparecido em log, PR ou histórico.
