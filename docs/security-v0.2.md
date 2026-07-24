# Luna Open Reception v0.2 Security Controls

Status: implementation draft. This document does not authorize production deployment.

## Implemented controls

- One-time first-administrator bootstrap guarded by `ADMIN_BOOTSTRAP_TOKEN`
- Login failure auditing, configurable lockout threshold and lockout duration
- Constant-work password verification for unknown accounts to reduce timing enumeration
- Positive session TTL normalization and explicit account-disable permission enforcement
- Current-session logout and all-session logout
- Human administrator emergency session revocation and optional account disable
- Permission-based administrative gates for review, safety and security actions
- Audit events for failed login, lockout, authorization denial, revocation and bootstrap
- Provider-neutral Secret Provider and MFA/passkey interfaces

## Runtime rules

`ADMIN_BOOTSTRAP_TOKEN` SHALL be at least 32 unpredictable characters, supplied only at
runtime, and removed or rotated immediately after successful bootstrap. The endpoint is
permanently single-use once any `admin` exists.

`LOGIN_MAX_FAILURES` defaults to `5`. `LOGIN_LOCKOUT_MINUTES` defaults to `15`.
Responses do not disclose whether an unknown account exists.

## Permission map

| Role | Permissions |
|---|---|
| `steward_reviewer` | `steward:review` |
| `safety_operator` | `kill_switch:change` |
| `security_admin` | `session:revoke`, `account:disable` |
| `admin` | all permissions above |

No real administrator or secret is created by this version. Production role assignment,
two-person approval and external identity-provider integration remain future work.

## Remaining gates

- Run Compose config, build and full-stack health checks in a Docker-capable environment.
- Replace application table creation with versioned migrations in v0.3.
- Implement durable distributed rate limiting before multi-instance deployment.
- Connect the interfaces to an approved Secret Manager and MFA/passkey provider.
- Add two-person approval for critical administrative actions.
- Complete independent security review and penetration testing.
