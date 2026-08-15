import os

os.environ["SESSION_SIGNING_SECRET"] = "test-secret-at-least-32-characters"

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_and_catalog():
    assert client.get("/health").json() == {"status": "ok", "mode": "phase-a-rule-based"}
    catalog = client.get("/api/catalog")
    assert catalog.status_code == 200
    assert len(catalog.json()["personas"]) == 5


def test_start_and_chat():
    started = client.post("/api/session", json={"card": "judgement", "persona": "reflection"})
    assert started.status_code == 200
    token = started.json()["session"]
    response = client.post("/api/chat", json={"session": token, "message": "다른 관점이 궁금해요"})
    assert response.status_code == 200
    assert response.json()["turn"] == 2


def test_extra_fields_and_bad_card_are_rejected():
    assert client.post("/api/session", json={"card": "the-sun", "name": "user"}).status_code == 422
    assert client.post("/api/session", json={"card": "../../secret"}).status_code == 400
