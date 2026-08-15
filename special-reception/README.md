# Special Reception Luna — Phase A

저장 없는 규칙형 타로 AI 친구 데모입니다. `open-reception`과 계정·Passport·DB·권한을 공유하지 않습니다.

## 고정 경계

- 로그인, 회원가입, 사용자 식별 없음
- DB, 쿠키, 대화 원문 저장 없음
- 외부 AI API, LLM, RAG 호출 없음
- 결제, 계약, 외부 메시지 없음
- 카드·페르소나 매핑과 응답은 결정적 규칙 기반
- 최대 5턴 또는 최초 발급 후 10분
- Railway 배포와 카카오채널 변경은 Human 승인 전 제외

브라우저에는 서명된 최소 세션 토큰만 유지합니다. 토큰에는 카드 코드, 페르소나 코드, 턴, 발급 시각만 들어가며 사용자 메시지는 포함되지 않습니다. 서버 프로세스도 세션이나 대화를 저장하지 않습니다.

## 로컬 실행

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
export SESSION_SIGNING_SECRET="replace-with-at-least-32-random-characters"
uvicorn app.main:app --host 127.0.0.1 --port 8080 --no-access-log
```

`http://127.0.0.1:8080/?card=judgement`에서 카드 파라미터를 시험할 수 있습니다.

## 테스트

```bash
pytest -q
```

## 자동 검증

`Special Reception Phase A` GitHub Actions는 다음을 필수 확인합니다.

- 규칙·API·격리 경계 테스트
- Python 컴파일과 브라우저 JavaScript 문법
- Docker 이미지 빌드
- 읽기 전용·capability 제거 컨테이너의 health/catalog
- DB·외부 AI·외부 HTTP 클라이언트 비연결
- 브라우저 영구 저장소 미사용과 최소 세션 토큰

배포 검토는 [사전 체크리스트](../docs/special-reception-predeployment-checklist.md)를 따릅니다.

## 운영 전 Human 승인 체크

1. KODA: 컨테이너·메모리·health check 검토
2. TRANG Manager: 한국어 톤·안전 문구 검토
3. CEO re.eul: Railway 배포 승인
4. 배포 URL 검증 후에만 카카오채널 링크 변경

`SESSION_SIGNING_SECRET`이 없으면 개발 편의를 위해 프로세스 시작 시 임시 키를 만듭니다. 운영에서는 반드시 별도 비밀값을 주입해야 하며 저장소에 커밋하지 않습니다.
