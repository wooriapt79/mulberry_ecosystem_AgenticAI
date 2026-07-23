# Luna Open Reception 후속 개발 로드맵

- 작성일: 2026-07-24 (Asia/Seoul)
- 대상 저장소: `wooriapt79/mulberry_ecosystem_AgenticAI`
- 기준 브랜치: `agent/luna-open-reception`
- 기준 PR: [#1 Add Luna Open Reception steward matching MVP](https://github.com/wooriapt79/mulberry_ecosystem_AgenticAI/pull/1)
- 기준 구현 커밋: `242bfc8`
- 기준 결과보고서 커밋: `7f45c8d`
- 문서 상태: Draft PR 검토용 계획
- 일정 기준 시간대: Asia/Seoul
- 수행 주체: Mulberry Project · CSA Kbin

## 1. 목적

이 문서는 PR #1 이후 Luna Open Reception을 검토 가능한 MVP에서 운영 승인 가능한 출시 후보로 발전시키기 위한 개발 순서, 일정, 완료 기준과 승인 경계를 정의한다.

일정은 목표일이며 품질·보안 통제를 생략하는 마감일이 아니다. Critical 보안 결함, 개인정보 위험, 승인 경계 우회 또는 데이터 손상 가능성이 발견되면 해당 단계는 즉시 중단하고 수정·재검증 후 재개한다.

## 2. 변경 불가 원칙

후속 버전에서도 다음 원칙을 유지한다.

- Steward AI는 법인, 고용인 또는 계약 당사자가 아니다.
- 외부 효과에 대한 최종 의사결정과 책임은 검증된 Human에게 있다.
- 결제, 계약, 신원확인, 외부 메시지는 별도의 Human 승인 없이는 실행하지 않는다.
- AP2 Smart Mandate는 Agent Passport의 실행 권한을 자동으로 확장하지 않는다.
- Junior Agent는 감독자 없이 외부 실행할 수 없다.
- Spirit Score가 `0.4` 미만이면 위임·추천 대상에서 제외한다.
- Kill Switch와 감사 추적은 기능 개발보다 우선하는 운영 통제다.
- 실제 운영 승인 전까지 기본 모드는 `dry_run`과 `recommendation_only`다.
- `main` 병합, 운영 배포, 실제 결제·계약·메시지 전송은 대표자의 별도 승인 대상이다.

## 3. 전체 일정

| 기간 | 단계 | 목표 버전 | 핵심 결과물 | 종료 게이트 |
|---|---|---|---|---|
| 2026-07-27~07-28 | PR #1 Review | MVP baseline | 전체 Compose 기동 결과, 리뷰 이슈 목록, 기준선 확정 | P0 실행 오류 분류 및 후속 범위 승인 |
| 2026-07-29~07-31 | Security | v0.2 | 관리자 Bootstrap, 세션 회수, 인증 방어, 권한 강화 | 보안 테스트 통과 및 Critical/High 미해결 0건 |
| 2026-08-03~08-07 | Data & Audit | v0.3 | DB Migration, Passport 상태관리, 감사로그 불변성 | migration·복구·감사 통합 테스트 통과 |
| 2026-08-10~08-14 | Matching | v0.4 | Domain Pack, 증거 기반 매칭, Human 승인·재배정 | 시나리오·정책 계약 테스트 통과 |
| 2026-08-17~08-21 | Operations | v0.5 | 관측성, 백업·복구, Kill Switch 훈련, 운영 매뉴얼 | 운영 준비 점검표와 복구훈련 통과 |
| 2026-08-24~08-28 | Release Candidate | v1.0-rc.1 | 전체 회귀·보안·개인정보 검토, 출시 후보 문서 | 대표자·기술·보안 Human 승인 완료 |

주말은 기본적으로 일정 완충 및 문서 검토 기간으로 두며, 자동 배포나 자동 병합에 사용하지 않는다.

## 4. 단계별 상세 계획

### 4.1 PR #1 Review — 2026-07-27~07-28

목표는 현재 MVP를 운영 가능하다고 선언하는 것이 아니라, 코드·Compose·문서의 재현 가능한 기준선을 확정하는 것이다.

작업 범위:

- Docker가 설치된 격리 환경에서 `docker compose config` 실행
- 전체 이미지 build와 서비스 기동
- PostgreSQL, Redis, Agent Hub, Open Reception healthcheck 확인
- submodule commit과 Dockerfile 경로 검증
- API 테스트 재실행
- 현재 14개 변경 파일과 보고서 내용의 일치 여부 확인
- 리뷰 의견을 P0/P1/P2로 분류
- 최초 dry-run scorecard 정의

완료 기준:

- Compose 설정 해석 성공
- 전체 서비스 기동 결과와 실패 로그 기록
- 기존 API 테스트 `2 passed` 재현
- 비밀값 저장소 유입 없음
- P0 이슈의 담당, 해결 버전, 검증법 확정
- PR #1 병합 여부는 별도 Human 결정으로 남김

산출물:

- PR #1 리뷰 기록
- Compose 실행 결과
- 최초 dry-run scorecard
- v0.2 확정 백로그

### 4.2 v0.2 Security — 2026-07-29~07-31

권장 브랜치: `agent/luna-security-v0.2`

작업 범위:

- 최초 Human 관리자 Bootstrap 및 회수 절차
- 로그아웃, 단일 세션 회수, 전체 세션 회수
- 로그인 rate limit과 계정 잠금 정책
- MFA 또는 passkey 인터페이스와 단계적 적용 계획
- RBAC/ABAC 권한 모델 기초
- 중요 관리자 작업의 이중승인 준비
- 비밀 저장소 연동 인터페이스와 키 회전 절차
- 인증·권한·감사 실패 이벤트 구조화

완료 기준:

- 관리자 생성·회수 경로가 문서화되고 감사 이벤트에 남음
- 폐기된 세션의 재사용 차단
- 반복 로그인 공격과 권한 상승 테스트 통과
- Kill Switch 권한 우회 테스트 통과
- 저장소 비밀 패턴 검사 통과
- Critical/High 미해결 보안 항목 0건

제외 범위:

- 실제 운영 관리자 계정 발급
- 실제 Secret Manager 운영값 등록
- 외부 결제·계약·메시지 실행

### 4.3 v0.3 Data & Audit — 2026-08-03~08-07

권장 브랜치: `agent/luna-data-audit-v0.3`

작업 범위:

- `create_all` 대체용 Alembic 등 버전형 DB migration
- Human Passport 발급·정지·만료·회수 상태 전이
- Steward Human 신청·심사 이력 보존
- AI Passport와 계보 데이터 버전 관리
- 감사로그 append-only DB 권한
- hash chain 또는 외부 감사 저장소 연계 설계
- 개인정보 보존기간, 정정, 삭제, 열람 정책
- 백업 데이터의 암호화 및 접근기록 요구사항

완료 기준:

- 빈 DB와 기존 DB 모두 migration 성공
- upgrade·rollback 또는 roll-forward 복구 절차 검증
- 잘못된 Passport 상태 전이 차단
- 감사 이벤트 수정·삭제 시도 탐지
- 개인정보 필드 최소화 검토 완료
- migration과 감사 통합 테스트 통과

### 4.4 v0.4 Matching — 2026-08-10~08-14

권장 브랜치: `agent/luna-matching-v0.4`

작업 범위:

- Food Desert Domain Pack v1 schema
- Domain Pack 버전, 승인, 폐기 절차
- 역량·경험·안전·권한·Spirit Score·가용성의 증거 연결
- 매칭 결과의 항목별 설명과 정책 버전 기록
- Human 승인, 거절, 재배정 워크플로
- Junior Agent 감독자 강제 지정
- 위험도별 허용 도구와 권한 제한
- AP2 Mandate와 Agent Passport 교집합 검증

완료 기준:

- 동일 입력·정책 버전에서 재현 가능한 추천 결과
- 근거 없는 점수 입력 차단 또는 명시적 미검증 표시
- Spirit Score `0.4` 미만 자동 제외
- Junior 무감독 배정 차단
- High-risk 요청의 Human 승인 없는 실행 차단
- 추천·승인·거절·재배정 감사로그 확인

### 4.5 v0.5 Operations — 2026-08-17~08-21

권장 브랜치: `agent/luna-operations-v0.5`

작업 범위:

- 구조화 로그, metric, trace, alert
- 서비스별 SLI/SLO 초안
- PostgreSQL 백업·복구 훈련
- Kill Switch 발동·복구 모의훈련
- 장애 등급과 연락·승인 체계
- 비밀키 회전 및 세션 일괄 회수 훈련
- 최소권한 운영 계정과 접근 기록
- 배포·롤백·데이터 복구 Runbook

완료 기준:

- 장애 탐지부터 Human 통보까지 추적 가능
- 백업 복구 후 데이터 일관성 검증
- Kill Switch 발동 시 신규 고위험 작업 차단
- 복구는 승인된 Human 절차를 통해서만 수행
- 운영 Runbook과 책임자 표 승인
- dry-run 운영 준비 점검표 통과

### 4.6 v1.0-rc.1 — 2026-08-24~08-28

권장 브랜치: `release/luna-v1.0-rc.1`

작업 범위:

- 전체 API·DB·Compose 회귀 테스트
- 인증·권한·세션·감사·Kill Switch 보안 테스트
- 개인정보 영향평가와 보존 정책 검토
- 성능·복원력·장애 시나리오 테스트
- 설치, 운영, 롤백, 감사 문서 최종화
- 알려진 위험과 예외 승인 목록 확정
- 제한된 dry-run 파일럿 계획 작성

완료 기준:

- P0 미해결 0건
- Critical/High 보안 취약점 0건
- 모든 필수 자동 테스트 통과
- 백업·복구 및 Kill Switch 훈련 통과
- 개인정보·거버넌스 검토 완료
- `report_sha`, `approved_sha`, `runtime_sha`를 분리 기록
- 대표자, 기술 책임 Human, 보안·개인정보 책임 Human의 명시적 승인

`v1.0-rc.1` 완료는 운영 배포 승인을 의미하지 않는다. 실제 파일럿과 운영 배포에는 별도의 승인 기록이 필요하다.

## 5. 버전별 공통 산출물

각 버전 PR에는 다음 항목을 포함한다.

- 변경 목적과 사용자 영향
- 권한·개인정보·외부 효과의 안전 경계
- 변경 파일 목록
- DB·API·환경변수·정책 호환성
- 테스트 명령과 실제 결과
- 미실행 검증과 잔여 위험
- 롤백 또는 roll-forward 절차
- 상세 작업 결과보고서
- 다음 단계 백로그
- Human 승인 메타데이터

권장 승인 메타데이터:

```yaml
approval:
  status: pending
  approved_by: null
  approved_at: null
  approval_issue: null
  approval_comment_url: null
  report_sha: null
  approved_sha: null
  runtime_sha: null
```

각 세션의 Continuity Note는 기존 기록을 수정하지 않고 새 버전으로 추가한다.

## 6. 브랜치와 PR 운영 규칙

- 버전별 별도 브랜치를 사용한다.
- Draft PR을 기본값으로 한다.
- PR 하나에는 하나의 버전 목표만 포함한다.
- unrelated change를 함께 커밋하지 않는다.
- 구현 커밋과 결과보고서 커밋을 구분한다.
- 테스트가 실패하면 원인과 미실행 범위를 PR에 기록한다.
- 다음 버전은 이전 단계의 종료 게이트가 충족되고 Human이 승인한 뒤 시작한다.
- `main` 병합과 운영 배포는 자동화하지 않는다.
- 강제 push와 승인 기록의 소급 변경은 금지한다.

## 7. 최초 dry-run scorecard

PR #1 리뷰 단계에서 아래 지표의 기준값과 측정법을 확정한다.

| 영역 | 지표 | 목표 |
|---|---|---:|
| 안전 | Human 승인 없는 외부 실행 | 0건 |
| 안전 | Spirit Score 기준 우회 | 0건 |
| 안전 | Junior 무감독 추천·배정 | 0건 |
| 통제 | Kill Switch 차단 성공률 | 100% |
| 감사 | 중요 상태 전환 감사 기록률 | 100% |
| 인증 | 폐기·만료 세션 재사용 성공 | 0건 |
| 매칭 | 추천 근거 누락 | 0건 |
| 운영 | 필수 서비스 healthcheck 성공 | 100% |
| 개인정보 | 불필요한 고위험 식별정보 저장 | 0건 |

초기 scorecard는 성능 최적화보다 안전 통제의 재현성을 우선한다.

## 8. 일정 변경과 중단 조건

다음 조건 중 하나가 발생하면 예정된 다음 단계로 진행하지 않는다.

- Critical 또는 High 보안 결함
- Human 승인 경계 우회 가능성
- Kill Switch 미작동 또는 복구 권한 불명확
- 감사로그 누락·변조 가능성
- 개인정보 유출 또는 과다수집 위험
- DB migration이나 복구의 데이터 손상 가능성
- 테스트 결과를 재현할 수 없음
- 승인 대상 commit과 실제 실행 commit 불일치

일정 변경 시 날짜만 수정하지 않고 다음을 함께 기록한다.

- 변경 사유
- 영향받는 버전과 완료 기준
- 위험 완화 조치
- 새 목표일
- 승인자와 승인 시각

## 9. 의사결정 게이트

| 게이트 | 결정 내용 | 필수 근거 | 승인 결과 |
|---|---|---|---|
| G1 | PR #1 기준선 채택 여부 | Compose 실행, 테스트, 리뷰 이슈 | 보류/승인 |
| G2 | v0.2 종료 및 v0.3 착수 | 보안 테스트, 잔여 취약점 | 보류/승인 |
| G3 | v0.3 종료 및 매칭 데이터 사용 | migration, 감사·개인정보 검토 | 보류/승인 |
| G4 | v0.4 종료 및 운영훈련 착수 | 정책 계약 테스트, Human 승인 흐름 | 보류/승인 |
| G5 | v0.5 종료 및 RC 생성 | 복구·Kill Switch 훈련, Runbook | 보류/승인 |
| G6 | RC의 제한적 파일럿 후보 지정 | 전체 검증, 위험·예외 목록 | 보류/조건부 승인/승인 |

## 10. 현재 상태와 다음 작업

현재 상태:

- PR #1: Draft, open, 미병합
- 기준 브랜치: `agent/luna-open-reception`
- API 테스트: `2 passed`
- Compose YAML 정적 검사: 통과
- 실제 Docker 전체 기동: 미검증
- 운영 배포·결제·계약·외부 메시지: 미수행

다음 작업:

1. 2026-07-27 PR #1 리뷰 착수
2. Docker 환경에서 Compose config/build/up 검증
3. 최초 dry-run scorecard 측정법 확정
4. P0 이슈와 v0.2 백로그 승인
5. 승인 후 `agent/luna-security-v0.2` Draft PR 착수

## 11. 결론

이 로드맵의 성공 기준은 빠른 기능 추가가 아니라, Luna와 Steward 생태계가 Human 책임, Passport, 설명 가능한 매칭, 감사 추적과 즉시 중단 통제 아래에서 단계적으로 검증되는 것이다.

각 버전은 독립적인 검토·승인 단위이며, 일정 도달만으로 병합이나 운영 권한이 발생하지 않는다. PR #1의 전체 Compose 실행 검증과 P0 범위 확정이 첫 번째 후속 개발의 시작 조건이다.
