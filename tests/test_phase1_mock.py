"""Phase 1 tests: Luna consumes policy output and enforces Human control."""

import unittest

from luna.src.matching_client import MatchingClient
from luna.src.state_manager import MatchingState, StateManager


def matching_fixture(payload: dict) -> dict:
    """Approved fixture representing output owned by the Matching service."""
    return {
        "decision_id": "dec-fixture-001",
        "correlation_id": payload["correlation_id"],
        "state": "APPROVAL_PENDING",
        "recommendation": {
            "policy_id": "matching-fixture-v0.4",
            "reason": "Fixture supplied by Matching boundary",
            "requires_approval": True,
            "approval_gate": "HUMAN_REVIEW",
        },
        "timestamp": "2026-07-31T00:00:00+00:00",
    }


class Phase1MockTests(unittest.TestCase):
    def setUp(self):
        self.client = MatchingClient(dry_run=True, mock_provider=matching_fixture)

    def test_luna_consumes_matching_fixture(self):
        response = self.client.recommend(
            user_id="user-123",
            steward_id="steward-456",
            mandate_status="ACTIVE",
            correlation_id="corr-001",
            idempotency_key="idem-001",
        )
        self.assertEqual(response["state"], "APPROVAL_PENDING")
        self.assertTrue(response["recommendation"]["requires_approval"])
        self.assertNotIn("spirit_score", response["recommendation"])

    def test_correlation_and_idempotency_are_independent(self):
        self.client.recommend(
            "user-123", "steward-456", "ACTIVE", "corr-002", "idem-002"
        )
        event = self.client.audit_log[-1]
        self.assertEqual(event["correlation_id"], "corr-002")
        self.assertEqual(event["idempotency_key"], "idem-002")

    def test_idempotency_uses_idempotency_key(self):
        first = self.client.recommend(
            "user-123", "steward-456", "ACTIVE", "corr-003", "idem-shared"
        )
        second = self.client.recommend(
            "user-123", "steward-456", "ACTIVE", "corr-004", "idem-shared"
        )
        self.assertEqual(first["decision_id"], second["decision_id"])

    def test_dry_run_rejects_luna_owned_policy_logic(self):
        with self.assertRaises(RuntimeError):
            MatchingClient(dry_run=True).recommend(
                "user-123", "steward-456", "ACTIVE"
            )

    def test_human_approval_is_mandatory(self):
        manager = StateManager("corr-state")
        manager.transition(MatchingState.RECOMMENDED)
        manager.transition(MatchingState.APPROVAL_PENDING)
        with self.assertRaises(PermissionError):
            manager.transition(MatchingState.HUMAN_APPROVED, actor="luna")
        manager.transition(MatchingState.HUMAN_APPROVED, actor="human:re.eul")
        manager.transition(MatchingState.DRY_RUN_COMPLETED)
        self.assertTrue(manager.is_terminal())

    def test_no_executed_state_exists(self):
        self.assertNotIn("EXECUTED", MatchingState.__members__)


if __name__ == "__main__":
    unittest.main(verbosity=2)
