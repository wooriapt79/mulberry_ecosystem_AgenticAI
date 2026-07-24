import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

db_file = Path(__file__).parent / "security.sqlite3"
if db_file.exists():
    db_file.unlink()
os.environ.setdefault("DATABASE_URL", f"sqlite:///{db_file}")
os.environ.setdefault("ADMIN_BOOTSTRAP_TOKEN", "bootstrap-token-for-tests-only-000000")
os.environ.setdefault("LOGIN_MAX_FAILURES", "3")

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

import app.main as main_module
from app.main import (
    ADMIN_PERMISSIONS,
    AuditEvent,
    BootstrapConsumption,
    LoginSession,
    SessionLocal,
    User,
    app,
)


def login(client, email, password):
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def ensure_admin(client):
    response = client.post("/auth/bootstrap", json={
        "email": "admin@example.org",
        "password": "administrator-pass",
        "bootstrap_token": os.environ["ADMIN_BOOTSTRAP_TOKEN"],
    })
    assert response.status_code in (201, 409)


def reset_bootstrap_state():
    """Give the PostgreSQL concurrency test an independent bootstrap state."""
    with SessionLocal() as db:
        admin_ids = db.scalars(
            select(User.id).where(
                (User.role == "admin") | (User.email.like("concurrent-admin-%@example.org"))
            )
        ).all()
        if admin_ids:
            db.execute(delete(LoginSession).where(LoginSession.user_id.in_(admin_ids)))
            db.execute(delete(User).where(User.id.in_(admin_ids)))
        db.execute(delete(BootstrapConsumption).where(BootstrapConsumption.id == "admin"))
        db.commit()


def test_bootstrap_is_single_use():
    with TestClient(app) as client:
        ensure_admin(client)
        response = client.post("/auth/bootstrap", json={
            "email": "another-admin@example.org",
            "password": "another-administrator-pass",
            "bootstrap_token": os.environ["ADMIN_BOOTSTRAP_TOKEN"],
        })
        assert response.status_code == 409


def test_bootstrap_consumption_survives_admin_role_change():
    with TestClient(app) as client:
        ensure_admin(client)
        with SessionLocal() as db:
            admin = db.scalar(select(User).where(User.email == "admin@example.org"))
            admin.role = "member"
            db.commit()
            assert db.get(BootstrapConsumption, "admin")
        response = client.post("/auth/bootstrap", json={
            "email": "replacement-admin@example.org",
            "password": "replacement-administrator-pass",
            "bootstrap_token": os.environ["ADMIN_BOOTSTRAP_TOKEN"],
        })
        assert response.status_code == 409
        with SessionLocal() as db:
            admin = db.scalar(select(User).where(User.email == "admin@example.org"))
            admin.role = "admin"
            db.commit()


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
        }).status_code == 401
        with SessionLocal() as db:
            assert db.scalar(select(AuditEvent).where(AuditEvent.action == "account.locked"))


def test_rbac_and_emergency_revoke():
    with TestClient(app) as client:
        ensure_admin(client)
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


def test_unknown_account_uses_password_verification(monkeypatch):
    calls = []
    original = main_module.password_valid

    def tracking_password_valid(password, encoded):
        calls.append(encoded)
        return original(password, encoded)

    monkeypatch.setattr(main_module, "password_valid", tracking_password_valid)
    with TestClient(app) as client:
        response = client.post("/auth/login", json={
            "email": "unknown-account@example.org", "password": "wrong-password",
        })
    assert response.status_code == 401
    assert calls == [main_module.DUMMY_PASSWORD_HASH]


def test_locked_and_unknown_accounts_have_same_external_response():
    with TestClient(app) as client:
        client.post("/auth/register", json={
            "email": "oracle-target@example.org", "password": "correct-horse-battery",
        })
        for _ in range(3):
            client.post("/auth/login", json={
                "email": "oracle-target@example.org", "password": "wrong-password",
            })
        locked = client.post("/auth/login", json={
            "email": "oracle-target@example.org", "password": "wrong-password",
        })
        unknown = client.post("/auth/login", json={
            "email": "not-registered@example.org", "password": "wrong-password",
        })
    assert (locked.status_code, locked.json()) == (unknown.status_code, unknown.json())
    assert locked.status_code == 401


@pytest.mark.skipif(
    not os.environ["DATABASE_URL"].startswith("postgresql"),
    reason="requires the PostgreSQL integration test environment",
)
def test_postgresql_failed_login_increment_is_atomic():
    email = "concurrent-failures@example.org"
    with TestClient(app) as client:
        client.post("/auth/register", json={
            "email": email, "password": "correct-horse-battery",
        })

    def invalid_login(_):
        with TestClient(app) as client:
            return client.post("/auth/login", json={
                "email": email, "password": "wrong-password",
            }).status_code

    with ThreadPoolExecutor(max_workers=3) as pool:
        statuses = list(pool.map(invalid_login, range(3)))
    assert statuses == [401, 401, 401]
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        assert user.failed_login_count == 3
        assert user.locked_until is not None


@pytest.mark.skipif(
    not os.environ["DATABASE_URL"].startswith("postgresql"),
    reason="requires the PostgreSQL integration test environment",
)
def test_postgresql_bootstrap_claim_is_atomic(monkeypatch):
    monkeypatch.setenv("ADMIN_BOOTSTRAP_TOKEN", "concurrent-bootstrap-token-000000000")
    reset_bootstrap_state()

    def bootstrap(index):
        with TestClient(app) as client:
            return client.post("/auth/bootstrap", json={
                "email": f"concurrent-admin-{index}@example.org",
                "password": "concurrent-administrator-pass",
                "bootstrap_token": os.environ["ADMIN_BOOTSTRAP_TOKEN"],
            }).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(bootstrap, range(2)))
    assert sorted(statuses) == [201, 409]
    with SessionLocal() as db:
        assert db.get(BootstrapConsumption, "admin")
        assert len(db.scalars(select(User).where(User.role == "admin")).all()) == 1
    # Restore the standard administrator fixture expected by later RBAC tests.
    reset_bootstrap_state()
    with TestClient(app) as client:
        response = client.post("/auth/bootstrap", json={
            "email": "admin@example.org",
            "password": "administrator-pass",
            "bootstrap_token": os.environ["ADMIN_BOOTSTRAP_TOKEN"],
        })
        assert response.status_code == 201


def test_session_ttl_is_clamped_to_safe_positive_value(monkeypatch):
    monkeypatch.setenv("SESSION_TTL_MINUTES", "0")
    with TestClient(app) as client:
        client.post("/auth/register", json={
            "email": "ttl@example.org", "password": "correct-horse-battery",
        })
        response = client.post("/auth/login", json={
            "email": "ttl@example.org", "password": "correct-horse-battery",
        })
    assert response.status_code == 200
    assert response.json()["expires_in"] == 60


def test_account_disable_requires_explicit_permission(monkeypatch):
    with TestClient(app) as client:
        ensure_admin(client)
        client.post("/auth/register", json={
            "email": "permission-target@example.org", "password": "correct-horse-battery",
        })
        target_headers = login(client, "permission-target@example.org", "correct-horse-battery")
        admin_headers = login(client, "admin@example.org", "administrator-pass")
        with SessionLocal() as db:
            target = db.scalar(select(User).where(User.email == "permission-target@example.org"))
            target_id = target.id

        monkeypatch.setitem(
            ADMIN_PERMISSIONS,
            "admin",
            ADMIN_PERMISSIONS["admin"] - {"account:disable"},
        )
        denied = client.post(
            f"/admin/users/{target_id}/revoke",
            headers=admin_headers,
            json={"reason": "permission boundary test", "disable_account": True},
        )
        assert denied.status_code == 403
        assert client.post(
            "/matching/recommendations",
            headers=target_headers,
            json={"domain": "food-desert"},
        ).status_code == 200
