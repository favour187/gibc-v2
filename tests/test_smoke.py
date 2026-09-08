from app.core.testing import auth_headers, create_user


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert "ai" in body


def test_feature_router(client):
    data = create_user(client, email="smoke@example.com")
    res = client.get("/api/learning/overview", headers=auth_headers(data["token"]))
    assert res.status_code == 200
    assert res.json()["curriculum"]["total_skills"] > 0


def test_auth_flow(client):
    data = create_user(client, email="smoke@example.com")
    me = client.get("/api/auth/me", headers=auth_headers(data["token"]))
    assert me.status_code == 200
    assert me.json()["email"] == "smoke@example.com"


def test_ai_ping(client):
    res = client.post("/api/demo/ai-ping", json={"prompt": "hello"})
    assert res.status_code == 200
    body = res.json()
    assert body["text"]
    assert body["provider"] == "local-demo"


def test_database_url_normalisation():
    from app.core.db import database_backend, normalize_database_url

    assert (
        normalize_database_url("postgres://u:p@h/d?sslmode=require")
        == "postgresql+psycopg://u:p@h/d?sslmode=require"
    )
    assert (
        normalize_database_url("postgresql://u:p@h/d") == "postgresql+psycopg://u:p@h/d"
    )
    assert normalize_database_url("sqlite:///./x.db") == "sqlite:///./x.db"
    assert database_backend("postgres://u:p@h/d") == "postgresql"
    assert database_backend("sqlite:///./x.db") == "sqlite"


def test_demo_user_seeded_in_production_only_when_asked():
    from fastapi.testclient import TestClient
    from app.core.testing import make_settings
    from app.main import build_app

    login = {"email": "demo@example.com", "password": "demo-password-123"}
    with TestClient(build_app(make_settings(environment="production"))) as c:
        assert c.post("/api/auth/login", json=login).status_code in (400, 401, 404)
    with TestClient(
        build_app(make_settings(environment="production", seed_demo_user=True))
    ) as c:
        assert c.post("/api/auth/login", json=login).status_code == 200
