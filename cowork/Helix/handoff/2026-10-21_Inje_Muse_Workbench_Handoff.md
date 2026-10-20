# Handoff — Helix GitHub Workbench and Inje Store Pilot
Date: 2026-10-21
From: Helix
To: KeBin / Mulberry implementation team
Status: Review requested

## Objective
Establish a GitHub-backed workbench and record today's decision to pursue a Raspberry Pi 5 store pilot for food-desert mitigation and voice-order care-signal routing, while contributing generic device integration to Muse.

## Artifacts
- [Workbench rules](../WORKBENCH.md)
- [Field lab architecture](../working/2026-10-21_Muse_RPi5_Inje_Store_Field_Lab_v0.1.md)
- [Muse sensor contribution plan](../working/2026-10-21_Muse_RPi5_Sensor_RFC_and_Draft_PR_Plan.md)
- [Upstream RFC #257](https://github.com/facebookincubator/muse-gadget-sdk/issues/257)

## Decisions
Store-first pilot; separate order and care paths; human oversight for care routing; optional Muse integration; use GitHub `cowork/` for shared documents. No recurring Muse monitoring.

## Review questions
1. Existing store phone number or separate order number?
2. Who is authorized to receive and act on care referrals, and what consent/urgent escalation protocol applies?
3. Which store and hardware will host the first controlled test?
4. What event schemas, ledger integration and offline queue are already implemented?
5. Who owns security and field test sign-off?

## Requested next action
KeBin reviews and records decisions. Keep this as Draft PR until team review. No live resident data or operational changes in this handoff.
