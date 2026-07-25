from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from app.main import (
    AuditChainHead,
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


def test_audit_chain_rejects_chain_head_tampering():
    with TestClient(app) as client:
        client.post("/auth/register", json={
            "email": "audit-head@example.org", "password": "correct-horse-battery",
        })
    with SessionLocal() as db:
        head = db.get(AuditChainHead, "global")
        original_sequence = head.sequence
        head.sequence += 1
        db.flush()
        assert verify_audit_chain(db) is False
        head.sequence = original_sequence
        head.event_hash = "f" * 64
        db.flush()
        assert verify_audit_chain(db) is False
        db.rollback()


def test_empty_audit_chain_requires_zeroed_head():
    class EmptyAuditSession:
        def __init__(self, event_hash):
            self.head = SimpleNamespace(sequence=0, event_hash=event_hash)

        def scalars(self, _statement):
            return SimpleNamespace(all=lambda: [])

        def get(self, model, identifier):
            assert model is AuditChainHead
            assert identifier == "global"
            return self.head

    assert verify_audit_chain(EmptyAuditSession("0" * 64)) is True
    assert verify_audit_chain(EmptyAuditSession("f" * 64)) is False


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
    reason="requires the PostgreSQL integration test environment",
)
def test_postgresql_human_passport_status_transitions_are_serialized():
    run_id = uuid4().hex
    owner_email = f"passport-concurrency-owner-{run_id}@example.org"
    admin_email = f"passport-concurrency-admin-{run_id}@example.org"
    with TestClient(app) as client:
        client.post("/auth/register", json={
            "email": owner_email,
            "password": "correct-horse-battery",
        })
        owner = _login(
            client,
            owner_email,
            "correct-horse-battery",
        )
        issued = client.put("/passport/human", headers=owner, json={
            "display_name": "Concurrent Passport Owner",
            "domains": ["food-desert"],
        })
        assert issued.status_code == 200
        client.post("/auth/register", json={
            "email": admin_email,
            "password": "administrator-pass",
        })
        with SessionLocal() as db:
            security_admin = db.scalar(select(User).where(
                User.email == admin_email
            ))
            security_admin.role = "security_admin"
            db.commit()
        admin = _login(
            client,
            admin_email,
            "administrator-pass",
        )

    def suspend_passport(request_number):
        with TestClient(app) as client:
            return client.post(
                f"/admin/passports/human/{issued.json()['id']}/status",
                headers=admin,
                json={
                    "status": "suspended",
                    "reason": f"concurrent suspension request {request_number}",
                },
            ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(suspend_passport, range(2)))
    assert sorted(statuses) == [200, 409]

    with SessionLocal() as db:
        history = db.scalars(select(HumanPassportStatusHistory).where(
            HumanPassportStatusHistory.passport_id == issued.json()["id"]
        ).order_by(HumanPassportStatusHistory.changed_at)).all()
        assert len(history) == 2
        assert history[0].from_status is None
        assert history[1].from_status == history[0].to_status == "active"
        assert history[1].to_status == "suspended"
        passport = db.get(HumanPassport, issued.json()["id"])
        assert passport.status == history[-1].to_status


def test_append_only_rows_reject_update_and_delete():
    with TestClient(app) as client:
        client.post("/auth/register", json={
            "email": "immutable-audit@example.org", "password": "correct-horse-battery",
        })
        owner = _login(client, "immutable-audit@example.org", "correct-horse-battery")
        issued = client.put("/passport/human", headers=owner, json={
            "display_name": "Immutable History", "domains": ["food-desert"],
        })
        assert issued.status_code == 200
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
        history_id = db.scalar(select(HumanPassportStatusHistory.id).where(
            HumanPassportStatusHistory.passport_id == issued.json()["id"]
        ))
        assert history_id is not None
        with pytest.raises(DBAPIError, match="append-only"):
            db.execute(text("""
                UPDATE human_passport_status_history
                SET reason = 'tampered' WHERE id = :history_id
            """), {"history_id": history_id})
            db.commit()
        db.rollback()
        with pytest.raises(DBAPIError, match="append-only"):
            db.execute(text("""
                DELETE FROM human_passport_status_history WHERE id = :history_id
            """), {"history_id": history_id})
            db.commit()
        db.rollback()
        with pytest.raises(DBAPIError, match="append-only"):
            db.execute(text(
                "DELETE FROM audit_events WHERE id = :event_id"
            ), {"event_id": event_id})
            db.commit()
