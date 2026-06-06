# Deploy

## Alvo definido

| Camada | Plataforma sugerida | Motivo |
| ------ | ------------------- | ------ |
| Backend | Render Web Service | Suporte simples a Dockerfile, variáveis de ambiente e health-check HTTP. |
| Banco | Render PostgreSQL | PostgreSQL gerenciado no mesmo provedor do backend. |
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
| `UPLOAD_DIR` | Não (default `uploads`) | `uploads` | Diretório do `LocalStorageBackend`. **Efêmero no Render** (veja Object storage). |
| `PUBLIC_UPLOAD_PATH` | Não (default `/uploads`) | `/uploads` | Prefixo público sob o qual as imagens são servidas. |
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

- `render.yaml`: declara o Web Service Docker do backend e o PostgreSQL gerenciado.
- `frontend/vercel.json`: declara build Vite, diretório de saída e rewrite SPA do frontend.

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

> **Limitação do free tier do Render:** o PostgreSQL free **não tem backups automáticos**
> e é **removido após ~90 dias** se inativo. Para produção real, suba para um plano pago
> (que inclui PITR/backups diários) ou exporte backups regularmente por conta própria.

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

O upload de imagens usa hoje o `LocalStorageBackend` (`backend/app/core/storage.py`),
que grava em `UPLOAD_DIR` (`uploads/`) e serve sob `PUBLIC_UPLOAD_PATH` (`/uploads`) via
`StaticFiles`.

> **O disco do Render free é efêmero:** qualquer arquivo gravado em `/uploads` é **perdido
> a cada deploy e a cada cold start/restart**. Em produção, as fotos **precisam** ir para
> um object storage externo (Cloudinary, Cloudflare R2 ou S3).

A costura já está pronta: `get_storage(settings)` é o **ponto único de decisão** do
backend de storage, e rotas/serviços dependem apenas da interface `StorageBackend`
(`salvar(conteudo, nome_arquivo) -> url` e `remover(url)`). Para plugar um backend de
nuvem:

1. Implemente uma subclasse de `StorageBackend` (ex.: `CloudinaryStorageBackend` ou
   `R2StorageBackend`) em `backend/app/core/storage.py`:
   - `salvar`: faz upload do conteúdo binário e devolve a **URL pública absoluta** do
     objeto.
   - `remover`: apaga o objeto pela URL, de forma idempotente.
2. Troque o corpo de `get_storage` para selecionar o backend conforme as `Settings`
   (ex.: novo campo `storage_backend: "local" | "cloudinary" | "r2"` + credenciais como
   `CLOUDINARY_URL` ou `R2_*`/`S3_*`). Adicione as credenciais como variáveis de ambiente
   (e ao `render.yaml` com `sync: false`).
3. Quando o storage devolver URLs absolutas, o `StaticFiles` local e o
   `PUBLIC_UPLOAD_PATH` deixam de ser necessários em produção; podem ser mantidos só para
   desenvolvimento.
4. Nenhuma mudança em rotas, serviços ou no schema `ImagemRead` é necessária — a URL
   continua sendo o identificador estável da imagem.

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
