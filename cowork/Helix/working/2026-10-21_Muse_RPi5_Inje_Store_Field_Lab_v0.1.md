# Muse × Mulberry — Inje Store Field Lab v0.1
Date: 2026-10-21
Owner: Helix / Mulberry Research Lab
Status: Working draft — not deployed, not field-validated

## 1. Purpose
Collaborate with Inje-gun business community stakeholders to pilot a Raspberry Pi 5-based local store gateway for **food-desert access** and **care-signal routing from voice orders**. Muse Gadget SDK is an optional, replaceable device integration and learning layer, not the telephony, speech recognition, or care decision engine.

## 2. Confirmed direction vs assumptions
- User-confirmed: first pilot venue type is a **store**; core services are food-desert mitigation and care routing from spoken orders.
- User-confirmed: GitHub `cowork/` is the Helix–KeBin collaboration workspace.
- Public upstream: [Muse RFC #257](https://github.com/facebookincubator/muse-gadget-sdk/issues/257), opened by `wooriapt79`; requests maintainer advice on Linux command integration vs [PR #85](https://github.com/facebookincubator/muse-gadget-sdk/pull/85).
- Not yet confirmed: store identity, telephone number architecture, call provider, staffing, resident consent workflow, hardware inventory, network availability, field agreements, measured performance, Muse maintainer endorsement.

## 3. Proposed logical architecture
```text
Resident phone order
  -> Telephony ingress + consent/notice + speech-to-text (to be selected)
  -> Mulberry Store Gateway (Raspberry Pi 5)
       -> Order Worker: product/quantity confirmation -> store order ledger -> fulfillment
       -> Care Signal Router: candidate signal -> consent/urgency check -> authorized human review
       -> Audit + retry queue + device health
       -> Optional Muse Linux Gadget adapter (read-only sensor / device commands)
  -> Human STEWARD oversight and follow-up
```

**Boundary:** Order and care records have separate access control, retention and audit. A care signal is not a diagnosis. Avoid automatic disclosure to third parties without lawful basis and an agreed consent/escalation policy. Explicit emergencies require a separately approved procedure.

## 4. MVP slices
| Slice | Minimum demonstrable result | Exclusions |
|---|---|---|
| Order capture | Speech/text -> item and quantity -> human-confirmed order | Autonomous payments |
| Care routing | Spoken need -> candidate flag -> human review / consent | Medical diagnosis, autonomous dispatch |
| Store ledger | Event IDs, status, retry/idempotency, reconciliation hooks | POS/VAN integration until approved |
| Device health | Pi 5 status, connectivity, restart and failure events | Remote privileged shell |
| Muse sensor | SHT31 read-only `sensors.read` example, mock tests | WiFi CSI, camera, actuators |

## 5. Safety and privacy gates
1. Run device adapter as dedicated non-admin user; allowlist sensor IDs; never expose arbitrary shell, device paths, or I²C addresses to requests.
2. No credentials, phone numbers, raw call recordings, health narratives or identifiable resident data in GitHub. Use synthetic fixtures.
3. Consent/notice and retention policy reviewed before any live call capture.
4. Human confirmation for ambiguous orders and care routing; escalation owner and availability defined before launch.
5. Define offline behavior: durable local queue, idempotent replay, explicit sync state, and no silent loss of orders.
6. Establish rollback, incident contact, physical device maintenance and software update process.

## 6. Proposed acceptance metrics (targets TBD, not measured)
- Order item/quantity confirmation accuracy; call-to-order completion; duplicate prevention.
- Care-signal precision/recall and human-review response time, with carefully approved synthetic test cases first.
- Network outage recovery and event replay; device uptime and failure diagnosis.
- Resident food access: successfully fulfilled orders, delivery lead time, and service accessibility.

## 7. Muse contribution boundary
Upstream: generic Raspberry Pi/Linux read-only sensor example, tests, docs, and reproducible device-health feedback. Mulberry-only: telephony integration, store and payment ledgers, STEWARD/Worker AI, care router, privacy controls. Do not represent Meta/Muse as an official pilot partner without agreement.

## 8. Decisions and open questions
**Decided:** store-first; food access + voice-order care routing; Raspberry Pi 5 gateway; GitHub cowork; upstream RFC #257; no periodic repo monitoring.
**Open:** existing store line vs dedicated order number; exact telephony interface; consent workflow; pilot shop; human care receiver; first hardware bill of materials; upstream maintainer response; target thresholds.

## 9. Next action
KeBin and implementation team review architecture and open questions. Prepare synthetic call-order/care-signal test scenarios. Coordinate Muse integration approach on #257 before upstream Draft PR. No production deployment or external messaging is authorized by this document.
