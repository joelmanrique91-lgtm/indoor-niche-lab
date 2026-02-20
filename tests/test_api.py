from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_api_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_api_stages_returns_list():
    resp = client.get("/api/stages")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
