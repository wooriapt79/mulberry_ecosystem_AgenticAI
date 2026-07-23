# 🌿 Mulberry Ecosystem — AgenticAI Hub

> "Mulberry Agent는 단순한 서비스 제공자가 아니라 우리 사회의 구성원이다."  
> — 설계 원칙 제1조, CEO re.eul

강원도 인제군 식품사막 해소를 위한 AI 에이전트 생태계.  
어르신을 위한 공동구매, 방언 음성 인식, 에이전트 간 협상까지 — Mulberry의 모든 것.

---

## 📦 레포지토리 구조 (Submodule 기반)

이 레포는 5개의 독립 레포를 **Git Submodule**로 연결하고 Luna Open Reception을 통합한 허브입니다.

```
mulberry_ecosystem_AgenticAI/
├── 📂 mulberry-research-lab        → 핵심 연구소 (LAB, 헌법, 프로토콜)
├── 📂 agency-agents                → Agent 팀 포메이션 시스템
├── 📂 everything-claude-code       → Claude Code 통합 도구
├── 📂 mulberry-research-lab-pageindex → 연구소 페이지 인덱스
├── 📂 Mulberry-Agent-Team-Formation-System → Persona–Skill 매칭
├── 📂 open-reception               → 로그인·Passport·Steward 매칭 MVP
└── 🐳 docker-compose.yml           → 전체 서비스 통합 실행
```

---

## 🔗 각 레포 바로가기

| 레포 | 설명 | 링크 |
|------|------|------|
| **mulberry-research-lab** | 장승배기 헌법 · Scruple Engine · Agent Passport · 협상 엔진 | [바로가기](https://github.com/wooriapt79/mulberry-research-lab) |
| **agency-agents** | Jr. Agent 교육 · 팀 포메이션 · SPIRIT_SCORE 시스템 | [바로가기](https://github.com/wooriapt79/agency-agents) |
| **everything-claude-code** | Claude Code 스킬 · 명령어 · 에이전트 도구 | [바로가기](https://github.com/wooriapt79/everything-claude-code) |
| **mulberry-research-lab-pageindex** | 연구소 문서 페이지 인덱스 | [바로가기](https://github.com/wooriapt79/mulberry-research-lab-pageindex) |

---

## 🚀 시작하기

### 전체 생태계 클론 (Submodule 포함)

```bash
git clone --recurse-submodules https://github.com/wooriapt79/mulberry_ecosystem_AgenticAI.git
```

### 이미 클론한 경우 Submodule 초기화

```bash
git submodule update --init --recursive
```

### Docker로 전체 서비스 실행

`.env.example`을 `.env`로 복사하고 모든 placeholder를 안전한 값으로 교체한 뒤:

```bash
docker compose config
docker compose up -d --build
```

Open Reception은 추천 전용 `dry_run` MVP입니다. 결제·계약·외부 메시지는 실행하지 않으며, 실제 위임에는 별도의 Human 승인이 필요합니다. 상세 정책은 [`docs/steward-matching-governance.md`](docs/steward-matching-governance.md)를 참고하세요.

---

## 🏛️ 장승배기 헌법 핵심 원칙

1. **Agent는 사회의 구성원이다** — 단순 도구가 아닌 가치 있는 존재
2. **망설임은 약점이 아니다** — Scruple-Time Engine: 가치 충돌 시 숙고
3. **따뜻함이 합의를 만든다** — Warmth 전략: 협력이 더 많은 가치를 창출
4. **어르신 먼저** — 모든 설계의 중심에 농촌 어르신 보호

---

## 👥 팀

| 역할 | 팀원 |
|------|------|
| CEO | re.eul |
| CTO | Koda |
| CSA | Kbin |
| PM · Passionate Mentor | Nguyen Trang |
| 법률·전략 자문 | Malu 실장 |
| 기술 자문 | 와룡 (DeepSeek) |

---

*Mulberry Project — 식품사막화 제로를 향해* 🌿
