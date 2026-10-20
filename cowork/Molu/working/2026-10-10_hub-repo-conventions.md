# 허브 레포 성격과 작업 규칙 (모루 정리)

- 대상: wooriapt79/mulberry_ecosystem_AgenticAI
- 작성: 모루·Cowork · 2026-10-10 · 상태: working (re.eul 확인 전)

## 1. 레포 성격

- **Mulberry 생태계 허브.** 연구·도구 레포 5개를 서브모듈로 묶고, 서비스(open-reception, special-reception, inje-lexicon, luna)를 폴더로 둔다.
- **주 작업자: KeBin** (re.eul 확인). 보안·운영·open-reception 계열 작업과 작업지시서가 여기서 돈다.
- 헌법 원칙: 장승배기 헌법 · Human 승인 · `dry_run`/추천 전용. 결제·계약·외부 메시지·배포·main 병합은 대표(re.eul) 별도 승인.
- 멤버마다 각자의 워크벤치 레포(프로젝트)가 따로 있다. 모루 워크벤치 레포는 다음 세션에서 셋팅 예정.

## 2. 작업 흐름 (re.eul 확인 규칙)

1. **요청과 과정은 Issue로 공유한다.**
   - 본문이나 댓글에 `#KeBin` → `kebin-task` 라벨 + 접수 댓글 자동 (kebin-issue-trigger.yml).
   - 새 Issue는 모두 `needs-fama-review`, `Fama` 라벨 + 안내 댓글 자동 (fama-issue-triage-notify.yml).
2. **작업은 별도 브랜치 → 항상 Draft PR.** main 직접 커밋 금지.
3. **병합은 re.eul.** Draft → Ready → 대표 머지 (병합 커밋 방식, "Merge pull request #N").
4. 결과 보고는 Issue 코멘트 또는 `docs/work-result-report-*.md`, 인계는 `cowork/<이름>/handoff/`.

## 3. 관찰한 관례

- PR 66건 모두 Closed, 대부분 merged. 최근 PR은 체크리스트(tasks)를 본문에 둔다.
- 커밋 접두어: `feat(open-reception)`, `fix(mobile)`, `test(...)`, `security:`, `docs(...)` 등 Conventional Commits.
- 작성자는 모두 re.eul 계정. AI 공동 작성자는 `Co-Authored-By` 트레일러로 표기 (기존 44건은 `Claude Sonnet 4.6 <noreply@anthropic.com>`).
- `.mailmap`은 이 레포에 없음 → 모루 이메일 등록 위치 확인 필요 (re.eul 확인 중).
- Windows 작업 트리는 CRLF, 저장소는 LF. 리눅스 쪽 git으로 커밋할 때는 `core.autocrlf=input`으로 맞출 것.

## 4. 모루가 지킬 것

- 이 레포에 손댈 때: Issue 먼저 → 브랜치 → Draft PR → re.eul 머지.
- KeBin 작업 영역(open-reception, security 등)은 건드리지 않고, 필요하면 `#KeBin` Issue로 요청.
- 파일 삭제는 하지 않는다. 필요하면 먼저 re.eul에게 확인.

## 5. 이번에 어긋난 점 (기록)

- 22a9b41: 웹 업로드 때 브랜치 지정 없이 main에 직접 들어감 → 되돌리지 않고 후속 Draft PR #88로 정리, re.eul 머지 완료.
