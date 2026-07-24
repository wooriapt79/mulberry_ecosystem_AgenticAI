from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import AuditEvent, SessionLocal, User, app


def login(client, email, password):
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_bootstrap_is_single_use():
    with TestClient(app) as client:
        response = client.post("/auth/bootstrap", json={
            "email": "another-admin@example.org",
            "password": "another-administrator-pass",
            "bootstrap_token": "bootstrap-token-for-tests-only-000000",
        })
        assert response.status_code == 409


def test_logout_and_logout_all_revoke_tokens():
    with TestClient(app) as client:
        client.post("/auth/register", json={
            "email": "sessions@example.org", "password": "correct-horse-battery",
        })
        first = login(client, "sessions@example.org", "correct-horse-battery")
        second = login(client, "sessions@example.org", "correct-horse-battery")
        assert client.post("/auth/logout", headers=first).status_code == 204
        assert client.post("/matching/recommendations", headers=first,
                           json={"domain": "food-desert"}).status_code == 401
        assert client.post("/auth/logout-all", headers=second).status_code == 200
        assert client.post("/matching/recommendations", headers=second,
                           json={"domain": "food-desert"}).status_code == 401


def test_login_lockout_is_audited():
    with TestClient(app) as client:
        client.post("/auth/register", json={
            "email": "locked@example.org", "password": "correct-horse-battery",
        })
        for _ in range(3):
            response = client.post("/auth/login", json={
                "email": "locked@example.org", "password": "wrong-password",
            })
            assert response.status_code == 401
        assert client.post("/auth/login", json={
            "email": "locked@example.org", "password": "correct-horse-battery",
        }).status_code == 423
        with SessionLocal() as db:
            assert db.scalar(select(AuditEvent).where(AuditEvent.action == "account.locked"))


def test_rbac_and_emergency_revoke():
    with TestClient(app) as client:
        client.post("/auth/register", json={
            "email": "victim@example.org", "password": "correct-horse-battery",
        })
        victim_headers = login(client, "victim@example.org", "correct-horse-battery")
        with SessionLocal() as db:
            victim = db.scalar(select(User).where(User.email == "victim@example.org"))
            victim_id = victim.id
        assert client.post(f"/admin/users/{victim_id}/revoke", headers=victim_headers,
                           json={"reason": "unauthorized attempt"}).status_code == 403
        admin_headers = login(client, "admin@example.org", "administrator-pass")
        response = client.post(f"/admin/users/{victim_id}/revoke", headers=admin_headers,
                               json={"reason": "security incident", "disable_account": True})
        assert response.status_code == 200
        assert response.json()["disabled"] is True
        assert client.post("/matching/recommendations", headers=victim_headers,
                           json={"domain": "food-desert"}).status_code in (401, 403)
