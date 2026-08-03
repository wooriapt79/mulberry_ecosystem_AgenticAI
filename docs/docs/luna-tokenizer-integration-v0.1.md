# Luna Open Reception ↔ AI Inje Tokenizer 연결 설계

- 작성일: 2026-08-03 (Asia/Seoul)
- 작성: SIL 이음 (Systems Integrity Lead)
- 대상 저장소: `wooriapt79/mulberry_ecosystem_AgenticAI`, `wooriapt79/mulberry-research-lab`
- 관련 문서: `steward-matching-governance.md`, `development-roadmap.md`, `pr-4-luna-matching-v0.4-result-report.md`
- 관련 외부 문서: AI Inje Tokenizer 개발 기획서 v1.0 (Wayong), 인제군 특화 토크나이저 개발 방법론 v0.1 (SIL 이음)
- 문서 상태: 설계 초안 — 검토 및 승인 대기

---

## 1. 배경과 문제

Luna Open Reception의 첫 Domain Pack은 `food-desert-v1`이다.
AI Inje Initiative의 첫 실증 파일럿도 식품사막 해소다.

**같은 도메인인데 두 프로젝트가 서로를 참조하지 않는다.**

| | Luna Open Reception | AI Inje Tokenizer |
|---|---|---|
| 도메인 | `food-desert-v1` | 식품사막 (브리프 09장) |
| 진행 | v0.4 완료, PR 검토 대기 | Phase 2 진행 중 |
| 산출물 | 접수·매칭·Human 승인 흐름 | vocab, 어휘 사전 |
| 상호 참조 | 없음 | 없음 |

이 문서는 두 프로젝트를 연결하는 세 개의 지점을 정의한다.

---

## 2. 선행 확인 — Luna는 자연어를 저장하지 않는다

초앉 횕전에 반드시 짚어야 할 사실이다.

현재 `MatchRequest` 모델은 전부 구조화 필드다.

```python
class MatchRequest(Base):
    __tablename__ = "matching_requests"
    requester_id: str
    domain: str                    # "food-desert"
    risk: str                      # low | medium | high
    required_permissions: list     # ["research"]
    status: str                    # "recommendation_only"
    approved_by: str | None
```

`MatchInput`도 마찬가지로 `domain`, `request_type`, `risk`, `required_permissions`만 받는다.
**주민의 실제 발화는 시스템 어디에도 저장되지 않는다.**

이는 결함이 아니라 의도된 설계다. v0.4 결과보고서의 리뷰 체크포인트 5번이 이를 명시한다.

> 감사로그에 민감 원문 없이 최소 메타데이터만 기록되는가

### 이 사실이 설계에 미치는 영향

- 기존 로그를 코퍼스로 재활용하는 접근은 **불가능하다** (데이터가 없다)
- 감사로그에 원문을 추가하는 접근은 **금지된다** (설계 원칙 위반)
- 따라서 연결은 **별도의 동의 기반 채널**을 신설하는 방식이어야 한다

---

## 3. 연결 지점 A — Domain Pack → 토크나이저 L4 시드 어휘

**즉시 실행 가능. 개인정보 위험 없음. 신규 개발 불필요.**

### 근거

`app/matching_policy.py`의 `FOOD_DESERT_DOMAIN_PACK`은 이미 이 도메인의 정규 용어 체계를 담고 있다.

```
domain              : food-desert
request_type        : food_access_research
                      membership_guidance
                      joint_purchase_draft
required_competencies : food-desert, research,
                        membership-guidance, joint-purchase
required_permissions  : research, recommend, draft
maximum_risk          : low, medium, high
supervision_level     : standard, steward, human
```

이것은 임의로 만든 목록이 아니라 **거버넌스 승인을 거친 도메인 개념 체계**다.

### 무엇을 얻는가

토크나이저 방법론 v0.1의 L4(도메인 어휘) 레이어는 지금까지 "식품사막·공동구매 관련 용어"라는
막연한 정의만 있었다. Domain Pack을 시드로 쓰면 L4*�� **추측이 아니라 거버넌스 모델에서 파생된다.**

### 매핑 방식

각 정규 개념에 대해, 주민이 실제로 사용하는 한국어 표현을 수집해 매핑한다.

```
[정규 개념]              [주민 표현 후보]              [출처]
joint_purchase_draft  →  공동구매 관련 실제 표현들   →  현장 수집
membership_guidance   →  가입·이용 안내 관련 표현     →  현장 수집
food_access_research  →  식품 구하기 관련 표현        →  현장 수집
```

주의: 위 우변은 **비워둔 채로 시작한다.** 인제 주민이 실제로 무슨 말을 쓰는지는
현장에서 확인해야 하며, 책상에서 채우면 안 된다.

### 산출물

`inje_lexicon/domain/food-desert.json`

```json
{
  "lexicon_version": "inje-food-desert-v0.1",
  "source_domain_pack": "food-desert-v1",
  "source_policy_version": "luna-matching-v0.4",
  "entries": [
    {
      "canonical": "joint_purchase_draft",
      "canonical_ko": "공동구매",
      "surface_forms": [],
      "domain": "food-desert",
      "layer": "L4",
      "evidence": "domain_pack",
      "verified": false
    }
  ]
}
```

- `surface_forms`는 현장 검증 전까지 빈 배열로 둔다
- `verified: false`는 아직 실제 발화로 확인되지 않았음을 뜻한다
- Domain Pack 버전을 명시해, 정책이 바뀌면 렉시콘도 갱신해야 함을 추적한다

---

## 4. 연결 지점 B — 동의 기반 발화 기여 채널

**신규 설계 필요. Luna의 프라이버시 경계를 침범하지 않는 별도 경로.**

### 설계 원칙

1. 기존 `matching_requests`와 `audit_events`는 **손대지 않는다**
2. 발화 데이터는 **별도 테이블**에 저장하며 매칭 흐름과 분리한다
3. 저장 조건은 **명시적 동의**이며, 동의 기록은 Participation Passport에 남긴다
4. 동의 철회 시 해당 발화는 삭제되고, 파생 렉시콘 항목도 함께 제거된다
5. 기본값은 **수집하지 않음**이다

### 제안 데이터 모델

```python
class UtteranceContribution(Base):
    """
    주민이 명시적으로 동의한 경우에만 저장되는 언어 기여 기록.
    matching_requests 및 audit_events와 독립적으로 운영한다.
    """
    __tablename__ = "utterance_contributions"

    id: str                          # uuid
    contributor_passport_id: str     # Participation Passport 참조 (동의 근거)
    consent_version: str             # 동의서 버전
    consent_granted_at: datetime

    original_text: str               # 원문 — 절대 표준화로 덮어쓰지 않음
    normalized_text: str | None      # 표준어 정규화본 (모델 입력용)
    region_tag: str | None           # 추정 지역 (예: inje)

    domain: str                      # "food-desert"
    request_type: str | None         # Domain Pack의 request_type과 정렬

    collection_channel: str          # "field_interview" | "reception_optin" | ...
    collected_by: str                # 수집 담당 Human ID

    status: str                      # "active" | "withdrawn" | "purged"
    withdrawn_at: datetime | None

    created_at: datetime
```

### 반드시 지킬 것

| 항목 | 규칙 |
|---|---|
| 감사로그 | 발화 원문을 `audit_events.detail`에 넣지 않는다. 기여 발생 사실과 ID만 기록한다 |
| 원문 보존 | `original_text`는 어떤 경우에도 정규화본으로 덮어쓰지 않는다 |
| 동의 철회 | 철회 시 `status`를 바꾸는 것으로 끝내지 않고, 파생 렉시콘 항목까지 추적 제거한다 |
| 기본값 | 수집하지 않음. 옵트인만 유효하며 옵트아웃 방식은 사용하지 않는다 |
| 접근 권한 | 별도 권한(`corpus:read`)을 신설한다. 매칭 권한으로 접근할 수 없어야 한다 |

### Participation Passport와의 연결

Executive Brief 10장은 Participation Passport를
*"누가 어떤 활동에 참여하고 어떤 기여를 했는지를 안전하게 기록하는 참여 이력"*으로 정의한다.

**언어 데이터 기여를 이 참여 활동의 한 유형으로 정의하면**, 별도 개인정보 동의 체계를
새로 만들 필요 없이 기존 설계 위에 얹을 수 있다.

이는 브리프 10장의 논지와도 일치한다 — 주민은 데이터 수집 대상이 아니라
*"지역 지식과 경험을 만드는 구성원"*이며, 방언 기여는 기록되는 기여 활동이 된다.

### 미해결 사항

- Participation Passport의 구현체가 현재 코드베이스에 없다. `human_passports`와의 관계 정리 필요
- 기여에 대한 보상 체계 여부와 수준은 미정 (브리프 10장 주석도 "별도 동의·거버넌스 기준" 필요를 명시)

---

## 5. 연결 지점 C — 역방향: 토크나이저 → Luna Edge 효율

두 프로젝트의 이익은 단방향이 아니다.

```
Luna  →  토크나이저 :  도메인 개념 체계 + (동의 시) 실제 발화
토크나이저  →  Luna :  토큰 수 감소 → Edge 추론 효율 개선
```

### 측정 가능한 형태로 정의

토크나이저 방법론 v0.1은 "토큰 수 감소가 Edge 추론 속도·메모리를 직접 개선한다"고 서술했으나,
그 효과를 검증할 대상이 없었다. **Luna가 그 대상이 된다.**

| 측정 항목 | 방법 |
|---|---|
| 토큰 절감률 | 동일 Luna 접수 문장에 대해 확장 전후 토큰 수 비교 |
| 추론 지연 | 라즈베리 파이에서 Luna 처리 경로 응답 시간 실측 |
| 노드당 처리량 | 동일 하드웨어에서 동시 처리 가능 요청 수 |

이 수치는 Executive Brief 04장의 "AI 크레딧을 시드머니로" 모델의 재무 근거이기도 하다.
Edge 한계비용이 낮아야 크레딧 모델이 성립하기 때문이다.

---

## 6. 승계할 경계 원칙

본 연결 작업은 `development-roadmap.md` 2장의 변경 불가 원칙을 그대로 승계한다.
특히 다음 항목이 직접 적용된다.

- 외부 효과에 대한 최종 의사결정과 책임은 검증된 Human에게 있다
- Kill Switch와 감사 추적은 기능 개발보다 우선하는 운영 통제다
- 실제 운영 승인 전까지 기본 모드는 `dry_run`과 `recommendation_only`다
- `main` 병합과 운영 배포는 대표자의 별도 승인 대상이다

추가로 본 작업에만 적용되는 원칙을 둔다.

- **코퍼스 수집은 매칭 서비스의 부수 효과가 되어서는 안 된다.** 접수했다는 이유로 발화가 저장되지 않는다
- **동의 없는 발화는 어떤 형태로도 렉시콘에 반영하지 않는다.** 집계·통계 형태도 포함한다

---

## 7. 단계 계획

| 단계 | 내용 | 선행 조건 | 개인정보 위험 |
|---|---|---|---|
| A-1 | Domain Pack → 렉시콘 시드 JSON 생성 | 없음 | 없음 |
| A-2 | 렉시콘 스키마 확정 및 저장소 위치 결정 | A-1 | 없음 |
| B-1 | 동의서 문안·철회 절차 확정 | 법률 검토 (Malu) | — |
| B-2 | Participation Passport ↔ human_passports 관계 정리 | B-1 | — |
| B-3 | `utterance_contributions` 모델 및 migration 구현 | B-2 | 낮음 (스키마만) |
| B-4 | 현장 수집 파일럿 (소규모) | B-1~B-3 전부 | **높음** |
| C-1 | 확장 vocab으로 Luna 처리 경로 토큰 수 측정 | 토크나이저 Phase 2 완료 | 없음 |
| C-2 | 라즈베리 파이 실측 | C-1 | 없음 |

### 순서를 바꾸면 안 되는 지점

**B-4(현장 수집)는 B-1~B-3이 모두 끝나기 전에 시작하지 않는다.**
동의 절차 없이 수집된 발화는 사후에 전량 폐기해야 하며, 그 경우 주민 신뢰도 함께 잃는다.

A 계열과 C 계열은 개인정보 위험이 없으므로 B와 병행 가능하다.
**A-1은 오늘 바로 착수할 수 있다.**

---

## 8. 결정이 필요한 사항

| 항목 | 결정자 | 시점 |
|---|---|---|
| 렉시콘 저장소 위치 (ecosystem vs research-lab) | Koda, Kbin | A-2 전 |
| 동의서 문안 및 철회 절차 | Malu, Kbin | B-1 |
| Participation Passport 구현 주체와 일정 | re.eul, Koda | B-2 전 |
| 언어 기여에 대한 보상 여부·수준 | re.eul | B-1과 함께 |
| `corpus:read` 권한의 부여 범위 | Kbin | B-3 |

---

## 9. 이 연결이 해결하는 기존 문제

| 기존 문제 | 출처 | 본 설계의 해결 |
|---|---|---|
| L4 도메인 어휘 정의가 막연함 | 토크나이저 방법론 v0.1 | Domain Pack에서 파생 (A) |
| 코퍼스 90%가 표준어 문어체 | 기획서 비교검토 2-③ | 구어 채널 확보 (B) |
| 개인정보 절차 부재 | 토크나이저 방법론 5장 | Participation Passport 활용 (B) |
| 토큰 절감 효과 검증 대상 없음 | 토크나이저 방법론 8장 | Luna가 측정 대상 (C) |
| 첫 파일럿과 코퍼스 우선순위 불일치 | 기획서 비교검토 | 둘 다 식품사막으로 정렬 |

---

## 10. 검토 요청 항목

1. Luna가 자연어를 저장하지 않는 현재 설계를 유지하는 것이 맞는가 (본 문서는 유지를 전제함)
2. `utterance_contributions`를 open-reception 안에 둘 것인가, 별도 서비스로 분리할 것인가
3. Domain Pack이 갱신될 때 렉시콘 갱신을 강제할 방법 (버전 핀 + CI 검사?)
4. A-1을 즉시 착수해도 좋은가

---

**SIL 이음 | Systems Integrity Lead**

본 문서는 Luna 구현체(`app/main.py`, `app/matching_policy.py`)와 거버넌스 문서를 직접 확인해 작성했다.
2절의 "Luna는 자연어를 저장하지 않는다"는 사실 확인 결과이며, 이전 구두 논의에서
"Luna 접수 로그를 코퍼스로 활용"이라 언급했던 내용을 정정한 것이다.
