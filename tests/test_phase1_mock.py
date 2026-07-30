"""Phase 1 Mock Testing - Matching v0.4 Integration Tests"""

import unittest
import json
import uuid
from datetime import datetime


class MockMatchingClient:
      """Mock Matching v0.4 API Client for Phase 1 Testing"""

    def __init__(self, dry_run=True):
              self.dry_run = dry_run
              self.request_cache = {}
              self.audit_log = []

    def call_matching_api(self, request_id, correlation_id, user_profile, policy_version):
              """Call Matching API with correlation_id propagation"""
              if correlation_id in self.request_cache:
                            return self.request_cache[correlation_id]

              request = {
                  "request_id": request_id,
                  "correlation_id": correlation_id,
                  "idempotency_key": correlation_id,
                  "user_profile": user_profile,
                  "policy_version": policy_version
              }

        response = self._process_matching_request(request)
        self.request_cache[correlation_id] = response
        self.audit_log.append({
                      "timestamp": datetime.now().isoformat(),
                      "event": "api_call",
                      "correlation_id": correlation_id,
                      "user_id": user_profile.get("user_id")
        })
        return response

    def _process_matching_request(self, request):
              """Mock Matching API processing logic"""
              user_profile = request["user_profile"]
              user_id = user_profile.get("user_id")

        if user_id and user_id.startswith("excluded-"):
                      return {
                                        "error_code": 403,
                                        "error_type": "MANDATE",
                                        "message": "User excluded",
                                        "correlation_id": request["correlation_id"]
                      }

        if not user_profile.get("purchase_amount") or user_profile.get("purchase_amount") < 30000:
                      return {
                                        "decision_id": f"dec-{uuid.uuid4()}",
                                        "correlation_id": request["correlation_id"],
                                        "state": "RECOMMENDATION",
                                        "recommendation": {
                                                              "policy_id": "policy-standard-v0.4",
                                                              "requires_approval": False
                                        },
                                        "timestamp": datetime.now().isoformat()
                      }

        return {
                      "decision_id": f"dec-{uuid.uuid4()}",
                      "correlation_id": request["correlation_id"],
                      "state": "APPROVAL_PENDING",
                      "recommendation": {
                                        "policy_id": "policy-high-value-v0.4",
                                        "requires_approval": True
                      },
                      "timestamp": datetime.now().isoformat()
        }


class Phase1MockTests(unittest.TestCase):
      """Phase 1 Mock Testing Suite"""

    def setUp(self):
              self.client = MockMatchingClient(dry_run=True)

    def test_scenario_1_normal_recommendation(self):
              """정상 추천 -> RECOMMENDATION"""
              response = self.client.call_matching_api(
                  request_id=f"req-{uuid.uuid4()}",
                  correlation_id=str(uuid.uuid4()),
                  user_profile={"user_id": "user-123", "steward_id": "steward-456"},
                  policy_version="v0.4"
              )
              self.assertEqual(response["state"], "RECOMMENDATION")
              self.assertFalse(response["recommendation"]["requires_approval"])

    def test_scenario_2_policy_exclusion(self):
              """정책 제외 -> 403 MANDATE"""
              response = self.client.call_matching_api(
                  request_id=f"req-{uuid.uuid4()}",
                  correlation_id=str(uuid.uuid4()),
                  user_profile={"user_id": "excluded-user-789", "steward_id": "steward-456"},
                  policy_version="v0.4"
              )
              self.assertEqual(response["error_code"], 403)

    def test_scenario_3_idempotency(self):
              """중복 요청 -> Idempotent"""
              correlation_id = str(uuid.uuid4())
              response_1 = self.client.call_matching_api(
                  request_id=f"req-{uuid.uuid4()}",
                  correlation_id=correlation_id,
                  user_profile={"user_id": "user-123"},
                  policy_version="v0.4"
              )
              response_2 = self.client.call_matching_api(
                  request_id=f"req-{uuid.uuid4()}",
                  correlation_id=correlation_id,
                  user_profile={"user_id": "user-123"},
                  policy_version="v0.4"
              )
              self.assertEqual(response_1["decision_id"], response_2["decision_id"])


if __name__ == "__main__":
      unittest.main(verbosity=2)
