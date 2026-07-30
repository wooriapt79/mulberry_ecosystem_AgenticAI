# Luna Workbench — Phase 1

**Branch:** `agent/luna-matching-integration`  
**Owner:** Luna  
**Review:** KeBin

Phase 1 connects Luna to Matching v0.4 in dry-run mode. Luna transports and
records Matching-owned decisions; it does not calculate Spirit Score, policy,
mandate eligibility, risk, thresholds, or approval requirements.

## Workflow

1. An adapter creates a simulated request.
2. `MatchingClient` sends it to a Matching-owned fixture in dry-run mode.
3. Luna validates and records the returned recommendation.
4. Every recommendation enters `APPROVAL_PENDING`.
5. An identified Human may approve, reject, or hold it.
6. Approved Phase 1 flows end at `DRY_RUN_COMPLETED`; no external action occurs.

## Safety

- `dry_run=True` by default.
- No payment, order, inventory, delivery, merge, or deployment without Human approval.
- Correlation and idempotency identifiers are separate.
- Live endpoint, timeout, retry, and error mappings remain TBD until verified.
- Luna may manage designated repositories through dedicated branches and Draft PRs.

## Tests

```bash
python -m unittest tests/test_phase1_mock.py -v
```

See `contracts/matching-v0.4/INTEGRATION_CONTRACT.md` for the current Draft
contract and remaining verification conditions.
