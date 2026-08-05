import pytest

from luna.src.matching_client import MatchingClient


def provider(payload):
    return {"correlation_id": payload["correlation_id"], "state": "APPROVAL_PENDING",
            "recommendation": {"policy_id": "p-1", "reason": {"score": 1},
            "requires_approval": True, "approval_gate": {"actor": "human"}}}


def test_cached_response_is_deeply_isolated():
    client = MatchingClient(mock_provider=provider)
    kwargs = dict(user_id="u", steward_id="s", mandate_status="active",
                  correlation_id="corr", idempotency_key="idem")
    first = client.recommend(**kwargs)
    first["recommendation"]["reason"]["score"] = -1
    second = client.recommend(**kwargs)
    assert second["recommendation"]["reason"]["score"] == 1


def test_audit_log_is_deeply_isolated():
    client = MatchingClient(mock_provider=provider)
    client.recommend("u", "s", "active", correlation_id="corr", idempotency_key="idem")
    exposed = client.audit_log
    exposed[0]["event"] = "tampered"
    assert client.audit_log[0]["event"] != "tampered"


def test_idempotency_key_rejects_changed_payload():
    client = MatchingClient(mock_provider=provider)
    client.recommend("u", "s", "active", correlation_id="corr", idempotency_key="idem")
    with pytest.raises(ValueError):
        client.recommend("u2", "s", "active", correlation_id="corr", idempotency_key="idem")
