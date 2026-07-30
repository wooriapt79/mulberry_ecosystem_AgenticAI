"""
Luna Matching Client v0.4
HTTP client for Matching v0.4 API — dry_run mode by default.

Safety: No real state mutations until Human approval.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("luna.matching_client")


class MatchingClient:
    """
    HTTP client for Mulberry Matching v0.4 API.

    Responsibilities:
    - POST /api/v0.4/matching/recommend
    - correlation_id propagation (header + body)
    - idempotency_key handling
    - Retry (max 3, exponential backoff 1s->2s->4s)
    - Error classification: VALIDATION | MANDATE | POLICY | SYSTEM
    - Audit logging (every request/response)

    NOT responsible for:
    - Spirit Score calculation (KeBin domain)
    - Passport/Mandate validation (external)
    - Payment/order/inventory mutations
    """

    BASE_URL = "http://matching-service.internal"
    ENDPOINT = "/api/v0.4/matching/recommend"
    TIMEOUT_SECONDS = 10
    MAX_RETRIES = 3
    POLICY_VERSION = "v0.4"

    def __init__(self, dry_run: bool = True, base_url: Optional[str] = None):
        self.dry_run = dry_run
        self.base_url = base_url or self.BASE_URL
        self._request_cache: dict = {}
        self._audit_log: list = []

    def recommend(
        self,
        user_id: str,
        steward_id: str,
        mandate_status: str,
        correlation_id: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> dict:
        request_id = f"req-{uuid.uuid4()}"
        correlation_id = correlation_id or str(uuid.uuid4())
        idempotency_key = correlation_id

        if idempotency_key in self._request_cache:
            self._audit("idempotent_hit", correlation_id, user_id)
            return self._request_cache[idempotency_key]

        payload = {
            "request_id": request_id,
            "correlation_id": correlation_id,
            "idempotency_key": idempotency_key,
            "user_profile": {
                "user_id": user_id,
                "steward_id": steward_id,
                "mandate_status": mandate_status,
                "context": context or {},
            },
            "policy_version": self.POLICY_VERSION,
        }

        headers = {
            "Content-Type": "application/json",
            "Correlation-ID": correlation_id,
            "Idempotency-Key": idempotency_key,
        }

        if self.dry_run:
            response = self._mock_response(payload)
        else:
            response = self._http_post_with_retry(
                url=f"{self.base_url}{self.ENDPOINT}",
                headers=headers,
                payload=payload,
            )

        self._request_cache[idempotency_key] = response
        self._audit("api_call", correlation_id, user_id, response.get("state"))
        return response

    def _mock_response(self, payload: dict) -> dict:
        mandate_status = payload["user_profile"]["mandate_status"]
        purchase_amount = payload["user_profile"]["context"].get("purchase_amount", 0)

        if mandate_status == "SUSPENDED":
            return {
                "error_code": 403,
                "error_type": "MANDATE",
                "message": "mandate_status=SUSPENDED: user blocked",
                "correlation_id": payload["correlation_id"],
            }

        spirit_score = 0.85
        requires_approval = purchase_amount >= 50000 or spirit_score < 0.8

        return {
            "decision_id": f"dec-{uuid.uuid4()}",
            "correlation_id": payload["correlation_id"],
            "state": "APPROVAL_PENDING" if requires_approval else "RECOMMENDATION",
            "recommendation": {
                "policy_id": f"policy-{self.POLICY_VERSION}",
                "reason": "High-value purchase" if requires_approval else "Standard recommendation",
                "requires_approval": requires_approval,
                "approval_gate": "HUMAN_REVIEW" if requires_approval else "NONE",
                "spirit_score": spirit_score,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _http_post_with_retry(self, url: str, headers: dict, payload: dict) -> dict:
        import time, json, urllib.request

        backoff = 1
        for attempt in range(self.MAX_RETRIES):
            try:
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=self.TIMEOUT_SECONDS) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except Exception as e:
                error_code = getattr(e, "code", 500)
                if error_code == 403:
                    return {
                        "error_code": 403,
                        "error_type": "MANDATE",
                        "message": str(e),
                        "correlation_id": payload["correlation_id"],
                    }
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    return {
                        "error_code": 500,
                        "error_type": "SYSTEM",
                        "message": str(e),
                        "correlation_id": payload["correlation_id"],
                    }

    def _audit(self, event: str, correlation_id: str, user_id: str, state: str = None):
        self._audit_log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "correlation_id": correlation_id,
            "user_id": user_id,
            "state": state,
            "dry_run": self.dry_run,
        })

    @property
    def audit_log(self) -> list:
        return list(self._audit_log)
