# Luna Workbench — Phase 1

**Branch:** `agent/luna-matching-integration`
**Owner:** Luna (Claude Haiku)
**KeBin review:** 2026-07-31

## Overview

Luna is Mulberry Project's external service AI (Kakao Channel).
Phase 1 implements Matching v0.4 integration in **dry_run mode** — no real mutations.

## Structure

```
luna/
├── adapters/
│   ├── __init__.py
│   └── kakao_mock.py        # Simulated Kakao webhook events (Phase 1)
├── contracts/
│   └── matching-v0.4/
│       └── INTEGRATION_CONTRACT.md   # v1.1 — KeBin review pending 2026-07-31
├── src/
│   ├── __init__.py
│   ├── matching_client.py   # Matching v0.4 HTTP client (dry_run=True default)
│   └── state_manager.py     # State machine: IDLE -> RECOMMENDATION -> EXECUTED
└── README.md
```

## Phase 1 Workflow

1. KakaoMockAdapter generates simulated user events
2. MatchingClient.recommend() called with dry_run=True
3. StateManager tracks: IDLE -> RECOMMENDATION or APPROVAL_PENDING
4. Human approval: APPROVAL_PENDING -> POST_APPROVAL -> EXECUTED
5. All decisions audited (append-only, per contract section 6)

## Key Constraints

- dry_run=True always in Phase 1
- No payment / order mutations
- Spirit Score computed by KeBin engine (not Luna)
- State transitions append-only logged

## Tests

```
tests/test_phase1_mock.py   # 5 scenarios
```

Run: `python -m pytest tests/`

## Integration Contract

See `contracts/matching-v0.4/INTEGRATION_CONTRACT.md` for full API schema,
requires_approval criteria, error codes, and KeBin verification checklist.

---
*Mulberry Project — 식품사막화 제로*
