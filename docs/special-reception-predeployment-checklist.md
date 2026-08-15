# Special Reception Luna — Pre-deployment Checklist

관련 Issue: #14, #15  
관련 구현: PR #17

이 문서는 배포를 승인하지 않습니다. Phase A 병합 코드가 운영 환경 후보로 이동하기 전에 필요한 검토와 Human 승인 증거를 정의합니다.

## 1. 자동 검증

- [ ] `Special Reception Phase A` GitHub Actions의 테스트 작업 통과
- [ ] Python 컴파일 및 브라우저 JavaScript 문법 검사 통과
- [ ] Docker 이미지 빌드 통과
- [ ] 읽기 전용·capability 제거 컨테이너에서 `/health`와 `/api/catalog` 확인
- [ ] DB·외부 AI·외부 HTTP 클라이언트 비연결 회귀 검사 통과
- [ ] 브라우저 영구 저장소와 절대 외부 API URL 미사용 확인
- [ ] 세션 토큰에 카드·페르소나·턴·발급 시각만 포함됨을 확인

## 2. KODA 기술 검토

- [ ] Railway 후보 서비스의 Root Directory를 `special-reception`으로 지정
- [ ] 실제 배포 전용 `SESSION_SIGNING_SECRET`을 Secret Provider에서 생성
- [ ] 비밀값이 GitHub, 로그, 문서, 카카오 URL에 노출되지 않는지 확인
- [ ] 운영 서비스가 `open-reception`, PostgreSQL, Redis 네트워크에 연결되지 않는지 확인
- [ ] CPU·메모리·재시작·휴면 정책과 비용 상한 기록
- [ ] 로그에서 요청 본문·대화 원문·세션 토큰을 수집하지 않는지 확인
- [ ] 롤백 대상을 직전 승인 이미지 또는 서비스 중지로 지정

## 3. TRANG Manager 콘텐츠 검토

- [ ] 5종 페르소나 말투가 단정형 예언·진단으로 오해되지 않는지 확인
- [ ] 고위험·개인정보·의료·법률·투자 안전 문구 확인
- [ ] 35장 현재 목록과 누락 Minor 2장 처리 방침 확정
- [ ] “재미와 자기성찰을 위한 익명 체험” 고지 확인
- [ ] 최대 5턴·10분 종료 흐름 확인

## 4. CEO re.eul Human 승인 게이트

아래는 각각 별도 승인으로 취급합니다.

- [ ] Railway 후보 환경 생성 승인
- [ ] 후보 환경 테스트 URL 발급 승인
- [ ] 카카오 인앱 브라우저 수동 시험 승인
- [ ] 카카오채널 실제 버튼·URL 변경 승인
- [ ] Phase B 사용자 피드백 또는 지표 수집 설계 승인

하나의 승인을 다른 항목의 묵시적 승인으로 해석하지 않습니다.

## 5. 금지 사항

- 승인 전 Railway 운영 배포 및 카카오 UI 변경
- 사용자 식별, 로그인, Passport, DB, 쿠키, 대화 원문 저장
- LLM, RAG, POS-2 검색엔진, 외부 AI API 연결
- 자동 신고·상담 연결·외부 메시지·결제·계약
- `open-reception`의 네트워크·비밀값·데이터베이스 공유

## 6. 승인 기록 형식

승인은 Issue #15에 다음 형식으로 남깁니다.

```text
[Human Approval]
Scope: <승인 항목 하나>
Environment: <후보/운영>
Approved by: CEO re.eul
Date: YYYY-MM-DD
Constraints: <유지할 경계>
```

승인 범위 밖의 작업은 새 Issue 또는 후속 Draft PR에서 다룹니다.
