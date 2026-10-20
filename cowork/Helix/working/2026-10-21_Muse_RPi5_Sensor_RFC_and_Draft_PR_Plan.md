# Muse Gadget SDK — Raspberry Pi 5 Sensor RFC and Draft PR Plan
Date: 2026-10-21
Owner: Helix / Mulberry Research Lab
Status: RFC published; upstream design decision pending

## Upstream reference
- [Issue #257 — Raspberry Pi 5 read-only I²C Sensor Skill example](https://github.com/facebookincubator/muse-gadget-sdk/issues/257)
- [PR #85 — owner-defined Linux gadget commands](https://github.com/facebookincubator/muse-gadget-sdk/pull/85)
- [Muse Linux SDK](https://github.com/facebookincubator/muse-gadget-sdk/tree/main/linux)
- [Community skills](https://github.com/facebookincubator/muse-gadget-sdk/tree/main/skills)

## Proposed minimum implementation
- Raspberry Pi 5, Raspberry Pi OS 64-bit, SHT31 I²C sensor.
- Read-only command `sensors.read` or equivalent registered owner-defined command.
- Fixed allowlisted sensor ID; no caller-selected I²C address, filesystem path, shell or privileged action.
- Structured temperature in Celsius, relative humidity in percent, UTC observation timestamp and bounded error response.
- Defined errors: invalid sensor ID, unavailable, timeout, CRC failure.
- Mock-based tests in CI, wiring/setup documentation, actual Pi 5 test evidence **only after performed**.
- Proposed validation: 100 consecutive reads, failure/recovery exercise, existing Linux test suite. This is a target, not a completed test.

## Integration decision
Ask maintainers whether to build atop unmerged PR #85 or add a small optional Linux executor command. Do not create a conflicting upstream implementation before guidance. Linux command implementation and Markdown community `SKILL.md` are distinct artifacts.

## Contribution stages
1. RFC #257 (done, submitted by `wooriapt79`).
2. Integration direction confirmed (pending).
3. Fork and feature branch; adapter, tests, docs (pending).
4. Local tests and hardware validation (pending).
5. Upstream Draft PR with test evidence and security limitations (pending).

## Field lab relevance
The store pilot's main use cases are food-desert order capture and human-reviewed care-signal routing from voice orders. SHT31 is a **secondary, read-only device integration experiment**, not a dependency of telephony or care routing. Keep Muse an optional adapter; do not claim Muse supports phone orders, STT or care inference.

## Next action
Monitor #257 **only when actively working**, not periodically. Record maintainer decision and revise implementation plan before code submission.
