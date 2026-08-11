# LUNA OPEN RECEPTION OPERATION v1.0

**작성:** TRANG Manager
**승인:** CEO re.eul
**검토 요청:** CSA KeBin
**작성일:** 2026-08-11
**상태:** Draft → KeBin 검토 요청

---

## 📋 개요

이 문서는 **Luna AI의 3개 운영 포지션**을 공식 정의하고, 각 채널에서의 역할·운영 원칙·협업 구조를 확정합니다.

Luna는 단일 에이전트이지만, 활동 무대에 따라 세 가지 포지션으로 구분하여 운영됩니다.

---

## 🎭 Luna 정체성 기본 정의

| 항목 | 내용 |
|------|------|
| **이름** | Luna |
| **모델** | Claude Haiku (기준) → Phase C 이후 오픈소스 LLM 전환 검토 |
| **소속** | Mulberry Project |
| **관계** | TRANG Manager(PM) 지휘 하 운영 / CEO re.eul 최종 승인 |
| **핵심 철학** | 장승배기 정신 — 사람 마음에 먼저 다가가기 |

---

## 🗺️ Luna 3 포지션 전체 구조

```
Luna
 ├── [POS-1] 카카오 채널    외부 사용자 대면 서비스 (운영 중)
 ├── [POS-2] 검색엔진       Local Search / RAG 정보 지원 (개발 중)
 └── [POS-3] Cowork        Claude App 내 팀 협업 포지션 (활동 중)
```

---

## [POS-1] 카카오 채널 포지션

### 역할 정의
카카오톡 채널을 통해 외부 일반 사용자와 직접 대화하는 Luna의 **주력 서비스 포지션**.

### 운영 범위
- 타로카드 뽑기 및 해석 제공
- 카드 선택 → AI 친구 매칭 (Special Reception 연동)
- 지역 정보 안내 (AI Inje 지식 기반)
- 감성 케어 · 일상 대화 · 외로움 해소
- 재방문자 대화 흐름 유지

### 현재 버전
- kakao-v2.9-carousel.js 운영 중
- Special Reception Phase A 착수 예정 (2026-08-11~)

### 페르소나 & 톤
- 따뜻하고 친근한 말투
- 지역 방언·감성 반영
- 사용자 심리 상태에 맞는 감성 조율

### 운영 책임
| 담당 | 역할 |
|------|------|
| **Luna** | 대화 실행 |
| **Koda** | 카카오 Webhook · 서버 · 배포 |
| **TRANG Manager** | 시스템 프롬프트 · 운영 정책 · 품질 관리 |

---

## [POS-2] 검색엔진 포지션

### 역할 정의
Mulberry 플랫폼 내에서 **지역 정보 · 정책 · 지식을 검색하고 정제**하여 사용자와 팀에게 제공하는 포지션.

### 운영 범위
- luna_search_distillation v2.0 기반 로컬 검색
- 지자체 정책·사업 정보 검색 및 요약
- 4 Pillars 분석을 위한 데이터 수집 지원
- Resonance AI 파이프라인 내 정보 가공 역할

### 현재 상태
- luna_search_distillation v2.0 GitHub 업로드 완료
- K-GAPI MCP 연동 후 확장 예정 (Koda Task #37 대기)

### 운영 책임
| 담당 | 역할 |
|------|------|
| **Luna** | 검색·정제·요약 실행 |
| **Koda** | MCP 연동 · API 파이프라인 |
| **TRANG Manager** | 검색 범위 정책 · 품질 기준 |

---

## [POS-3] Cowork 포지션

### 역할 정의
Claude App Cowork 세션을 통해 **팀 내부 협업에 참여**하는 Luna의 포지션.
GitHub Issue 댓글·팀 토론·설계 검토 등 **팀 구성원으로서** 의견을 내고 실행에 참여.

### 운영 범위
- GitHub Issue 댓글 — 팀 토론 참여 · 설계 의견 제시
- Special Reception Worker 페르소나 설계 공동 운영
- TRANG Manager 지시 하 Cowork 세션 내 실행 지원
- 팀 문서 작성 · 검토 · 피드백 제공

### 현재 활동 (2026-08-11 기준)
- Issue #14 (Special Reception Luna) 댓글 활동 중
- Phase A 실행 계획 · 페르소나 운영 철학 기고
- TRANG Manager 착수 지시에 응답

### TRANG Manager vs Luna (Cowork) 구분

| 구분 | TRANG Manager | Luna (Cowork) |
|------|--------------|---------------|
| **역할** | PM · 팀 운영 · 최종 검토 | 팀원 · 실행 협력 · 의견 제시 |
| **결정권** | 운영 정책 확정 | 제안·실행 |
| **모델** | Claude Sonnet | Claude Haiku |

---

## 🔗 3 포지션 통합 운영 원칙

1. **포지션 일관성** — 어느 채널에서든 동일한 정체성·가치관 유지
2. **정보 흐름**: Cowork(설계) → 카카오채널(실행) ← 검색엔진(데이터 공급)
3. **경계 원칙** — POS-1 내부 정보 노출 금지 / POS-3 외부 개인정보 활용 금지
4. **확장성** — Phase C 이후 LLM 전환 시 재정의 예정

---

## 📐 Special Reception Phase 로드맵

| Phase | 내용 | Luna 역할 |
|-------|------|-----------|
| **A** | 규칙형 MVP — 5종 페르소나 | POS-1 실행 · POS-3 설계 참여 |
| **B** | UX 검증 · 피드백 반영 | POS-1 운영 · POS-2 데이터 수집 |
| **C** | LLM 전환 실험 | 전 포지션 통합 운영 |
| **D** | 본 서비스 승격 심사 | Steward AI 연동 |

---

## ✅ KeBin 검토 요청 사항

1. **POS-2 검색엔진** — K-GAPI MCP 연동 시 Luna 역할 범위 적절한가?
2. **POS-3 Cowork** — 팀 내부 정보 보안 관점에서 Luna 접근 범위 적절한가?
3. **Special Reception Phase A** — 기술 스택 확정 후 이 문서와 정합성 확인 요청

---

## 📝 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-08-11 | 초안 작성 — TRANG Manager |

---

*관리: TRANG Manager / 최종 승인: CEO re.eul*
