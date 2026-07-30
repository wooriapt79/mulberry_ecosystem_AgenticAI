# 📋 Matching v0.4 Integration Contract

**상태:** Phase 1 설계 확정본 (v1.1)
**작성일:** 2026-07-30
**수정일:** 2026-07-30 (TRANG Manager 리뷰 반영)
**KeBin 검증:** 2026-07-31 예정
**최종 승인:** CEO re.eul (2026-08-03)

---

## 1. HTTP API 명세

### Endpoint

```
POST /api/v0.4/matching/recommend
Host: matching-service.internal
Content-Type: application/json
Correlation-ID: {uuid4}
Idempotency-Key: {uuid4}
```

### Request Schema

```json
{
  "request_id": "req-{uuid4}",
  "correlation_id": "corr-{uuid4}",
  "idempotency_key": "idem-{uuid4}",
  "user_profile": {
    "user_id": "string (required)",
    "steward_id": "string (required)",
    "mandate_status": "ACTIVE | SUSPENDED | NONE (required — 권한 게이트 판단 기준)",
    "context": {
      "purchase_amount": "number (optional)",
      "delivery_address": "string (optional)"
    }
  },
  "policy_version": "v0.4"
}
```

> **`mandate_status` 필수 처리 이유:** Spirit Score 게이트 및 권한 검사의 핵심 입력값.
> `SUSPENDED` 상태 유저는 MANDATE 에러(403)로 즉시 차단.

### Response Schema (Success — requires_approval: false)

```json
{
  "decision_id": "dec-{uuid4}",
  "correlation_id": "corr-{uuid4}",
  "state": "RECOMMENDATION",
  "recommendation": {
    "policy_id": "string",
    "reason": "string",
    "requires_approval": false,
    "approval_gate": "NONE",
    "spirit_score": "number (0.0 ~ 1.0)"
  },
  "timestamp": "ISO8601"
}
```

### Response Schema (Success — requires_approval: true)

```json
{
  "decision_id": "dec-{uuid4}",
  "correlation_id": "corr-{uuid4}",
  "state": "APPROVAL_PENDING",
  "recommendation": {
    "policy_id": "string",
    "reason": "string",
    "requires_approval": true,
    "approval_gate": "HUMAN_REVIEW | SUPERVISOR_CHECK",
    "spirit_score": "number (0.0 ~ 1.0)"
  },
  "timestamp": "ISO8601"
}
```

### Response Schema (Error)

```json
{
  "error_code": "400 | 403 | 500",
  "error_type": "VALIDATION | MANDATE | POLICY | SYSTEM",
  "message": "string",
  "correlation_id": "corr-{uuid4}"
}
```

---

## 2. Correlation ID & Idempotency

### 역할 분리

| 필드 | 역할 | 생명주기 |
|------|------|----------|
| `correlation_id` | 요청 추적 — 전체 흐름에서 불변 | 요청 생성 시 발급, 감사 로그까지 동일 값 |
| `idempotency_key` | 중복 실행 방지 — 재시도 식별 | 재시도 포함 동일 요청은 동일 키 사용 |

> **운영 규칙:** 초기 요청에서는 `correlation_id == idempotency_key` (UUID4 동일 발급)로 단순화.
> 재시도 시에는 `idempotency_key`를 동일하게 유지하되 `correlation_id`는 별도 추적 가능.

### Propagation

1. Matching API 호출 시 `Correlation-ID` + `Idempotency-Key` 헤더 포함
2. `decision_id ↔ correlation_id` 매핑 저장 (PR #3 hash-chain audit에 기록)
3. 중복 요청 수신 시 → 이전 결과 반환 (재계산 ❌)

---

## 3. `requires_approval` 판단 기준

| 조건 | 값 | `approval_gate` |
|------|----|-----------------|
| Spirit Score ≥ 0.8 AND 위험도 LOW AND 금액 < 50,000원 | `false` | `NONE` |
| Spirit Score 0.5 ~ 0.8 OR 금액 50,000 ~ 200,000원 | `true` | `HUMAN_REVIEW` |
| Spirit Score < 0.5 OR 금액 ≥ 200,000원 OR 위험도 HIGH | `true` | `SUPERVISOR_CHECK` |
| mandate_status == SUSPENDED | 403 MANDATE 에러 (추천 자체 불가) | — |

> **jr.Agent 감독자 요건:** `SUPERVISOR_CHECK` 게이트는 활성 감독자가 존재할 때만 허용.
> 활성 감독자 없음 → 500 SYSTEM 에러 반환 (silent pass ❌).

---

## 4. State Transitions

```
IDLE
  ↓ POST /recommend
RECOMMENDATION
  ├─ requires_approval=false → POST_APPROVAL → EXECUTED
  │    └─ (Spirit Score ≥ 0.8 AND 저위험 AND 소액 조건 충족)
  └─ requires_approval=true → APPROVAL_PENDING
       ├─ (Human Accept)  → POST_APPROVAL → EXECUTED
       ├─ (Human Reject)  → REJECTED → ROLLBACK
       └─ (Human Hold)    → ON_HOLD (재배정 가능)
```

> ⚠️ `requires_approval=false` 경로도 `POST_APPROVAL` 단계를 거침.
> Spirit Score 재계산 없이 확정 기록만 남김. Human 개입 없이 자동 EXECUTED 처리.

---

## 5. Error Handling

| HTTP | Type | Description | Retry |
|------|------|-------------|-------|
| 400 | VALIDATION | 필드 누락, 형식 오류, `policy_version` 불일치 | ✅ |
| 403 | MANDATE | 권한 없음, `mandate_status=SUSPENDED` | ❌ |
| 403 | POLICY | 정책 위반 — 도메인 팩 규칙 거부 | ❌ |
| 500 | SYSTEM | 서버 오류, 활성 감독자 없음 | ✅ |

### Retry Strategy

- Max Retries: 3
- Backoff: Exponential (1s → 2s → 4s)
- Timeout: 10s per request
- 403 에러는 Retry 금지 (재시도해도 동일 결과)

---

## 6. Audit Log 연동 (PR #3 참조)

이 계약서의 감사 요건은 PR #3에서 구현된 hash-chain audit을 사용합니다.

```
감사 저장소: open-reception audit chain (PR #3)
알고리즘: SHA-256 hash-chain + UTC 정규화
직렬화: PostgreSQL row lock / SQLite write lock
추적 항목:
  - 요청 수신 (correlation_id, idempotency_key, user_id)
  - 추천 결정 (decision_id, policy_id, spirit_score, requires_approval)
  - Human 결정 (승인/거절/보류, 결정자 ID, timestamp)
  - state transition 전체 이력
```

> append-only 강제 — UPDATE/DELETE 금지 (PR #3 적용)

---

## 7. Safety Boundaries

✅ **금지사항:**
- Spirit Score 재계산 ❌
- Matching 정책 우회 ❌
- 결제/주문/배송 상태 변경 ❌
- Human 승인 없는 `SUPERVISOR_CHECK` 등급 매칭 ❌
- 활성 감독자 부재 시 silent pass ❌

✅ **필수조건:**
- Dry-run 모드 기본값 (`dry_run=true`)
- 모든 요청/응답 감사 기록 (PR #3 hash-chain)
- KeBin 리뷰 후 merge
- `policy_version: v0.4` 명시 필수

---

## 8. KeBin 검증 항목 (2026-07-31)

- [ ] 실제 엔드포인트 URL 확인 (`matching-service.internal` → 실 도메인)
- [ ] HTTP 에러 코드 매핑 검증 (특히 POLICY 403 처리)
- [ ] Timeout SLA 10초 적절성 확인
- [ ] Retry 횟수 3회 & backoff 간격 적절성
- [ ] Spirit Score 임계값 (0.5 / 0.8) PR #4 구현과 일치 여부
- [ ] 금액 기준값 (50,000 / 200,000원) 도메인 팩 v1과 일치 여부
- [ ] 활성 감독자 부재 처리 로직 확인
- [ ] PR #3 audit chain 연동 실제 동작 검증

---

**Status:** ✅ 설계 확정본 v1.1 → KeBin 검토 대기
