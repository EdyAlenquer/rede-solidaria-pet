FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Número de workers do Uvicorn. Default conservador (2) adequado ao free tier;
# em produção ajuste via env WEB_CONCURRENCY conforme as CPUs disponíveis.
ENV WEB_CONCURRENCY=2

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# Usuário não-root: o container serve apenas o servidor, sem privilégios extras.
RUN adduser --disabled-password --gecos "" --no-create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Readiness via /ready (SELECT 1): valida que o processo consegue atender
# requisições e que o banco responde. Usa o Python já instalado (sem curl).
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=4).status == 200 else 1)"]

# O container apenas serve o servidor; as migrações Alembic rodam no passo de
# deploy (preDeployCommand no Render / command no compose), nunca no boot.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WEB_CONCURRENCY:-2}"]
