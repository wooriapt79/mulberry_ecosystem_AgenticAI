# Matching v0.4 Integration Contract

**상태:** Phase 1 Draft — KeBin 검증 중  
**원칙:** Luna는 Matching의 정책 결과를 소비하며 정책을 계산하지 않는다.

## 1. Phase 1 경계

- Luna는 요청 전달, 응답 검증, 상태 추적, 감사 기록을 담당한다.
- Spirit Score, 위험도, 금액 임계값, mandate 판정, `requires_approval`은 Matching 정책 영역이다.
- Phase 1의 모든 추천은 Human 승인 대상이며 실제 결제·주문·배송을 실행하지 않는다.
- Luna의 저장소 관리 기능은 허용하되 전용 브랜치와 Draft PR을 기본 통제로 사용한다.

## 2. HTTP API

다음 항목은 실제 Matching v0.4 구현과 대조 후 확정한다.

| 항목 | 상태 |
|---|---|
| Base URL 및 endpoint | TBD |
| Timeout SLA | TBD |
| Retry 횟수·backoff | TBD |
| HTTP 오류 매핑 | TBD |
| 감독자 부재 처리 | TBD — 서버 장애와 정책 보류를 구분 |

승인 전에는 `dry_run=true`와 Matching 소유 fixture만 사용한다. 임의의 내부 주소,
임계값 또는 오류 코드를 운영 계약으로 간주하지 않는다.

### Request envelope

```json
{
  "request_id": "req-{uuid4}",
  "correlation_id": "corr-{uuid4}",
  "idempotency_key": "idem-{uuid4}",
  "user_profile": {
    "user_id": "string",
    "steward_id": "string",
    "mandate_status": "string",
    "context": {}
  },
  "policy_version": "v0.4"
}
```

### Response envelope

```json
{
  "decision_id": "string",
  "correlation_id": "corr-{uuid4}",
  "state": "APPROVAL_PENDING",
  "recommendation": {
    "policy_id": "string",
    "reason": "string",
    "requires_approval": true,
    "approval_gate": "HUMAN_REVIEW"
  },
  "timestamp": "ISO8601"
}
```

응답의 정책 필드는 Matching이 제공한다. Luna는 이를 생성·변경·재계산하지 않는다.

## 3. Correlation ID와 Idempotency Key

| 필드 | 역할 |
|---|---|
| `correlation_id` | 전체 흐름과 감사 이벤트 추적 |
| `idempotency_key` | 동일 업무 요청의 중복 처리 방지 |

두 값은 별도로 발급하고 별도 필드와 헤더로 전달한다. 중복 판정은
`idempotency_key`를 기준으로 한다. 메모리 캐시는 Phase 1 테스트 편의 기능일 뿐
운영 멱등성 저장소로 간주하지 않는다.

## 4. Human-gated state transitions

```text
IDLE -> RECOMMENDED -> APPROVAL_PENDING
APPROVAL_PENDING -> HUMAN_APPROVED -> DRY_RUN_COMPLETED
APPROVAL_PENDING -> HUMAN_REJECTED
APPROVAL_PENDING -> ON_HOLD
```

- `HUMAN_APPROVED`, `HUMAN_REJECTED`, `ON_HOLD`에는 식별 가능한 Human actor가 필요하다.
- Phase 1에는 자동 `EXECUTED` 상태가 없다.
- 실제 외부 실행, 병합, 배포는 별도의 Human 승인 범위에서만 수행한다.

## 5. 검증 조건

- [x] Luna 자체 정책·Spirit Score 계산 제거
- [x] Human 승인 없는 완료 경로 제거
- [x] `correlation_id`와 `idempotency_key` 분리
- [x] 미확정 endpoint·timeout·retry·오류값을 TBD 처리
- [x] Python 테스트 수집 및 실행
- [ ] 실제 Matching v0.4 API·모델과 계약 대조
- [ ] CI 실행 증빙
- [ ] PR #3 audit chain 실제 연동 검증

모든 미확정 항목과 CI 증빙이 확인될 때까지 PR #7은 Draft로 유지한다.
