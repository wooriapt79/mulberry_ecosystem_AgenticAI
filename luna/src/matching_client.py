"""Luna client boundary for Matching v0.4.

Luna transports Matching decisions; it does not calculate policy, Spirit
Score, mandate eligibility, or approval requirements.

Codex fixes applied (2026-07-31 TRANG Manager):
  - recommend(): idempotency key now bound to request fingerprint;
    conflicting reuse (different user/steward/mandate) raises ValueError.
  - _validate_response(): full envelope required; state must be
    'APPROVAL_PENDING' — partial or unsafe states are rejected.
"""

import hashlib
import json
import logging
import urllib.request
import uuid
from datetime import datetime, timezone
from typing import Callable, Optional

logger = logging.getLogger("luna.matching_client")


def _request_fingerprint(
    user_id: str, steward_id: str, mandate_status: str, context: Optional[dict]
) -> str:
    """Canonical SHA-256 fingerprint for an idempotency key binding."""
    payload = json.dumps(
        {
            "user_id": user_id,
            "steward_id": steward_id,
            "mandate_status": mandate_status,
            "context": context or {},
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


class MatchingClient:
    """Transport Matching recommendations in dry-run mode by default."""

    POLICY_VERSION = "v0.4"

    def __init__(
        self,
        dry_run: bool = True,
        base_url: Optional[str] = None,
        endpoint: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        max_retries: Optional[int] = None,
        mock_provider: Optional[Callable[[dict], dict]] = None,
    ):
        self.dry_run = dry_run
        self.base_url = base_url
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.mock_provider = mock_provider
        # Maps idempotency_key -> (fingerprint, response)
        self._request_cache: dict[str, tuple[str, dict]] = {}
        self._audit_log: list[dict] = []

    def recommend(
        self,
        user_id: str,
        steward_id: str,
        mandate_status: str,
        correlation_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        context: Optional[dict] = None,
    ) -> dict:
        correlation_id = correlation_id or f"corr-{uuid.uuid4()}"
        idempotency_key = idempotency_key or f"idem-{uuid.uuid4()}"
        fingerprint = _request_fingerprint(user_id, steward_id, mandate_status, context)

        if idempotency_key in self._request_cache:
            cached_fp, cached_response = self._request_cache[idempotency_key]
            if cached_fp != fingerprint:
                raise ValueError(
                    f"Idempotency key '{idempotency_key}' was already used with a "
                    "different request payload. Reuse is only permitted for identical "
                    "requests (same user_id, steward_id, mandate_status, and context)."
                )
            self._audit("idempotent_hit", correlation_id, idempotency_key, user_id)
            return cached_response

        payload = {
            "request_id": f"req-{uuid.uuid4()}",
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

        if self.dry_run:
            if self.mock_provider is None:
                raise RuntimeError(
                    "dry_run requires a Matching-owned mock_provider or approved fixture"
                )
            response = self.mock_provider(payload)
        else:
            self._validate_live_config()
            response = self._http_post(payload)

        self._validate_response(response, correlation_id)
        self._request_cache[idempotency_key] = (fingerprint, response)
        self._audit(
            "matching_response",
            correlation_id,
            idempotency_key,
            user_id,
            response.get("state"),
        )
        return response

    def _validate_live_config(self) -> None:
        missing = [
            name
            for name, value in (
                ("base_url", self.base_url),
                ("endpoint", self.endpoint),
                ("timeout_seconds", self.timeout_seconds),
                ("max_retries", self.max_retries),
            )
            if value is None
        ]
        if missing:
            raise RuntimeError(
                "Live Matching configuration is not approved: " + ", ".join(missing)
            )

    def _http_post(self, payload: dict) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Correlation-ID": payload["correlation_id"],
            "Idempotency-Key": payload["idempotency_key"],
        }
        request = urllib.request.Request(
            f"{self.base_url}{self.endpoint}",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _validate_response(response: dict, correlation_id: str) -> None:
        if response.get("correlation_id") != correlation_id:
            raise ValueError("Matching response correlation_id mismatch")

        # Full envelope required — partial responses are rejected.
        recommendation = response.get("recommendation")
        if recommendation is None:
            raise ValueError(
                "Matching response missing 'recommendation' envelope. "
                "Every response must include the full approval-pending structure."
            )
        required = {"policy_id", "reason", "requires_approval", "approval_gate"}
        if not required.issubset(recommendation):
            raise ValueError("Matching response is missing policy-owned fields")
        if recommendation["requires_approval"] is not True:
            raise ValueError("Phase 1 requires Human approval for every recommendation")

        # Enforce APPROVAL_PENDING — reject unsafe states (e.g. DRY_RUN_COMPLETED).
        state = response.get("state")
        if state != "APPROVAL_PENDING":
            raise ValueError(
                f"Matching response state must be 'APPROVAL_PENDING', got '{state}'. "
                "Responses outside the approval-pending envelope are rejected."
            )

    def _audit(
        self,
        event: str,
        correlation_id: str,
        idempotency_key: str,
        user_id: str,
        state: Optional[str] = None,
    ) -> None:
        self._audit_log.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": event,
                "correlation_id": correlation_id,
                "idempotency_key": idempotency_key,
                "user_id": user_id,
                "state": state,
                "dry_run": self.dry_run,
            }
        )

    @property
    def audit_log(self) -> list:
        return list(self._audit_log)
