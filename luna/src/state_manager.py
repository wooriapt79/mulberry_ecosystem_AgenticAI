"""Human-gated state transitions for Luna Matching recommendations.

Codex fix applied (2026-07-31 TRANG Manager):
  - history property now returns deep copies of transition records so
    external code cannot mutate the manager's internal audit history.
"""

import copy
import logging
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger("luna.state_manager")


class MatchingState(str, Enum):
    IDLE = "IDLE"
    RECOMMENDED = "RECOMMENDED"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    HUMAN_APPROVED = "HUMAN_APPROVED"
    HUMAN_REJECTED = "HUMAN_REJECTED"
    ON_HOLD = "ON_HOLD"
    DRY_RUN_COMPLETED = "DRY_RUN_COMPLETED"


VALID_TRANSITIONS = {
    MatchingState.IDLE: [MatchingState.RECOMMENDED],
    MatchingState.RECOMMENDED: [MatchingState.APPROVAL_PENDING],
    MatchingState.APPROVAL_PENDING: [
        MatchingState.HUMAN_APPROVED,
        MatchingState.HUMAN_REJECTED,
        MatchingState.ON_HOLD,
    ],
    MatchingState.HUMAN_APPROVED: [MatchingState.DRY_RUN_COMPLETED],
    MatchingState.ON_HOLD: [
        MatchingState.APPROVAL_PENDING,
        MatchingState.HUMAN_REJECTED,
    ],
    MatchingState.HUMAN_REJECTED: [],
    MatchingState.DRY_RUN_COMPLETED: [],
}

HUMAN_ONLY_TARGETS = {
    MatchingState.HUMAN_APPROVED,
    MatchingState.HUMAN_REJECTED,
    MatchingState.ON_HOLD,
}


class StateManager:
    def __init__(self, correlation_id: str):
        self.correlation_id = correlation_id
        self._state = MatchingState.IDLE
        self._history: list[dict] = []
        self._record_transition(None, MatchingState.IDLE, "init", "system")

    @property
    def state(self) -> MatchingState:
        return self._state

    def transition(
        self, target: MatchingState, actor: str = "system", reason: str = ""
    ) -> bool:
        allowed = VALID_TRANSITIONS.get(self._state, [])
        if target not in allowed:
            raise ValueError(
                f"Invalid transition {self._state} -> {target}. "
                f"Allowed: {[state.value for state in allowed]}"
            )
        if target in HUMAN_ONLY_TARGETS and not actor.startswith("human:"):
            raise PermissionError(f"{target.value} requires an identified Human actor")

        previous = self._state
        self._state = target
        self._record_transition(previous, target, reason, actor)
        logger.info(
            "[STATE] %s: %s -> %s (actor=%s)",
            self.correlation_id,
            previous.value,
            target.value,
            actor,
        )
        return True

    def _record_transition(self, previous, current, reason, actor):
        self._history.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "from": previous.value if previous else None,
                "to": current.value,
                "actor": actor,
                "reason": reason,
            }
        )

    @property
    def history(self) -> list:
        """Return deep copies of transition records.

        Callers cannot mutate the manager's internal audit history through
        the returned objects (actor, reason, state fields are immutable
        from the caller's perspective).
        """
        return copy.deepcopy(self._history)

    def is_terminal(self) -> bool:
        return self._state in (
            MatchingState.HUMAN_REJECTED,
            MatchingState.DRY_RUN_COMPLETED,
        )
