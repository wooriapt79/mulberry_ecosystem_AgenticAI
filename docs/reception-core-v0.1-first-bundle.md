# Reception Core v0.1 — First Bundle Contract

Related: Issue #12, Issue #19

## Purpose

This first bundle establishes deterministic domain contracts before database migrations or public APIs are added. It extends `open-reception`; it does not create a parallel policy engine.

## Boundaries

- Matching v0.4 remains the only recommendation policy source.
- Assignment and work start require an explicit Human approval signal.
- All behavior remains `dry_run` and `recommendation_only`.
- No payment, contract, inventory, delivery, external message, Kakao webhook, or production deployment is enabled.
- Passport users and anonymous visitors remain separate identity domains.
- Channel identities are never copied into a Case, audit event, or correlation ID.

## Case contract

The initial state machine is:

```text
draft -> submitted -> triaged -> assigned -> in_progress
                                      |             |
                                      |             +-> waiting_for_visitor
                                      |             +-> resolved -> closed
                                      +-> escalated / blocked
```

`rejected` and `cancelled` are terminal. Invalid transitions fail closed. Transitions into `assigned` and `in_progress` require Human approval.

## Visitor identity

`derive_visitor_identity()` creates a stable HMAC-SHA256 pseudonymous identifier from a channel type and an opaque external subject. Only `visitor_id` and `key_version` may enter the Reception Core contract.

- Secrets must be at least 32 bytes and come from a future Secret Provider.
- The raw channel subject is not returned or stored by this module.
- Passport `user_id` is not part of `ReceptionRequest`.
- Cross-channel identity merging and automated key rotation remain v0.2 work.

## Data separation

The first bundle accepts structured summaries and desired outcomes, not raw conversations. The following keys cannot carry values, including when nested under `internal_note` or another object:

- `sensitive_context`
- `shopmate_context`
- `emotional_state`
- `psychological_profile`
- `personality_inference`
- `conversation_raw`
- `channel_identity`
- `channel_session_id`

`sensitive_context` exists only as a null reservation in v0.1. RBAC, encryption, retention/deletion, audit policy, and consent must be designed and approved before any sensitive value is accepted.

## Correlation

The generated `rc_<uuid>` identifier is the future join key for Case, Matching request/decision, Human approval, and audit events. It contains no visitor or channel identity.

## Validation

- deterministic state transition tests
- Human approval gate tests
- HMAC identity and key-version tests
- nested sensitive-data rejection tests
- terminal-state and invalid-transition tests

The current bundle is a domain baseline only. API, persistence migration, Web Adapter, Matching integration, and durable queue are separate reviewable bundles tracked in Issue #19.
