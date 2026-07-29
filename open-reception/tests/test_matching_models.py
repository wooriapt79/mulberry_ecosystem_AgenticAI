from sqlalchemy import inspect, select

from app.main import (
    AiPassport,
    MatchRequest,
    MatchingCandidate,
    MatchingDecision,
    MatchingRecommendation,
    SessionLocal,
    User,
)
from app.matching_policy import DOMAIN_PACK_VERSION, MATCHING_POLICY_VERSION


def test_matching_schema_records_policy_evidence_and_human_decision():
    with SessionLocal() as db:
        user = User(
            email="matching-models@example.com",
            password_hash="test-only",
            role="member",
        )
        agent = AiPassport(
            id="matching-model-agent",
            name="Matching Model Agent",
            level="steward",
            domains=["food-desert"],
            permissions=["research"],
            spirit_score=0.8,
            status="active",
        )
        db.add_all([user, agent])
        db.flush()
        request = MatchRequest(
            requester_id=user.id,
            domain="food-desert",
            risk="low",
            required_permissions=["research"],
        )
        db.add(request)
        db.flush()
        recommendation = MatchingRecommendation(
            request_id=request.id,
            domain_pack_version=DOMAIN_PACK_VERSION,
            policy_version=MATCHING_POLICY_VERSION,
            rationale={"request_type": "food_access_research"},
        )
        db.add(recommendation)
        db.flush()
        candidate = MatchingCandidate(
            recommendation_id=recommendation.id,
            agent_passport_id=agent.id,
            agent_kind="steward_ai",
            rank=1,
            score=0.91,
            eligible=True,
            evidence={"competencies": ["food-desert", "research"]},
            exclusion_reasons=[],
        )
        decision = MatchingDecision(
            recommendation_id=recommendation.id,
            action="approve",
            from_status="recommended",
            to_status="approved",
            decided_by=user.id,
            reason="test approval",
        )
        db.add_all([candidate, decision])
        db.commit()

        stored = db.scalar(
            select(MatchingRecommendation).where(
                MatchingRecommendation.request_id == request.id
            )
        )
        stored_candidate = db.scalar(
            select(MatchingCandidate).where(
                MatchingCandidate.recommendation_id == stored.id
            )
        )
        stored_decision = db.scalar(
            select(MatchingDecision).where(
                MatchingDecision.recommendation_id == stored.id
            )
        )

        assert stored.domain_pack_version == "food-desert-v1"
        assert stored.policy_version == "luna-matching-v0.4"
        assert stored_candidate.evidence["competencies"] == [
            "food-desert",
            "research",
        ]
        assert stored_candidate.eligible is True
        assert stored_decision.action == "approve"
        assert stored_decision.to_status == "approved"
        assert stored_decision.created_at is not None


def test_matching_v04_tables_and_foreign_keys_are_migrated():
    with SessionLocal() as db:
        inspector = inspect(db.bind)

        assert {
            "matching_recommendations",
            "matching_candidates",
            "matching_decisions",
        } <= set(inspector.get_table_names())
        assert {
            fk["referred_table"]
            for fk in inspector.get_foreign_keys("matching_candidates")
        } == {"matching_recommendations", "ai_passports"}
        assert {
            fk["referred_table"]
            for fk in inspector.get_foreign_keys("matching_decisions")
        } == {"matching_recommendations", "users"}
