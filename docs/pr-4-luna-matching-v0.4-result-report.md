# PR #4 결과보고서 — Luna Matching v0.4

- 작업 브랜치: `agent/luna-matching-v0.4`
- 기준 브랜치: `main`
- 정책 버전: `luna-matching-v0.4`
- Domain Pack: `food-desert-v1`
- 상태: 구현 및 로컬·GitHub Actions 검증 완료 / PR 검토 대기

## 1. 결과 요약

Luna가 회원 요청을 접수하고 검증 가능한 정책과 Agent Passport 정보를 사용해
Steward AI 또는 감독 가능한 jr.Agent를 추천하도록 구현했다. 모든 추천은
`recommendation_only`이며, 실제 연결·위임·외부 실행은 Human 결정 및 후속 절차
없이 수행되지 않는다.

## 2. 구현 범위

### 정책과 추천

- Food Desert 요청 유형별 필수 역량·권한·위험도·감독 수준 정의
- Domain Pack과 매칭 정책 버전 고정
- 동일 입력에서 점수와 agent ID를 기준으로 결정론적 순위 생성
- 검증된 역량·권한·Spirit Score·감독 상태를 후보별 근거로 저장
- 부적격 후보도 제외 사유와 함께 기록

### 안전 게이트

- Spirit Score `< 0.4` 제외, 경계값 `0.4` 허용
- 필수 권한과 AP2 Mandate 요청 권한을 모두 충족하지 못하면 제외
- 요청 위험도가 정책 허용 범위를 넘으면 제외
- jr.Agent는 정책상 허용되고 활성 감독자가 있을 때만 추천
- Human 승인 직전에 후보 활성 상태·Spirit Score·감독자 상태 재검증
- 동일 추천에 두 번째 Human 결정을 `409 Conflict`로 차단

### 데이터와 감사

- 추천 정책 스냅샷 저장
- 후보 순위·점수·근거·제외 사유 저장
- 승인·거절·재배정·보류 결정 이력을 append-only 행으로 저장
- 추천 및 Human 결정 이벤트를 기존 hash-chain 감사로그에 연결
- Alembic `0002_v04` migration과 왕복 검증 추가

## 3. API 변화

- `POST /matching/recommendations`
  - `request_type` 입력 추가
  - `recommendation_id`, `policy_version`, 후보 근거·감독자 참조 반환
  - 기존 `status=recommendation_only`와 `human_approval_required=true` 유지
- `POST /admin/matching/recommendations/{id}/decision`
  - `approve`, `reject`, `reassign`, `hold` 지원
  - `matching:decide` Human 관리자 권한 필요
- 서비스 버전 `0.4.0`

## 4. 검증 결과

- Python compile: 통과
- SQLite 전체 pytest: `31 passed, 5 skipped`
- 신규 검증:
  - 동일 입력의 결정론적 후보 순서
  - 정책·증거 스냅샷 저장
  - Spirit Score 미달 제외
  - 감독자 없는 jr.Agent 제외
  - Human 승인 이력 1건만 생성
  - 반복 결정 `409 Conflict`
  - 결정 감사 이벤트 1건 생성
- 기존 보안·Passport·감사 체인·migration 회귀: 통과
- GitHub Actions run `30490087253`: 성공
- PostgreSQL 전체 pytest: `34 passed, 2 skipped`
- 명시적 동시성·시간대 게이트: `5 passed`
- PostgreSQL migration v0.4 downgrade/upgrade 왕복: 통과

## 5. 유지된 안전 경계

- `dry_run=true`
- `recommendation_only`
- Luna의 실제 업무 실행 금지
- UI·운영 배포 미포함
- 결제·자금 이동·계약 체결 미포함
- 이메일·메신저 등 외부 메시지 전송 미포함
- `main` 직접 변경 및 자동 병합 미수행

## 6. 리뷰 체크포인트

1. Domain Pack의 요청 유형과 권한 정의가 운영 정책과 일치하는가
2. jr.Agent 감독자 요건이 충분한가
3. 승인 직전 재검증 범위가 Agent Passport 정책과 일치하는가
4. PostgreSQL CI와 migration 왕복이 통과하는가
5. 감사로그에 민감 원문 없이 최소 메타데이터만 기록되는가

## 7. 결론

PR #4는 Luna의 접수·검증·추천·Human 결정 흐름을 구현하며, 외부 실행을 열지
않는다. 로컬 SQLite와 GitHub Actions의 PostgreSQL·동시성·migration 검증이
모두 성공해 코드 리뷰 가능한 상태다. 리뷰 차단 항목이 해결된 뒤 병합 여부를
판단한다.
