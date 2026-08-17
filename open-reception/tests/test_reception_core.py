import pytest

from app.reception_core import (
    CaseState,
    ReceptionContractError,
    ReceptionRequest,
    derive_visitor_identity,
    new_correlation_id,
    transition_case,
    validate_case_payload,
)


SECRET = b"v0.1-test-secret-is-at-least-32-bytes"


def test_visitor_identity_is_stable_pseudonymous_and_versioned():
    first = derive_visitor_identity("web", "opaque-channel-subject", SECRET, 1)
    second = derive_visitor_identity("web", "opaque-channel-subject", SECRET, 1)
    assert first == second
    assert first.visitor_id.startswith("vis_")
    assert "opaque-channel-subject" not in first.visitor_id
    assert first.key_version == 1


def test_identity_rejects_short_secret():
    with pytest.raises(ReceptionContractError, match="at least 32 bytes"):
        derive_visitor_identity("web", "subject", b"short", 1)


def test_request_keeps_passport_user_out_and_sensitive_context_null():
    request = ReceptionRequest(
        visitor_id=derive_visitor_identity("web", "subject", SECRET, 1).visitor_id,
        channel_type="web",
        channel_event_id="evt-1",
        request_type="food_access",
        summary="공동구매 문의",
        desired_outcome="가능한 접수 절차 확인",
    )
    assert request.sensitive_context is None
    assert "user_id" not in request.__dict__


def test_non_null_sensitive_context_is_rejected():
    with pytest.raises(ReceptionContractError, match="must be null"):
        ReceptionRequest(
            visitor_id="vis_123",
            channel_type="web",
            channel_event_id="evt-1",
            request_type="food_access",
            summary="문의",
            desired_outcome="답변",
            sensitive_context={"mood": "sad"},  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("field", ["sensitive_context", "shopmate_context", "emotional_state", "psychological_profile", "conversation_raw", "channel_identity"])
def test_sensitive_or_raw_data_cannot_be_hidden_in_nested_payload(field):
    with pytest.raises(ReceptionContractError):
        validate_case_payload({"internal_note": {field: "must-not-be-stored"}})


def test_assignment_and_work_start_require_human_approval():
    with pytest.raises(ReceptionContractError, match="Human approval"):
        transition_case(CaseState.TRIAGED, CaseState.ASSIGNED)
    assert transition_case(CaseState.TRIAGED, CaseState.ASSIGNED, human_approved=True) == CaseState.ASSIGNED
    with pytest.raises(ReceptionContractError, match="Human approval"):
        transition_case(CaseState.ASSIGNED, CaseState.IN_PROGRESS)


def test_invalid_transition_is_rejected_and_terminal_state_stays_closed():
    with pytest.raises(ReceptionContractError, match="not allowed"):
        transition_case(CaseState.DRAFT, CaseState.IN_PROGRESS, human_approved=True)
    with pytest.raises(ReceptionContractError, match="not allowed"):
        transition_case(CaseState.CLOSED, CaseState.TRIAGED)


def test_correlation_id_contains_no_identity():
    correlation_id = new_correlation_id()
    assert correlation_id.startswith("rc_")
    assert len(correlation_id) == 35
