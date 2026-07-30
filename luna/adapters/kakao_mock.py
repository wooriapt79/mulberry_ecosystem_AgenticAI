"""
Luna Kakao Adapter Mock
Simulates Kakao Channel webhook events for Phase 1 testing.
"""
import uuid
from datetime import datetime, timezone

class KakaoMockAdapter:
    def make_recommendation_request(self, user_id="test-user-001", steward_id="steward-A",
                                     mandate_status="ACTIVE", purchase_amount=0) -> dict:
        return {
            "event": "user_message",
            "correlation_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user": {"user_id": user_id, "channel": "kakao"},
            "payload": {
                "intent": "matching_recommend",
                "steward_id": steward_id,
                "mandate_status": mandate_status,
                "context": {"purchase_amount": purchase_amount},
            },
        }

    def make_approval_response(self, decision_id: str, approved: bool, actor: str = "human") -> dict:
        return {
            "event": "approval_response",
            "decision_id": decision_id,
            "approved": approved,
            "actor": actor,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
