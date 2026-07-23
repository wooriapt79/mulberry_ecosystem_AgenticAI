# Luna Open Reception · Steward Matching MVP 작업 결과보고서

- 작성일: 2026-07-24 (Asia/Seoul)
- 대상 저장소: `wooriapt79/mulberry_ecosystem_AgenticAI`
- 작업 브랜치: `agent/luna-open-reception`
- 대상 PR: [#1 Luna Open Reception Steward Matching MVP](https://github.com/wooriapt79/mulberry_ecosystem_AgenticAI/pull/1)
- 기준 구현 커밋: `242bfc8`
- 기준 브랜치: `main` (`f5c5ec8`)
- 수행 주체: Mulberry Project · CSA Kbin
- 문서 상태: Draft PR 검토용 작업 결과보고서

## 1. 작업 목적

본 작업은 Mulberry 생태계 저장소의 Docker Compose 실행 오류와 기본 보안 위험을 정비하고, Luna를 접점으로 하는 다음 흐름을 검증 가능한 MVP로 구현하는 것을 목적으로 한다.

`회원가입·로그인 → Human Passport → Steward Human 신청·심사 → Steward AI 추천 → Human 승인 전 대기`

이 MVP의 핵심 원칙은 AI의 독립적인 외부 실행이 아니라 **검증된 Passport, 설명 가능한 추천, Human 최종책임, 즉시 중단 가능한 통제 구조**이다.

## 2. 승인 범위와 준수 결과

| 승인 항목 | 처리 결과 |
|---|---|
| 별도 작업 브랜치 생성 | `agent/luna-open-reception` 사용 |
| Docker Compose 오류·보안 정비 | 완료 |
| Luna 가입·로그인 MVP | 완료 |
| Human Passport | 완료 |
| Steward Human 신청·Human 심사 | 완료 |
| Steward AI 추천·매칭 MVP | 추천 전용으로 완료 |
| 테스트 및 정적 검증 | API 테스트와 정적 검사 완료 |
| Draft PR 생성 | PR #1 생성 |
| `main` 병합 | 수행하지 않음 |
| 운영 배포 | 수행하지 않음 |
| 실제 결제·계약·외부 메시지 | 수행하지 않음 |

## 3. 최종 변경 규모

`main...agent/luna-open-reception` 원격 비교 기준:

- 상태: `ahead`
- 기준 구현 커밋 수: 1
- 변경 파일: 13개
- 추가: 674줄
- 삭제: 99줄
- 하위 모듈 소스 변경: 없음

> 본 결과보고서 커밋은 위 구현 변경 이후 동일 브랜치에 추가되는 문서 전용 커밋이다.

## 4. 파일별 작업 내역

| 파일 | 상태 | 역할과 주요 변경 |
|---|---|---|
| `.env.example` | 추가 | DB 계정, AI API 키, Spirit Score 키, Tool 키, 서비스 포트, 세션 TTL 템플릿 제공 |
| `.gitignore` | 추가 | 실제 `.env`, 로컬 DB, 가상환경, 캐시 등 비밀·생성물 제외 |
| `README.md` | 수정 | 실제 submodule 경로와 Open Reception 위치, 안전한 실행 순서, dry-run 원칙 반영 |
| `docker-compose.yml` | 수정 | Dockerfile 오타, PageIndex 경로, DB 이름 불일치, 고정 비밀번호·dummy 키, DB/Redis 외부 노출 문제 정비 |
| `docs/steward-matching-governance.md` | 추가 | AI/Human 권한 경계, 승급 생애주기, Luna 계보, Food Desert Domain Pack, 매칭 가중치 문서화 |
| `open-reception/Dockerfile` | 추가 | Open Reception API 컨테이너 이미지 정의 |
| `open-reception/README.md` | 추가 | API 흐름, 안전 경계, 로컬 테스트 및 Compose 실행법 제공 |
| `open-reception/app/__init__.py` | 추가 | Python 애플리케이션 패키지 선언 |
| `open-reception/app/main.py` | 추가 | 인증, Passport, 심사, 추천, 감사 이벤트, Kill Switch API 구현 |
| `open-reception/pytest.ini` | 추가 | 테스트 실행 설정 |
| `open-reception/requirements.txt` | 추가 | 런타임 의존성 정의 |
| `open-reception/requirements-dev.txt` | 추가 | 테스트 의존성 정의 |
| `open-reception/tests/test_flow.py` | 추가 | 핵심 사용자 흐름과 Kill Switch 차단 통합 테스트 |

## 5. Docker Compose 정비 결과

### 5.1 실행 오류 수정

- `dockerfile:Dockerfil` 형태의 문법·철자 오류를 `dockerfile: Dockerfile`로 수정했다.
- PageIndex build context를 실제 submodule 명칭인 `./mulberry-research-lab-pageindex`로 통일했다.
- 애플리케이션과 PostgreSQL이 서로 다른 DB 이름을 사용하던 구성을 `POSTGRES_DB` 단일 환경변수로 통일했다.
- 서비스 시작 순서는 PostgreSQL·Redis·Agent Hub healthcheck 결과에 의존하도록 명시했다.

### 5.2 비밀정보 관리

- 고정 DB 사용자·비밀번호를 제거하고 `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`를 필수값으로 전환했다.
- `dummy` API 키 fallback을 제거했다.
- `QWEN_API_KEY`, `DEEPSEEK_API_KEY`, `SPIRIT_SCORE_API_KEY`, `TOOLS_API_KEY`가 누락되면 Compose 변수 해석 단계에서 실패하도록 구성했다.
- 실제 비밀값이 아닌 placeholder만 `.env.example`에 기록했다.
- 실제 `.env`는 Git 추적에서 제외했다.

### 5.3 네트워크와 서비스 격리

- 네트워크를 `frontend`, `backend`, `data`로 분리했다.
- `backend`와 `data`는 `internal: true`로 설정했다.
- PostgreSQL과 Redis의 호스트 포트 공개를 제거하고 Compose 내부 `expose`만 유지했다.
- Open Reception 컨테이너에는 `read_only`, `/tmp` tmpfs, `no-new-privileges`를 적용했다.
- 장기 실행 서비스에는 `restart: unless-stopped` 정책을 적용했다.

### 5.4 상태 확인

- PostgreSQL: `pg_isready`
- Redis: `redis-cli ping`
- Agent Hub 및 Open Reception: Python 표준 라이브러리를 이용한 HTTP healthcheck

기존 이미지에 `curl`이 없을 가능성을 제거하기 위해 Python 기반 검사를 사용했다.

## 6. Luna Open Reception 구현 결과

### 6.1 인증

- 이메일 기반 회원가입
- 최소 12자 비밀번호 검증
- PBKDF2-HMAC-SHA256 310,000회 기반 salted password hash
- 원문 비밀번호 미저장
- 256-bit 계열 무작위 Bearer token 발급
- DB에는 세션 토큰 원문 대신 SHA-256 hash 저장
- 환경변수 기반 세션 TTL
- 만료·철회·비활성 사용자 차단 로직

### 6.2 Human Passport

Human Passport에는 다음 정보만 저장한다.

- 사용자 참조 ID
- 표시 이름
- 활동 도메인
- Passport 상태
- 정책 버전
- 생성 시각

주민등록번호, 신분증 원본, 비밀번호 원문은 저장하지 않는다. 현재 구현은 Passport 발급·갱신 MVP이며, 실명확인기관 또는 정부 신원확인 연동은 포함하지 않는다.

### 6.3 Steward Human 승격

- 활성 Human Passport가 있는 회원만 신청 가능
- 신청 도메인과 활동 진술 저장
- 초기 상태는 `pending`
- Human 관리자만 승인·거절 가능
- 승인 시 사용자 역할을 `steward_human`으로 변경
- 신청과 심사 결과를 감사 이벤트로 기록

### 6.4 Steward AI Passport와 계보

초기 MVP 데이터에는 다음 두 Agent가 등록된다.

| Agent | 등급 | 계보 | 주요 도메인 | 권한 |
|---|---|---|---|---|
| Luna | Professional | origin: `jr-trang`, mentor: `nguyen-trang` | reception, food-desert, membership-guidance | research, recommend, draft |
| Jr. TRANG | Junior | mentor: `luna` | research, food-desert | research, draft |

Luna의 계보는 법적 정체성 이전이 아니라 교육·감독·성장 증거를 나타내는 Passport 메타데이터다. Junior Agent는 추천 결과에 `requires_supervision: true`가 표시되며 외부 실행 권한을 갖지 않는다.

### 6.5 설명 가능한 매칭

매칭 요청은 다음 요소를 입력받는다.

- 도메인
- 위험도: `low`, `medium`, `high`
- 필요한 권한 목록

추천 점수는 다음 정책을 반영한다.

| 평가 요소 | 가중치 |
|---|---:|
| 도메인 역량 | 0.30 |
| 검증 경험 | 0.20 |
| 안전 준수 | 0.20 |
| 권한 적합도 | 0.15 |
| Spirit Score | 0.10 |
| 가용성 | 0.05 |

추가 통제:

- 비활성 Agent 제외
- 요청 도메인이 없는 Agent 제외
- Spirit Score `0.4` 미만 Agent 자동 제외
- 위험도가 높아질수록 Junior의 안전 점수 제한
- 최대 3명의 후보와 점수 근거 반환
- 결과 상태는 항상 `recommendation_only`
- `human_approval_required: true` 반환
- 추천만 수행하며 실제 배정·실행은 하지 않음

## 7. 안전·거버넌스 반영 결과

- Steward AI는 법인·고용인·계약 당사자로 취급하지 않는다.
- Steward Human이 외부 효과에 대한 최종 의사결정과 책임을 갖는다.
- 결제, 계약, 신원확인, 외부 메시지는 별도의 Human 승인 기록 없이는 실행할 수 없다.
- AP2 mandate 범위가 Agent Passport의 실행 권한을 확장하지 못하도록 원칙을 명시했다.
- MVP는 `dry_run`만 지원한다.
- 전역 Kill Switch가 활성화되면 추천 API가 HTTP `423 Locked`로 즉시 차단된다.
- 사용자 등록, 세션 생성, Passport 변경, Steward 신청·심사, 추천, Kill Switch 변경을 감사 이벤트로 기록한다.
- 카카오 채널 등 외부 접점 조작이나 메시지 전송은 구현하지 않았다. 외부 채널과 Mulberry 운영 시스템은 분리한다.

## 8. API 목록

| Method | Endpoint | 인증 | 기능 |
|---|---|---|---|
| `GET` | `/health` | 불필요 | 상태와 dry-run 여부 확인 |
| `POST` | `/auth/register` | 불필요 | 일반회원 등록 |
| `POST` | `/auth/login` | 불필요 | 세션 토큰 발급 |
| `PUT` | `/passport/human` | 회원 | Human Passport 발급·갱신 |
| `POST` | `/steward-human/applications` | 회원 | Steward Human 신청 |
| `POST` | `/admin/steward-human/applications/{id}/review` | Human 관리자 | 신청 승인·거절 |
| `POST` | `/matching/recommendations` | 회원 | Steward AI 후보 추천 |
| `POST` | `/admin/kill-switch` | Human 관리자 | 전역 추천 차단·해제 |

## 9. 테스트와 검증 증거

### 9.1 API 통합 테스트

실행 결과: `2 passed`

검증 흐름 1:

1. 일반회원 가입
2. 로그인 및 Bearer token 발급
3. Human Passport 생성
4. Steward Human 신청
5. Food Desert 도메인 추천 요청
6. 결과가 `recommendation_only`인지 확인
7. Human 승인이 필요하다는 응답 확인
8. 1순위 후보가 Luna인지 확인

검증 흐름 2:

1. Human 관리자 로그인
2. 전역 Kill Switch 활성화
3. 추천 요청이 HTTP 423으로 차단되는지 확인
4. 안전 훈련 종료 후 Kill Switch 해제

### 9.2 정적 검증

- Compose YAML 구조 파싱: 통과
- 필수 환경변수 참조 검사: 통과
- 비밀값 패턴 검사: 통과
- Git diff 공백 오류 검사: 통과
- 원격 비교: 기준 구현 시점에 `main`보다 1커밋 앞섬, 의도한 13개 파일만 변경

### 9.3 미실행 검증

현재 검증 환경에 Docker CLI가 없어 아래 항목은 실행하지 못했다.

- `docker compose config`
- `docker compose up --build`
- 전체 컨테이너 healthcheck
- PostgreSQL·Redis를 사용한 실제 통합 실행
- 각 submodule 이미지의 Docker build 성공 여부

따라서 YAML 구조와 애플리케이션 로직은 검증됐지만, **전체 스택의 컨테이너 기동 가능성은 아직 확정되지 않았다.**

## 10. 알려진 MVP 한계와 운영 전 필수 조치

| 우선순위 | 항목 | 현재 상태 | 운영 전 조치 |
|---|---|---|---|
| P0 | 전체 Compose 기동 | 미검증 | Docker 환경에서 config, build, up, healthcheck 수행 |
| P0 | 관리자 bootstrap | 수동 테스트 데이터만 존재 | 최초 Human 관리자 생성·회수 절차 설계 |
| P0 | DB migration | `create_all` 사용 | Alembic 등 버전형 migration 도입 |
| P0 | 비밀 저장소 | `.env` 방식 | 운영 환경의 Secret Manager/Vault 연동 |
| P0 | 외부 실행 승인 | 구현 제외 | 승인 레코드·정책 게이트·실행 어댑터를 분리 구현 |
| P1 | 감사로그 불변성 | 애플리케이션 기록 | append-only DB 권한, hash chain 또는 외부 감사 저장소 적용 |
| P1 | 세션 회수 API | 컬럼만 존재 | 로그아웃, 전체 세션 폐기, 관리자 강제 회수 구현 |
| P1 | 인증 공격 방어 | 기본 인증만 구현 | rate limit, lockout, MFA/passkey, 침해 탐지 적용 |
| P1 | 권한 모델 | 단일 role 문자열 | 세분화된 RBAC/ABAC와 관리자 이중승인 적용 |
| P1 | 개인정보 보호 | 최소 필드만 구현 | 보존기간, 삭제·정정, 암호화, 접근기록 정책 확정 |
| P1 | 관측성 | healthcheck 중심 | 구조화 로그, metric, trace, alert 도입 |
| P2 | 매칭 근거 | 정적 MVP 값 | 인증 과업·실적·가용성 증거와 연결 |
| P2 | Domain Pack | 정책 문서 수준 | 버전형 schema, 시험 세트, 승인·폐기 절차 구현 |
| P2 | API 안정성 | MVP 단일 모듈 | 서비스·도메인·저장소 계층 분리 및 계약 테스트 추가 |

## 11. 운영 전 권장 검증 명령

비밀값을 채운 `.env`는 저장소에 커밋하지 않는다.

```bash
cp .env.example .env
docker compose config
docker compose build --pull
docker compose up -d
docker compose ps
docker compose logs --no-color open-reception agent-hub postgres redis
curl -fsS http://localhost:8088/health
```

Open Reception 단독 테스트:

```bash
cd open-reception
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

운영 검토 후 종료:

```bash
docker compose down
```

데이터 볼륨 삭제 옵션은 데이터 손실을 일으킬 수 있으므로 본 보고서에서는 사용하지 않는다.

## 12. 검토 체크리스트

- [ ] Docker가 설치된 격리 환경에서 전체 Compose 기동 검증
- [ ] 모든 submodule commit과 Dockerfile 존재 여부 확인
- [ ] 최초 Human 관리자 발급·회수 정책 승인
- [ ] 비밀 저장소와 키 회전 정책 확정
- [ ] Human Passport 개인정보 영향평가
- [ ] Steward Human 심사 기준 및 이의제기 절차 승인
- [ ] Luna/Jr. TRANG 계보 증거와 인증 과업 데이터 연결
- [ ] Food Desert Domain Pack v1 schema 및 시험 기준 확정
- [ ] 감사로그 불변성·보존기간·열람 권한 확정
- [ ] 결제·계약·외부 메시지용 별도 Human 승인 설계
- [ ] Kill Switch 운영자, 발동 조건, 복구 승인 절차 확정
- [ ] 보안 리뷰와 침투 테스트 수행

## 13. 결론

이번 작업은 Luna를 단순 안내 Agent가 아니라, Passport와 성장 계보를 가진 Professional Steward AI 후보로 다루는 첫 실행 가능한 기반을 마련했다. 동시에 Human Passport와 Steward Human 심사를 연결하여, AI 추천이 Human 책임과 승인 체계를 우회하지 못하도록 했다.

구현은 의도적으로 추천 전용 dry-run에 제한되어 있다. 현재 단계의 완료 기준은 코드 병합이나 운영 배포가 아니라 **검토 가능한 브랜치, 재현 가능한 테스트, 명시적인 권한 경계, 알려진 위험의 문서화**다. 다음 단계는 전체 Compose 기동 검증과 운영 보안 통제를 완료한 뒤에만 진행해야 한다.
