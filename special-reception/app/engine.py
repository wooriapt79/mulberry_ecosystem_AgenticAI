from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from dataclasses import dataclass

from .catalog import CARD_TO_PERSONA, PERSONAS

MAX_TURNS = 5
SESSION_TTL_SECONDS = 10 * 60
MAX_MESSAGE_LENGTH = 500

HIGH_RISK = re.compile(
    r"(죽고\s*싶|자살|극단적\s*선택|자해|목숨을\s*끊|살기\s*싫)", re.IGNORECASE
)
PROFESSIONAL = re.compile(
    r"(진단|처방|약을\s*(끊|먹)|투자\s*추천|주식\s*종목|법률\s*판단|소송)", re.IGNORECASE
)
FORTUNE = re.compile(
    r"(미래를\s*맞|운명을\s*정|확실히\s*(되|오|맞)|로또|당첨|결혼할까|헤어질까)", re.IGNORECASE
)
PERSONAL_DATA = re.compile(
    r"(주민등록번호|비밀번호|계좌번호|카드번호|휴대폰\s*번호|전화번호|주소)", re.IGNORECASE
)


class SessionError(ValueError):
    pass


@dataclass(frozen=True)
class Session:
    card: str
    persona: str
    turn: int
    issued_at: int


def _secret() -> bytes:
    configured = os.getenv("SESSION_SIGNING_SECRET")
    if configured:
        return configured.encode("utf-8")
    if not hasattr(_secret, "ephemeral"):
        _secret.ephemeral = secrets.token_bytes(32)  # type: ignore[attr-defined]
    return _secret.ephemeral  # type: ignore[attr-defined]


def _encode(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    body = base64.urlsafe_b64encode(raw).rstrip(b"=")
    signature = hmac.new(_secret(), body, hashlib.sha256).digest()
    return f"{body.decode()}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode()}"


def _decode(token: str, now: int | None = None) -> Session:
    try:
        body_text, signature_text = token.split(".", 1)
        body = body_text.encode()
        signature = base64.urlsafe_b64decode(signature_text + "=" * (-len(signature_text) % 4))
        expected = hmac.new(_secret(), body, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected):
            raise SessionError("invalid session")
        raw = base64.urlsafe_b64decode(body_text + "=" * (-len(body_text) % 4))
        payload = json.loads(raw)
        session = Session(
            card=str(payload["card"]),
            persona=str(payload["persona"]),
            turn=int(payload["turn"]),
            issued_at=int(payload["issued_at"]),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        if isinstance(exc, SessionError):
            raise
        raise SessionError("invalid session") from exc

    current = int(time.time()) if now is None else now
    if current - session.issued_at >= SESSION_TTL_SECONDS:
        raise SessionError("expired session")
    if session.card not in CARD_TO_PERSONA or session.persona not in PERSONAS:
        raise SessionError("invalid session")
    if session.turn < 1 or session.turn > MAX_TURNS:
        raise SessionError("invalid session")
    return session


def start_session(card: str, persona: str | None = None, now: int | None = None) -> dict[str, object]:
    card_code = card.strip().lower()
    if card_code not in CARD_TO_PERSONA:
        raise SessionError("unsupported card")
    persona_code = (persona or CARD_TO_PERSONA[card_code]).strip().lower()
    if persona_code not in PERSONAS:
        raise SessionError("unsupported persona")
    issued_at = int(time.time()) if now is None else now
    selected = PERSONAS[persona_code]
    session = Session(card=card_code, persona=persona_code, turn=1, issued_at=issued_at)
    return {
        "session": _encode(session.__dict__),
        "turn": 1,
        "remaining_turns": MAX_TURNS - 1,
        "expires_in_seconds": SESSION_TTL_SECONDS,
        "persona": {"code": selected.code, "name": selected.name, "tagline": selected.tagline},
        "reply": " ".join(selected.openings),
        "notice": "재미와 자기성찰을 위한 익명 체험이며 예언·진단·상담 서비스가 아닙니다.",
    }


def _safe_reply(message: str, persona_code: str, turn: int) -> tuple[str, str | None]:
    if HIGH_RISK.search(message):
        return (
            "지금 즉각적인 위험이 있다면 혼자 있지 말고 119 또는 가까운 응급실에 연락해 주세요. "
            "한국에서는 자살예방 상담전화 109도 이용할 수 있어요. 이 데모는 위기상담이나 신고를 대신할 수 없습니다.",
            "high_risk",
        )
    if PERSONAL_DATA.search(message):
        return (
            "개인정보는 입력하거나 공유하지 말아 주세요. 이 체험에는 이름·연락처·주소·계좌 정보가 필요하지 않습니다.",
            "personal_data",
        )
    if PROFESSIONAL.search(message):
        return (
            "이 체험은 의료·법률·투자 판단을 제공하지 않아요. 중요한 결정은 자격 있는 전문가와 확인해 주세요.",
            "professional_advice",
        )
    if FORTUNE.search(message):
        return (
            "카드는 미래나 운명을 확정하지 않아요. 대신 지금 선택 가능한 관점을 함께 살펴볼 수 있어요.",
            "fortune_claim",
        )
    persona = PERSONAS[persona_code]
    index = min(max(turn - 2, 0), len(persona.replies) - 1)
    return persona.replies[index], None


def continue_session(token: str, message: str, now: int | None = None) -> dict[str, object]:
    session = _decode(token, now=now)
    clean = message.strip()
    if not clean:
        raise SessionError("empty message")
    if len(clean) > MAX_MESSAGE_LENGTH:
        raise SessionError("message too long")
    if session.turn >= MAX_TURNS:
        raise SessionError("session complete")

    next_turn = session.turn + 1
    reply, safety_route = _safe_reply(clean, session.persona, next_turn)
    complete = next_turn >= MAX_TURNS or safety_route == "high_risk"
    next_token = None
    if not complete:
        next_session = Session(
            card=session.card,
            persona=session.persona,
            turn=next_turn,
            issued_at=session.issued_at,
        )
        next_token = _encode(next_session.__dict__)

    return {
        "session": next_token,
        "turn": next_turn,
        "remaining_turns": 0 if complete else MAX_TURNS - next_turn,
        "complete": complete,
        "safety_route": safety_route,
        "reply": reply,
    }
