# PR #4 작업계획 — Luna Matching v0.4

- 상태: 구현 완료 / PR 검토 대기
- 기준 브랜치: `main`
- 작업 브랜치: `agent/luna-matching-v0.4`
- 기준 커밋: `ebbb05d` (PR #3 병합)
- 예정 PR 제목: `feat(open-reception): add evidence-based steward matching v0.4`

## 1. 작업 목적

Luna Matching v0.4는 회원의 요청을 접수한 뒤 회원 등급, 요청 특성, 위험도, Spirit Score, Agent Passport 권한 및 검증 가능한 역량 증거를 바탕으로 적합한 **Steward AI** 또는 감독 가능한 **jr.Agent(Steward)**를 추천하고 Human 승인 절차를 거쳐 연결하는 기능이다.

Luna는 이 단계에서 업무를 직접 실행하지 않는다.

> 회원 요청 접수 → 자격·권한·위험도 검증 → Steward 후보 추천 → Human 승인·거절·재배정 → 연결 이력 보존

## 2. 이번 블록의 범위

### 포함

1. **Food Desert Domain Pack v1**
   - 요청 유형과 필요한 역량 정의
   - 위험도 및 감독 수준 정의
   - 정책 버전 식별자 포함

2. **증거 기반 Steward 후보 구성**
   - 역량, 경험, 안전 조건, 권한, 가용성을 근거와 연결
   - 근거가 없는 값은 점수에 사용하지 않거나 `unverified`로 표시
   - 항목별 추천 근거를 저장

3. **회원 등급·요청 조건별 연결**
   - 일반·저위험 요청: jr.Agent 후보 추천 가능
   - 전문 요청: Steward AI 우선 추천
   - 고위험·민감 요청: Senior Steward 또는 Human 승인 필수
   - 추가 자료가 필요한 요청: 연결 보류

4. **안전 및 권한 게이트**
   - Spirit Score `< 0.4` 후보 자동 제외
   - jr.Agent의 감독자 없는 독립 배정 차단
   - AP2 Mandate와 Agent Passport 권한의 교집합 검증
   - 권한 범위를 벗어난 후보 추천 차단

5. **Human 워크플로**
   - 추천 승인
   - 추천 거절
   - 재배정
   - 보류 및 추가 자료 요청

6. **감사 추적**
   - 추천 정책 버전
   - 후보별 근거와 제외 사유
   - 승인·거절·재배정 이력
   - append-only 감사로그

7. **회귀 검증**
   - SQLite 및 PostgreSQL
   - 결정론적 추천
   - 권한·안전 게이트
   - Human 승인 상태 전이
   - 동시 요청과 감사 이력 일관성

### 제외

- UI 및 대시보드
- 실제 외부 업무 실행
- 결제와 자금 이동
- 계약 체결
- 이메일·메신저 등 외부 메시지 전송
- 운영 배포
- `dry_run`, `recommendation_only` 경계 해제

## 3. 핵심 역할

| 주체 | 책임 |
|---|---|
| 회원 | 요청 제출, 필요한 자료 제공, 최종 위임 동의 |
| Luna | 접수, 자격·권한·위험도 검증, 후보 추천, 연결 조정 |
| Steward AI | 검증된 전문성과 권한 범위 안에서 후보로 추천 |
| jr.Agent(Steward) | 저위험 요청에 한해 감독자와 함께 후보로 추천 |
| Human Steward/관리자 | 승인, 거절, 재배정, 고위험 요청 판단 |
| 감사 계층 | 추천 근거와 모든 상태 전이를 append-only로 기록 |

## 4. 상태 흐름

| 상태 | 의미 | 허용되는 다음 상태 |
|---|---|---|
| `received` | 회원 요청 접수 완료 | `validating` |
| `validating` | 등급·권한·위험도·자료 검증 중 | `needs_evidence`, `recommended`, `blocked` |
| `needs_evidence` | 근거 또는 자료 부족 | `validating`, `cancelled` |
| `recommended` | 정책에 따른 후보 추천 생성 | `approved`, `rejected`, `reassignment_requested` |
| `approved` | Human 승인 완료 | `connected` |
| `rejected` | 추천 거절 | `validating`, `cancelled` |
| `reassignment_requested` | 다른 후보 요청 | `validating`, `recommended` |
| `connected` | 승인된 Steward와 연결 확정 | 종료 |
| `blocked` | 정책·권한·안전 조건 위반 | Human 검토 또는 종료 |
| `cancelled` | 요청 철회 또는 종료 | 종료 |

`connected`는 연결 확정만 의미하며 실제 업무 실행 권한을 부여하지 않는다.

## 5. 결정 규칙

### 5.1 후보 제외

다음 조건 중 하나라도 충족하면 자동 추천 대상에서 제외한다.

- Spirit Score `< 0.4`
- 필요한 Agent Passport 권한 없음
- AP2 Mandate 범위와 Passport 권한의 교집합 없음
- 필수 역량 증거 없음
- 가용성 없음
- jr.Agent에게 필요한 감독자 없음
- 요청 위험도가 후보의 허용 범위를 초과함

### 5.2 후보 순위

후보 순위는 버전이 명시된 정책과 검증된 입력만 사용해 계산한다.

- 같은 입력과 같은 정책 버전은 같은 결과를 생성해야 한다.
- 동점 처리 규칙은 명시적이고 결정론적이어야 한다.
- 총점뿐 아니라 항목별 근거를 저장해야 한다.
- 검증되지 않은 추론을 사실 또는 점수 근거로 사용하지 않는다.

### 5.3 Human 승인

- 고위험·민감 요청은 Human 승인 전 `connected`로 전이할 수 없다.
- jr.Agent는 감독자 식별자 없이 승인할 수 없다.
- 승인자는 추천 당시의 정책·근거·권한 스냅샷을 확인할 수 있어야 한다.
- 승인과 재배정은 현재 상태를 재검증한 뒤 원자적으로 기록한다.

## 6. 데이터 및 감사 계약

최소 기록 항목:

- 요청 ID와 회원 등급
- 요청 유형과 위험도
- Domain Pack 버전
- 매칭 정책 버전
- AP2 Mandate 참조
- 후보 Agent Passport 참조
- 후보별 검증된 증거
- 제외 사유
- 추천 순위와 항목별 근거
- 감독자 참조(jr.Agent인 경우)
- Human 결정 및 결정자
- 상태 전이 시간
- 감사 이벤트 sequence/hash

민감 원문은 감사 이벤트에 직접 복제하지 않고 필요한 참조와 최소 메타데이터만 보존한다.

## 7. 구현 순서

1. Domain Pack 및 정책 스키마 정의
2. 요청·후보·추천·결정 모델과 migration 추가
3. 권한·Spirit Score·감독자 안전 게이트 구현
4. 결정론적 후보 평가와 근거 생성
5. Human 승인·거절·재배정 상태 전이 구현
6. 기존 감사 체인에 추천 및 결정 이벤트 연결
7. SQLite 회귀 테스트
8. PostgreSQL·동시성·migration 왕복 CI 검증
9. 작업 결과보고서와 PR 설명 갱신
10. 리뷰 차단 항목 해결 후 병합 판단

## 8. 테스트 계약

### 필수 기능 테스트

- 일반·저위험 요청에서 감독 가능한 jr.Agent 추천
- 전문 요청에서 증거가 있는 Steward AI 추천
- Spirit Score `0.4` 경계값 허용 및 `0.4` 미만 제외
- 권한 교집합이 없는 후보 제외
- 근거 부족 후보의 `unverified` 또는 제외 처리
- 고위험 요청의 승인 전 연결 차단
- 승인·거절·재배정 정상 흐름
- 동일 입력·정책 버전의 동일 추천 결과

### 필수 무결성·동시성 테스트

- 동일 요청에 대한 동시 승인 중 하나만 성공
- 승인 직전 후보 권한·상태 변경 시 재검증 후 차단
- jr.Agent 감독자 비활성화 시 승인 차단
- 추천과 Human 결정의 감사 이벤트 순서 보존
- 감사 chain head와 마지막 이벤트 일치
- migration upgrade/downgrade/upgrade 왕복
- SQLite와 PostgreSQL에서 정책 결과 일치

## 9. 완료 기준

- 모든 추천에 정책 버전과 검증 가능한 근거가 존재한다.
- 같은 입력과 정책 버전에서 결과가 재현된다.
- Spirit Score, 권한, 위험도, 감독 규칙을 우회할 수 없다.
- 고위험 요청은 Human 승인 전 연결되지 않는다.
- 승인·거절·재배정 이력이 append-only로 보존된다.
- SQLite 및 PostgreSQL 전체 회귀와 migration 검증이 통과한다.
- 기존 Open Reception의 `dry_run` 및 `recommendation_only` 경계를 유지한다.
- UI·외부 실행·결제·계약·메시지 전송을 포함하지 않는다.

## 10. 리뷰 체크포인트

각 구현 블록은 다음 순서로 빠르게 검토한다.

1. 스키마와 migration
2. 정책 및 결정론적 매칭
3. 안전·권한 게이트
4. Human 상태 전이
5. 감사 이력과 동시성
6. SQLite/PostgreSQL 검증 결과
7. 범위 제외 항목 유지 여부

이 문서는 PR #4의 독립 실행계획과 검수 기준이다. 전체 프로젝트의 장기 로드맵은 기존 로드맵 문서를 기준으로 하며, 본 문서는 Luna Matching v0.4 블록의 구현과 리뷰에만 사용한다.

## 11. 구현 결과

- Domain Pack 및 버전 고정: 완료
- 추천·후보·Human 결정 모델과 migration: 완료
- Spirit Score·권한·감독자 안전 게이트: 완료
- 결정론적 후보 평가와 항목별 근거 저장: 완료
- Human 승인·거절·재배정·보류 상태 전이: 완료
- 추천·결정 감사 체인 연결: 완료
- SQLite 전체 회귀: `31 passed, 5 skipped`
- PostgreSQL 검증: PR CI에서 확인

구현 상세와 검증 근거는 `docs/pr-4-luna-matching-v0.4-result-report.md`를 기준으로 한다.
