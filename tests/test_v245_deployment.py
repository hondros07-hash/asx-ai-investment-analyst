"""Release boundary checks without external providers or production credentials."""
from fastapi.testclient import TestClient
from api.main import app

def test_liveness_is_local_and_explicit():
    response = TestClient(app).get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "axia-api"}

def test_readiness_is_local_and_explicit():
    response = TestClient(app).get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "service": "axia-api"}
