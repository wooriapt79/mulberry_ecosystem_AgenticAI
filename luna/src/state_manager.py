"""
Luna State Manager
State transitions for Matching v0.4 recommendations.
"""
import logging
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger("luna.state_manager")

class MatchingState(str, Enum):
    IDLE = "IDLE"
    RECOMMENDATION = "RECOMMENDATION"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    POST_APPROVAL = "POST_APPROVAL"
    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"
    ON_HOLD = "ON_HOLD"
    ROLLBACK = "ROLLBACK"

VALID_TRANSITIONS = {
    MatchingState.IDLE: [MatchingState.RECOMMENDATION],
    MatchingState.RECOMMENDATION: [MatchingState.POST_APPROVAL, MatchingState.APPROVAL_PENDING],
    MatchingState.APPROVAL_PENDING: [MatchingState.POST_APPROVAL, MatchingState.REJECTED, MatchingState.ON_HOLD],
    MatchingState.POST_APPROVAL: [MatchingState.EXECUTED],
    MatchingState.ON_HOLD: [MatchingState.APPROVAL_PENDING, MatchingState.REJECTED],
    MatchingState.EXECUTED: [],
    MatchingState.REJECTED: [MatchingState.ROLLBACK],
    MatchingState.ROLLBACK: [],
}

class StateManager:
    def __init__(self, correlation_id: str):
        self.correlation_id = correlation_id
        self._state = MatchingState.IDLE
        self._history: list = []
        self._record_transition(None, MatchingState.IDLE, "init")

    @property
    def state(self) -> MatchingState: return self._state

    def transition(self, target: MatchingState, actor: str = "system", reason: str = "") -> bool:
        allowed = VALID_TRANSITIONS.get(self._state, [])
        if target not in allowed:
            raise ValueError(f"Invalid transition {self._state} -> {target}. Allowed: {[s.value for s in allowed]}")
        prev = self._state
        self._state = target
        self._record_transition(prev, target, reason, actor)
        logger.info(f"[STATE] {self.correlation_id}: {prev.value} -> {target.value} (actor={actor})")
        return True

    def _record_transition(self, prev, current, reason, actor="system"):
        self._history.append({"timestamp": datetime.now(timezone.utc).isoformat(),
            "from": prev.value if prev else None, "to": current.value, "actor": actor, "reason": reason})

    @property
    def history(self) -> list: return list(self._history)

    def is_terminal(self) -> bool:
        return self._state in (MatchingState.EXECUTED, MatchingState.ROLLBACK)
