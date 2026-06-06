"""Testes dos manifests versionáveis de deploy."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]


def test_render_yaml_define_backend_e_postgres() -> None:
    """`render.yaml` declara backend Docker e PostgreSQL gerenciado."""
    manifest = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))

    service = manifest["services"][0]
    database = manifest["databases"][0]

    assert service["type"] == "web"
    assert service["plan"] == "free"
    assert service["runtime"] == "docker"
    assert service["dockerfilePath"] == "./backend/Dockerfile"
    assert "dockerCommand" not in service
    assert service["healthCheckPath"] == "/ready"
    assert database["plan"] == "free"
    assert database["databaseName"] == "rede_solidaria_pet"
    assert any(env["key"] == "DATABASE_URL" for env in service["envVars"])
    assert {
        "key": "CORS_ORIGINS",
        "value": "https://rede-solidaria-pet.vercel.app",
    } in service["envVars"]


def test_render_yaml_aplica_migracoes_em_predeploy() -> None:
    """As migrações rodam no `preDeployCommand`, fora do boot do container."""
    manifest = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))
    service = manifest["services"][0]

    assert "alembic upgrade head" in service["preDeployCommand"]


def test_render_yaml_gera_secret_key() -> None:
    """`render.yaml` gera uma SECRET_KEY própria no Render (sem hardcode)."""
    manifest = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))
    service = manifest["services"][0]

    secret = next(env for env in service["envVars"] if env["key"] == "SECRET_KEY")
    assert secret.get("generateValue") is True
    assert "value" not in secret


def test_backend_dockerfile_migra_no_start_e_serve() -> None:
    """Dockerfile aplica migrações no start e serve o Uvicorn como usuário não-root.

    O `preDeployCommand` do Render só roda em planos pagos; no free tier as
    migrações precisam rodar no start do container (uma vez, antes do Uvicorn
    forkar os workers — sem corrida em instância única). É idempotente: em
    planos pagos o preDeploy já as aplicou e este passo vira no-op.
    """
    dockerfile = (ROOT / "backend/Dockerfile").read_text(encoding="utf-8")

    assert "uvicorn app.main:app" in dockerfile
    # Migração roda no start (necessária no free tier, que ignora preDeployCommand).
    assert "alembic upgrade head" in dockerfile
    # Workers parametrizados por WEB_CONCURRENCY.
    assert "WEB_CONCURRENCY" in dockerfile
    # Hardening: usuário não-root e healthcheck de readiness.
    assert "USER appuser" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "/ready" in dockerfile


def test_compose_backend_tem_healthcheck_de_readiness() -> None:
    """O serviço backend do compose declara healthcheck batendo em /ready."""
    manifest = yaml.safe_load((ROOT / "compose.yml").read_text(encoding="utf-8"))
    backend = manifest["services"]["backend"]

    assert "healthcheck" in backend
    assert "/ready" in " ".join(backend["healthcheck"]["test"])
    # A migração continua sendo um passo explícito no compose (ok em local).
    assert "alembic upgrade head" in backend["command"]


def test_vercel_json_define_build_vite_e_rewrites_spa() -> None:
    """`frontend/vercel.json` configura build Vite e fallback SPA."""
    manifest_path = ROOT / "frontend/vercel.json"

    assert manifest_path.exists()
    assert not (ROOT / "vercel.json").exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["buildCommand"] == "npm run build"
    assert manifest["outputDirectory"] == "dist"
    assert manifest["installCommand"] == "npm ci"
    assert manifest["framework"] == "vite"
    assert manifest["rewrites"] == [{"source": "/(.*)", "destination": "/index.html"}]


def test_production_smoke_workflow_define_urls_publicas() -> None:
    """Workflow manual exige URLs públicas HTTPS para validar produção."""
    manifest = yaml.safe_load(
        (ROOT / ".github/workflows/production-smoke.yml").read_text(encoding="utf-8")
    )

    trigger = manifest.get("on", manifest.get(True))
    inputs = trigger["workflow_dispatch"]["inputs"]
    steps = manifest["jobs"]["smoke"]["steps"]

    assert inputs["frontend_url"]["required"] is True
    assert inputs["backend_url"]["required"] is True
    assert any("node scripts/smoke-production.mjs" in step.get("run", "") for step in steps)
