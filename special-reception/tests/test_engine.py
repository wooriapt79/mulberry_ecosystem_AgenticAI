import os

import pytest

os.environ["SESSION_SIGNING_SECRET"] = "test-secret-at-least-32-characters"

from app.catalog import CARD_TO_PERSONA
from app.engine import MAX_TURNS, SessionError, continue_session, start_session


def test_catalog_contains_phase_a_cards():
    assert len(CARD_TO_PERSONA) == 35
    assert CARD_TO_PERSONA["judgement"] == "reflection"


def test_session_reaches_five_turn_limit_without_storage():
    result = start_session("judgement", "reflection", now=1000)
    assert result["turn"] == 1
    for expected_turn in range(2, MAX_TURNS + 1):
        result = continue_session(result["session"], "가볍게 이야기할게요", now=1001)
        assert result["turn"] == expected_turn
    assert result["complete"] is True
    assert result["session"] is None


def test_expired_session_is_rejected():
    result = start_session("the-sun", now=1000)
    with pytest.raises(SessionError, match="expired session"):
        continue_session(result["session"], "안녕하세요", now=1600)


def test_tampered_session_is_rejected():
    result = start_session("the-sun", now=1000)
    token = result["session"]
    replacement = "A" if token[-1] != "A" else "B"
    with pytest.raises(SessionError, match="invalid session"):
        continue_session(token[:-1] + replacement, "안녕하세요", now=1001)


def test_high_risk_message_ends_session_with_fixed_guidance():
    result = start_session("the-hermit", now=1000)
    reply = continue_session(result["session"], "죽고 싶어요", now=1001)
    assert reply["complete"] is True
    assert reply["safety_route"] == "high_risk"
    assert "119" in reply["reply"]
    assert "109" in reply["reply"]


@pytest.mark.parametrize(
    ("message", "route"),
    [
        ("제 계좌번호를 적을게요", "personal_data"),
        ("이 약을 끊어도 될까요?", "professional_advice"),
        ("제가 결혼할까요?", "fortune_claim"),
    ],
)
def test_safety_routes(message, route):
    result = start_session("the-star", now=1000)
    reply = continue_session(result["session"], message, now=1001)
    assert reply["safety_route"] == route


def test_unsupported_card_is_rejected():
    with pytest.raises(SessionError, match="unsupported card"):
        start_session("not-a-card", now=1000)
