# Matching v0.4 Integration Contract

**Status:** Phase 1 Design Specification  
**Created:** 2026-07-30  
**KeBin Review:** Pending (2026-07-31)  
**Final Approval:** CEO re.eul (2026-08-03)

---

## 1. HTTP API Specification

### Endpoint
```
POST /api/v0.4/matching/recommend
Host: matching-service.internal
Content-Type: application/json
Correlation-ID: {uuid}
```

### Request Schema
- request_id: req-{uuid}
- correlation_id: corr-{uuid}
- user_profile: {user_id, steward_id, mandate_status, context}
- policy_version: v0.4

### Response Schema (Success)
- decision_id: dec-{uuid}
- state: RECOMMENDATION | APPROVAL_PENDING
- recommendation: {policy_id, reason, requires_approval}

### Error Handling
- 400 VALIDATION: Field missing or format error (Retry: YES)
- 403 MANDATE: No permission, policy rejection (Retry: NO)
- 500 SYSTEM: Server error (Retry: YES)

---

## 2. Safety Boundaries

- Spirit Score Recalculation: PROHIBITED
- Matching Policy Bypass: PROHIBITED
- Payment/Order/Shipping State Changes: PROHIBITED
- High-Risk Matching Without Approval: PROHIBITED

---

**Status:** Design confirmation → Awaiting KeBin review
