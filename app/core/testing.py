from __future__ import annotations
import tempfile
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from .config import Settings
from .http import create_app

def make_settings(**overrides) -> Settings:
    tmpdir = Path(tempfile.mkdtemp(prefix="hackathon-test-"))
    base = dict(
        app_name="Test App",
        app_version="0.0.0-test",
        environment="development",
        database_url=f"sqlite:///{tmpdir }/test.db",
        secret_key="test-secret",
        ai_mode="local",
        ai_cache_ttl_seconds=0,
        rate_limit_per_minute=10_000,
        data_dir=str(tmpdir),
    )
    base.update(overrides)
    return Settings(**base)

def build_test_app(**overrides) -> FastAPI:
    return create_app(make_settings(**overrides))

def make_test_client(**overrides) -> TestClient:
    return TestClient(build_test_app(**overrides))

def create_user(
    client: TestClient,
    email: str = "tester@example.com",
    password: str = "password123",
    display_name: str = "Tester",
):
    payload = {"email": email, "password": password, "display_name": display_name}
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return response.json()

def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token }"}
