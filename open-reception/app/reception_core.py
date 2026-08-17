from __future__ import annotations

import hashlib
import hmac
import re
import uuid
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping


class ReceptionContractError(ValueError):
    """Raised when a Reception Core safety contract is violated."""


class CaseState(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    TRIAGED = "triaged"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_VISITOR = "waiting_for_visitor"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ESCALATED = "escalated"
    BLOCKED = "blocked"


ALLOWED_TRANSITIONS: dict[CaseState, frozenset[CaseState]] = {
    CaseState.DRAFT: frozenset({CaseState.SUBMITTED, CaseState.CANCELLED}),
    CaseState.SUBMITTED: frozenset({CaseState.TRIAGED, CaseState.REJECTED, CaseState.CANCELLED}),
    CaseState.TRIAGED: frozenset({CaseState.ASSIGNED, CaseState.ESCALATED, CaseState.BLOCKED, CaseState.REJECTED, CaseState.CANCELLED}),
    CaseState.ASSIGNED: frozenset({CaseState.IN_PROGRESS, CaseState.ESCALATED, CaseState.BLOCKED, CaseState.CANCELLED}),
    CaseState.IN_PROGRESS: frozenset({CaseState.WAITING_FOR_VISITOR, CaseState.RESOLVED, CaseState.ESCALATED, CaseState.BLOCKED, CaseState.CANCELLED}),
    CaseState.WAITING_FOR_VISITOR: frozenset({CaseState.IN_PROGRESS, CaseState.RESOLVED, CaseState.CANCELLED}),
    CaseState.RESOLVED: frozenset({CaseState.CLOSED, CaseState.IN_PROGRESS}),
    CaseState.ESCALATED: frozenset({CaseState.TRIAGED, CaseState.BLOCKED, CaseState.CANCELLED}),
    CaseState.BLOCKED: frozenset({CaseState.TRIAGED, CaseState.CANCELLED}),
    CaseState.CLOSED: frozenset(),
    CaseState.REJECTED: frozenset(),
    CaseState.CANCELLED: frozenset(),
}


FORBIDDEN_DATA_KEYS = frozenset({
    "sensitive_context",
    "shopmate_context",
    "emotional_state",
    "psychological_profile",
    "personality_inference",
    "conversation_raw",
    "channel_identity",
    "channel_session_id",
})
SAFE_TOKEN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


@dataclass(frozen=True)
class VisitorIdentity:
    visitor_id: str
    key_version: int


@dataclass(frozen=True)
class ReceptionRequest:
    visitor_id: str
    channel_type: str
    channel_event_id: str
    request_type: str
    summary: str
    desired_outcome: str
    visitor_update: str = ""
    sensitive_context: None = None

    def __post_init__(self) -> None:
        if self.sensitive_context is not None:
            raise ReceptionContractError("sensitive_context is reserved and must be null in v0.1")
        for name, value in (("channel_type", self.channel_type), ("request_type", self.request_type)):
            if not SAFE_TOKEN.fullmatch(value):
                raise ReceptionContractError(f"invalid {name}")
        if not self.visitor_id.startswith("vis_"):
            raise ReceptionContractError("visitor_id must be pseudonymous")
        if not self.channel_event_id or len(self.channel_event_id) > 128:
            raise ReceptionContractError("invalid channel_event_id")
        if not self.summary.strip() or len(self.summary) > 500:
            raise ReceptionContractError("invalid summary")
        if not self.desired_outcome.strip() or len(self.desired_outcome) > 500:
            raise ReceptionContractError("invalid desired_outcome")


def derive_visitor_identity(channel_type: str, external_subject: str, secret: bytes, key_version: int) -> VisitorIdentity:
    if not SAFE_TOKEN.fullmatch(channel_type):
        raise ReceptionContractError("invalid channel_type")
    if not external_subject or len(external_subject) > 256:
        raise ReceptionContractError("invalid external subject")
    if len(secret) < 32:
        raise ReceptionContractError("visitor identity secret must be at least 32 bytes")
    if key_version < 1:
        raise ReceptionContractError("key_version must be positive")
    material = f"{channel_type}\x1f{external_subject}".encode("utf-8")
    digest = hmac.new(secret, material, hashlib.sha256).hexdigest()
    return VisitorIdentity(visitor_id=f"vis_{digest}", key_version=key_version)


def validate_case_payload(payload: Mapping[str, Any]) -> None:
    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                normalized = str(key).strip().lower()
                if normalized in FORBIDDEN_DATA_KEYS and child not in (None, "", [], {}):
                    raise ReceptionContractError(f"{normalized} is not accepted in v0.1")
                walk(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                walk(child)

    walk(payload)


def transition_case(current: CaseState, target: CaseState, *, human_approved: bool = False) -> CaseState:
    if target not in ALLOWED_TRANSITIONS[current]:
        raise ReceptionContractError(f"transition {current.value}->{target.value} is not allowed")
    if target in {CaseState.ASSIGNED, CaseState.IN_PROGRESS} and not human_approved:
        raise ReceptionContractError("Human approval is required before assignment or work starts")
    return target


def new_correlation_id() -> str:
    return f"rc_{uuid.uuid4().hex}"
