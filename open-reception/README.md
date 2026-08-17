# Luna Open Reception

Mulberry의 메인 Reception 서비스입니다. 방문 요청을 접수하고 Human Passport와 검증된 정책을 기반으로 Steward 후보를 추천하되, 실제 배정·위임·외부 실행은 Human 승인 없이는 수행하지 않습니다.

> 현재 기준: **Matching v0.4 병합 완료 + Reception Core v0.1 첫 묶음 Draft**
>
> 운영 원칙: `dry_run=true`, `recommendation_only=true`

## 현재 개발 상태

| 단계 | 상태 | 주요 내용 |
|---|---|---|
| Open Reception MVP | 완료 | 회원가입·로그인·Human Passport·Steward Human 신청 |
| Security v0.2 | 완료 | Bootstrap, 로그인 잠금, 권한 게이트, 세션 폐기 |
| Data & Audit v0.3 | 완료 | Alembic, append-only 이력, SHA-256 감사 체인 |
| Matching v0.4 | 완료 | 정책·증거 기반 후보 추천과 Human 결정 |
| Reception Core v0.1 | Draft | Case 상태, 익명 Visitor, Human Gate, 민감정보 비저장 계약 |
| Web Reception Adapter | 예정 | Case API와 Web 접수 흐름 |
| Kakao Adapter | 제외/후속 | 운영 webhook·메시지 연결은 별도 승인 |
| 운영 배포 | 미승인 | Railway 및 실제 외부 실행 미수행 |

진행 추적:

- 설계 기록: [Issue #12](https://github.com/wooriapt79/mulberry_ecosystem_AgenticAI/issues/12)
- 실행 Issue: [Issue #19](https://github.com/wooriapt79/mulberry_ecosystem_AgenticAI/issues/19)
- 현재 Draft: [PR #20](https://github.com/wooriapt79/mulberry_ecosystem_AgenticAI/pull/20)

## 책임 경계

```text
Web / future Kakao Adapter
        ↓ channel-neutral request
Reception Core
        ↓ recommendation request
Matching v0.4
        ↓ candidates + evidence + exclusions
Human Approval
        ↓ approved decision only
Future Action Gateway
```

- **Channel Adapter:** 채널 입력 검증, 서명·replay·idempotency 담당
- **Reception Core:** Case 접수, 상태 전이, 공개 진행상황과 내부 데이터 분리
- **Matching v0.4:** 정책·점수·권한·감독 판정의 단일 원본
- **Human:** 담당 확정, 위임, 고위험 결정의 최종 권한자
- **Action Gateway:** 현재 비활성. 승인된 후속 범위에서만 검토

Luna는 대화와 접수 흐름을 담당하지만 Matching 정책, 권한, Spirit Score 또는 감독 판정을 별도로 재구현하지 않습니다.

## 기본 사용자 흐름

1. `POST /auth/register`
2. `POST /auth/login`
3. `PUT /passport/human`
4. `POST /steward-human/applications`
5. Human 관리자의 신청 검토
6. `POST /matching/recommendations`
7. 정책 버전·추천 근거·제외 사유 확인
8. Human 관리자의 승인·거절·재배정·보류 결정
9. 외부 실행 없이 감사 이벤트 기록

Reception Core v0.1에서는 익명 Visitor 흐름을 별도로 추가하고 있습니다. Passport의 `user_id`와 Visitor의 `visitor_id`는 같은 identity로 자동 병합하지 않습니다.

## API

### 상태 및 인증

- `GET /health`
- `POST /auth/bootstrap` — 최초 Human 관리자 1회 생성
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `POST /auth/logout-all`
- `POST /admin/users/{user_id}/revoke`

### Passport 및 Steward

- `PUT /passport/human`
- `POST /admin/passports/human/{passport_id}/status`
- `POST /steward-human/applications`
- `POST /admin/steward-human/applications/{application_id}/review`

### Matching·감사·비상 통제

- `POST /matching/recommendations`
- `POST /admin/matching/recommendations/{recommendation_id}/decision`
- `GET /admin/audit/verify`
- `POST /admin/kill-switch`

Reception Core의 Case API는 PR #20 이후 별도 작업 묶음에서 추가합니다. 현재 도메인 계약을 공개 API로 오인하면 안 됩니다.

## Matching v0.4 안전 기준

- Food Desert Domain Pack과 Matching 정책 버전 고정
- 검증된 역량·권한·Spirit Score·감독 상태 기반 결정적 추천
- Spirit Score `< 0.4` 후보 제외
- 필수 권한 또는 위험 기준 미충족 후보 제외
- jr.Agent는 활성 감독자가 있을 때만 추천
- Human 승인 직전 후보 상태 재검증
- 동일 추천에 대한 중복 Human 결정 차단
- 추천·결정 이력을 append-only 감사 체인에 연결

Matching 결과는 후보와 설명일 뿐 실제 고용·계약·위임 또는 업무 실행이 아닙니다.

## Reception Core v0.1

첫 Draft 묶음은 API나 DB보다 먼저 도메인 안전 계약을 고정합니다.

- Case 상태와 허용 전이
- `assigned` 및 `in_progress` 진입 전 Human 승인
- HMAC-SHA256 기반 가명 `visitor_id`
- identity key의 `key_version`
- Passport 사용자와 익명 Visitor 분리
- Case·Matching·Human Decision·Audit용 identity-free correlation ID

최소 상태 모델:

```text
draft
→ submitted
→ triaged
→ assigned
→ in_progress
→ waiting_for_visitor
→ resolved
→ closed
```

예외 상태:

```text
rejected / cancelled / escalated / blocked
```

상세 계약은 [Reception Core v0.1 첫 작업 묶음](../docs/reception-core-v0.1-first-bundle.md)을 참고합니다.

## 데이터 및 개인정보 경계

| 데이터 | 처리 원칙 |
|---|---|
| `visitor_update` | 방문자에게 공개 가능한 내용만 |
| `internal_note` | 권한 있는 담당자의 일반 업무 메모 |
| `conversation_raw` | 첫 v0.1 묶음에서 저장 경로를 열지 않음 |
| `sensitive_context` | nullable 예약 필드, 실제 값 입력·저장 거부 |
| 채널 원본 identity | Case·감사로그·correlation ID에 기록 금지 |
| Passport `user_id` | Visitor ID와 자동 결합 금지 |

다음 값은 일반 필드나 중첩 JSON으로 우회 저장할 수 없습니다.

- ShopMate 민감 맥락
- 감정·심리·성향 추론
- 원 대화
- 채널 원본 식별자
- 사용자 확인 없는 다중 채널 identity

민감정보를 실제로 다루려면 RBAC, 암호화, 동의, 보존·삭제, 감사 정책을 별도 설계하고 Human 승인을 받아야 합니다.

## 고정 금지 사항

현재 버전은 다음을 수행하지 않습니다.

- 결제 또는 자금 이동
- 계약 체결
- 재고·배송 변경
- 운영 Kakao 메시지 송수신
- 외부 자동 메시지
- Human 승인 없는 담당 확정·위임
- 운영 Railway 배포
- 실제 MFA/Passkey 또는 Secret Provider 등록
- 서로 다른 채널 계정 자동 병합
- 민감정보 또는 ShopMate 심리 데이터 저장

Global Kill Switch는 Matching을 즉시 차단하며, Human identity와 책임이 항상 최종 권한을 가집니다.

## 로컬 실행 및 검증

Python 3.12 기준:

```bash
cd open-reception
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

전체 Compose 검증:

```bash
cp .env.example .env
# 모든 placeholder를 로컬 전용 안전 값으로 교체
docker compose config
docker compose up --build
```

실제 비밀값을 저장소에 커밋하지 마십시오. 운영 관리자, 외부 Provider 또는 배포 환경은 이 저장소만으로 생성되지 않습니다.

## 주요 문서

- [Steward Matching Governance](../docs/steward-matching-governance.md)
- [Security v0.2](../docs/security-v0.2.md)
- [Data & Audit v0.3 결과](../docs/work-result-report-data-audit-v0.3-2026-07-25.md)
- [Matching v0.4 결과](../docs/pr-4-luna-matching-v0.4-result-report.md)
- [Reception Core v0.1 첫 작업 묶음](../docs/reception-core-v0.1-first-bundle.md)

## 검토·병합 절차

```text
Execution Issue
→ agent/* 작업 브랜치
→ 코드·테스트·문서
→ Draft PR
→ GitHub Actions
→ KODA 기술 검토
→ TRANG 운영·UX 검토
→ CEO re.eul Human 승인
→ 병합 판단
```

Draft PR 생성이나 CI 통과는 운영 배포 또는 외부 실행 승인을 의미하지 않습니다.
