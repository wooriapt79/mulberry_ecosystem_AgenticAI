# Luna Open Reception v0.2 Security 작업 결과보고서

- 작성일: 2026-07-25 (Asia/Seoul)
- 대상 저장소: `wooriapt79/mulberry_ecosystem_AgenticAI`
- 기준: PR #1 병합 커밋 `6fd2e1b`
- 작업 브랜치: `agent/luna-security-v0.2`
- 문서 상태: Draft PR 검토용
- 수행 주체: Mulberry Project · CSA KeBin

## 1. 목적과 승인 경계

본 작업은 v0.1 Open Reception의 인증·세션·관리자 권한 공백을 보완하는
v0.2 Security 단계다. `main` 자동 병합, 운영 배포, 실제 관리자 발급,
실제 Secret 등록, 결제·계약·외부 메시지 실행은 범위에서 제외했다.
기본 동작은 계속 `dry_run`과 `recommendation_only`다.

## 2. 구현 결과

| 영역 | 구현 |
|---|---|
| 관리자 Bootstrap | 런타임 토큰 검증, 최초 `admin` 1회 생성, 재사용 차단, 감사 이벤트 |
| 인증 방어 | 실패 횟수 기록, 임계치 잠금, 잠금 중 로그인 차단, 성공 시 실패 상태 초기화 |
| 세션 회수 | 현재 로그아웃, 사용자 전체 로그아웃, 관리자 긴급 일괄 회수 |
| 계정 차단 | 권한 있는 Human 관리자의 긴급 비활성화 |
| RBAC | 검토·Kill Switch·세션 회수·계정 차단 권한 분리 |
| 감사 | 실패·잠금·권한 거부·Bootstrap·세션 회수 이벤트 |
| MFA/Secret | 공급자 중립 인터페이스와 운영 연동 경계 |
| Compose | Bootstrap·잠금 정책 환경변수의 필수/기본값 반영 |

## 3. API 변화

- `POST /auth/bootstrap`
- `POST /auth/logout`
- `POST /auth/logout-all`
- `POST /admin/users/{user_id}/revoke`
- `/health` 버전 응답을 `0.2.0`으로 갱신

기존 가입, 로그인, Human Passport, Steward Human 신청·심사, 추천,
Kill Switch API는 호환성을 유지한다.

## 4. 데이터 변화

`users`에 실패 횟수와 잠금 종료 시각을, `sessions`에 회수 시각·행위자·사유를
추가했다. 이 단계는 v0.1의 `create_all` 방식을 유지하므로 기존 PostgreSQL에
자동 컬럼 변경을 적용하지 않는다. 실제 기존 DB 반영은 v0.3의 버전형 migration
완료 전까지 운영에 사용할 수 없다.

## 5. 권한 모델

| 역할 | 권한 |
|---|---|
| `steward_reviewer` | Steward 신청 심사 |
| `safety_operator` | Kill Switch 변경 |
| `security_admin` | 세션 회수, 계정 비활성화 |
| `admin` | 위 권한 전체 |

권한 없는 시도는 HTTP 403으로 거절하고 `authorization.denied` 이벤트를 기록한다.
역할 부여 API와 이중승인은 구현하지 않아 임의 권한 상승 경로를 만들지 않았다.

## 6. 테스트 증거

실행 명령:

```bash
python -m pytest -q
```

결과: `6 passed`.

검증 항목:

- v0.1 회원가입·Passport·Steward 신청·추천 회귀
- Human 관리자 Bootstrap과 Kill Switch
- Bootstrap 재사용 차단
- 단일 세션 및 전체 세션 회수 후 토큰 재사용 차단
- 로그인 3회 실패 후 잠금 및 감사 이벤트
- 일반회원의 관리자 API 접근 차단
- 관리자 긴급 회수·계정 비활성화

추가 정적 검증:

- Python bytecode compile: 통과
- Compose YAML 파싱: 통과
- 환경변수 placeholder 검사: 통과
- 실제 비밀값 패턴 검사: 통과

## 7. 미실행·잔여 위험

- 현재 실행환경에는 Docker CLI가 없어 `docker compose config`, 이미지 build,
  전체 스택 기동 및 PostgreSQL 통합 검증을 실행하지 못했다.
- 로그인 잠금은 계정 단위 방어다. 다중 인스턴스·IP/디바이스 기반의 분산 rate
  limiter는 운영 전 추가해야 한다.
- MFA/Passkey와 Secret Provider는 인터페이스만 있으며 실제 공급자 연결은 없다.
- 실제 기존 DB에는 v0.3 migration 없이 새 컬럼을 적용할 수 없다.
- 관리자 중요 작업의 이중승인과 역할 부여 워크플로는 아직 없다.
- 감사로그 불변성은 v0.3 범위다.

따라서 본 버전은 보안 통제 구현·검토 후보이며 운영 준비 완료 선언이 아니다.

## 8. 운영 전 필수 게이트

1. Docker 가능 환경에서 Compose config/build/up/healthcheck
2. v0.3 migration으로 빈 DB와 기존 DB 모두 검증
3. 분산 rate limiter와 MFA/Passkey 공급자 연결
4. Secret Manager 연동과 Bootstrap 토큰 즉시 회전 절차 검증
5. 이중승인 및 관리자 역할 생애주기 구현
6. 독립 보안 리뷰와 침투 테스트

## 9. 승인 메타데이터

```yaml
approval:
  status: pending
  approved_by: null
  approved_at: null
  report_sha: null
  approved_sha: null
  runtime_sha: null
```

`main` 병합과 운영 배포는 대표자의 별도 승인 없이는 수행하지 않는다.
