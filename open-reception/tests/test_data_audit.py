import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from app.main import (
    AuditEvent,
    HumanPassport,
    HumanPassportStatusHistory,
    SessionLocal,
    User,
    app,
    verify_audit_chain,
)


def _login(client, email, password):
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_audit_hash_chain_verifies():
    with TestClient(app) as client:
        client.post("/auth/register", json={
            "email": "audit-chain@example.org", "password": "correct-horse-battery",
        })
    with SessionLocal() as db:
        events = db.scalars(select(AuditEvent).order_by(AuditEvent.sequence)).all()
        assert events
        assert all(event.event_hash and event.previous_hash for event in events)
        assert verify_audit_chain(db) is True


def test_human_passport_status_transition_and_history():
    with TestClient(app) as client:
        client.post("/auth/register", json={
            "email": "passport-owner@example.org", "password": "correct-horse-battery",
        })
        owner = _login(client, "passport-owner@example.org", "correct-horse-battery")
        issued = client.put("/passport/human", headers=owner, json={
            "display_name": "Passport Owner", "domains": ["food-desert"],
        })
        assert issued.status_code == 200

        client.post("/auth/register", json={
            "email": "v03-security-admin@example.org",
            "password": "administrator-pass",
        })
        with SessionLocal() as db:
            security_admin = db.scalar(select(User).where(
                User.email == "v03-security-admin@example.org"
            ))
            security_admin.role = "security_admin"
            db.commit()
        admin = _login(client, "v03-security-admin@example.org", "administrator-pass")
        changed = client.post(
            f"/admin/passports/human/{issued.json()['id']}/status",
            headers=admin,
            json={"status": "suspended", "reason": "identity review required"},
        )
        assert changed.status_code == 200
        assert changed.json()["status"] == "suspended"
        invalid = client.post(
            f"/admin/passports/human/{issued.json()['id']}/status",
            headers=admin,
            json={"status": "expired", "reason": "invalid direct transition check"},
        )
        assert invalid.status_code == 200

    with SessionLocal() as db:
        passport = db.get(HumanPassport, issued.json()["id"])
        history = db.scalars(select(HumanPassportStatusHistory).where(
            HumanPassportStatusHistory.passport_id == passport.id
        ).order_by(HumanPassportStatusHistory.changed_at)).all()
        assert [entry.to_status for entry in history] == ["active", "suspended", "expired"]


@pytest.mark.skipif(
    not os.environ["DATABASE_URL"].startswith("postgresql"),
    reason="requires PostgreSQL append-only enforcement",
)
def test_postgresql_audit_rows_reject_update_and_delete():
    with TestClient(app) as client:
        client.post("/auth/register", json={
            "email": "immutable-audit@example.org", "password": "correct-horse-battery",
        })
    with SessionLocal() as db:
        event_id = db.scalar(select(AuditEvent.id).where(
            AuditEvent.action == "user.registered",
            AuditEvent.target_type == "user",
        ).order_by(AuditEvent.sequence.desc()))
        with pytest.raises(DBAPIError, match="append-only"):
            db.execute(text(
                "UPDATE audit_events SET action = 'tampered' WHERE id = :event_id"
            ), {"event_id": event_id})
            db.commit()
        db.rollback()
        with pytest.raises(DBAPIError, match="append-only"):
            db.execute(text(
                "DELETE FROM audit_events WHERE id = :event_id"
            ), {"event_id": event_id})
            db.commit()
