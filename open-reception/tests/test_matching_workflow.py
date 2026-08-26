from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import (
    AiPassport,
    AuditEvent,
    MatchingCandidate,
    MatchingDecision,
    MatchingRecommendation,
    SessionLocal,
    User,
    app,
    password_hash,
)


def _register_and_login(client, email, password):
    client.post("/auth/register", json={"email": email, "password": password})
    response = client.post("/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_recommendation_is_deterministic_and_persists_evidence():
    with TestClient(app) as client:
        headers = _register_and_login(
            client, "matching-flow@example.org", "matching-flow-password"
        )
        payload = {
            "domain": "food-desert",
            "request_type": "food_access_research",
            "risk": "low",
            "required_permissions": ["research"],
        }
        first = client.post("/matching/recommendations", headers=headers, json=payload)
        second = client.post("/matching/recommendations", headers=headers, json=payload)

        assert first.status_code == second.status_code == 200
        assert [item["agent_id"] for item in first.json()["candidates"]] == [
            item["agent_id"] for item in second.json()["candidates"]
        ]
        assert first.json()["candidates"][0]["agent_id"] == "luna"
        assert first.json()["policy_version"] == "luna-matching-v0.4"

        with SessionLocal() as db:
            recommendation = db.get(
                MatchingRecommendation, first.json()["recommendation_id"]
            )
            candidates = db.scalars(
                select(MatchingCandidate).where(
                    MatchingCandidate.recommendation_id == recommendation.id
                )
            ).all()
            assert recommendation.domain_pack_version == "food-desert-v1"
            assert any(candidate.evidence["permissions"] == ["research"] for candidate in candidates)
            assert all(candidate.exclusion_reasons is not None for candidate in candidates)


def test_spirit_permission_and_supervisor_gates_record_exclusions():
    with SessionLocal() as db:
        db.add_all(
            [
                AiPassport(
                    id="low-spirit",
                    name="Low Spirit",
                    level="professional",
                    domains=["food-desert", "research"],
                    permissions=["research"],
                    spirit_score=0.39,
                    status="active",
                ),
                AiPassport(
                    id="orphan-junior",
                    name="Orphan Junior",
                    level="junior",
                    domains=["food-desert", "research"],
                    permissions=["research"],
                    spirit_score=0.8,
                    mentor_agent="missing-supervisor",
                    status="active",
                ),
            ]
        )
        db.commit()

    with TestClient(app) as client:
        headers = _register_and_login(
            client, "matching-gates@example.org", "matching-gates-password"
        )
        response = client.post(
            "/matching/recommendations",
            headers=headers,
            json={
                "domain": "food-desert",
                "request_type": "food_access_research",
                "required_permissions": ["research"],
            },
        )
        recommendation_id = response.json()["recommendation_id"]

    with SessionLocal() as db:
        candidates = {
            item.agent_passport_id: item
            for item in db.scalars(
                select(MatchingCandidate).where(
                    MatchingCandidate.recommendation_id == recommendation_id
                )
            ).all()
        }
        assert "spirit_score_below_threshold" in candidates["low-spirit"].exclusion_reasons
        assert "active_supervisor_required" in candidates["orphan-junior"].exclusion_reasons


def test_human_decision_is_append_only_and_cannot_be_repeated():
    with TestClient(app) as client:
        member_headers = _register_and_login(
            client, "decision-member@example.org", "decision-member-password"
        )
        recommendation = client.post(
            "/matching/recommendations",
            headers=member_headers,
            json={
                "domain": "food-desert",
                "request_type": "food_access_research",
                "required_permissions": ["research"],
            },
        ).json()

        admin_email = "matching-admin@example.org"
        admin_password = "matching-admin-password"
        with SessionLocal() as db:
            db.add(
                User(
                    email=admin_email,
                    password_hash=password_hash(admin_password),
                    role="admin",
                )
            )
            db.commit()
        admin_login = client.post(
            "/auth/login", json={"email": admin_email, "password": admin_password}
        )
        admin_headers = {
            "Authorization": f"Bearer {admin_login.json()['access_token']}"
        }
        payload = {
            "action": "approve",
            "reason": "verified policy evidence",
            "candidate_id": recommendation["candidates"][0]["candidate_id"],
        }
        approved = client.post(
            f"/admin/matching/recommendations/{recommendation['recommendation_id']}/decision",
            headers=admin_headers,
            json=payload,
        )
        repeated = client.post(
            f"/admin/matching/recommendations/{recommendation['recommendation_id']}/decision",
            headers=admin_headers,
            json=payload,
        )
        assert approved.status_code == 200
        assert approved.json()["status"] == "approved"
        assert repeated.status_code == 409

    with SessionLocal() as db:
        decisions = db.scalars(
            select(MatchingDecision).where(
                MatchingDecision.recommendation_id
                == recommendation["recommendation_id"]
            )
        ).all()
        audit_events = db.scalars(
            select(AuditEvent).where(
                AuditEvent.target_id == recommendation["recommendation_id"],
                AuditEvent.action == "matching.approve",
            )
        ).all()
        assert len(decisions) == 1
        assert len(audit_events) == 1
