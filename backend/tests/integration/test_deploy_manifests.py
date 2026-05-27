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
    assert service["dockerCommand"].startswith("sh -c")
    assert "alembic upgrade head" in service["dockerCommand"]
    assert "uvicorn app.main:app" in service["dockerCommand"]
    assert service["healthCheckPath"] == "/health"
    assert database["plan"] == "free"
    assert database["databaseName"] == "rede_solidaria_pet"
    assert any(env["key"] == "DATABASE_URL" for env in service["envVars"])
    assert any(env["key"] == "CORS_ORIGINS" for env in service["envVars"])


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
