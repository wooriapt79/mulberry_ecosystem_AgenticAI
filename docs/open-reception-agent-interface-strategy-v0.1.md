# Open Reception Agent Interface Strategy v0.1

- 상태: Strategic Reference / Human review required
- 기준일: 2026-08-17
- 관련 설계: Issue #12
- 실행 추적: Issue #19
- 현재 구현: Draft PR #20
- 적용 대상: PC Web, Mobile Web, future OS/Agent adapters

## 1. 목적

이 문서는 앱 중심 인터페이스가 에이전트 중심 인터페이스로 이동하는 기술 흐름을 검토하고, Mulberry Open Reception의 장기 개발 방향을 고정하기 위한 전략 기준이다.

핵심 판단은 다음과 같다.

> 앱 소프트웨어 자체가 즉시 사라지는 것이 아니라, 사용자가 앱을 찾고 열고 메뉴를 조작하던 최상위 인터페이스가 AI Agent로 이동하고 있다.

기존 구조:

```text
PC:     Person → Web → Service
Mobile: Person → App → Service
```

전환 구조:

```text
Person → AI Agent → Capability / Service
```

Open Reception은 특정 OS의 Super Agent를 복제하는 제품이 아니다. 사용자의 의도를 구조화하고 서비스 후보를 투명하게 제시하며, 동의·권한·Human 승인·감사를 거쳐 실행 계층으로 전달하는 **Human-governed Agent Interface**를 목표로 한다.

## 2. 확인된 기술 동향

### 2.1 HarmonyOS Atomic Service

Huawei는 원서비스(元服务, Atomic Service)를 독립적으로 배포·실행해 하나의 업무 흐름을 완결할 수 있는 서비스 형태로 설명한다. 공식 자료는 면설치, 즉시 접근, 서비스 직행, 여러 시스템 진입점에서의 노출을 강조한다.

ASCF(Atomic Service Cross Framework)는 기존 미니프로그램 개발 방식과 자산을 활용해 HarmonyOS 원서비스로 전환하는 경로를 제공한다.

전략적 의미:

- 대형 앱을 기능 단위 서비스로 분해
- OS와 시스템 AI가 상황에 맞는 기능을 발견
- 앱 탐색보다 의도와 상황 중심으로 서비스 제공
- 서비스가 앱 내부 화면이 아니라 호출 가능한 capability가 됨

### 2.2 Apple App Intents

Apple App Intents는 앱의 행동과 데이터를 구조화해 Apple Intelligence, Siri, Spotlight, Shortcuts 같은 시스템 기능이 발견하고 실행할 수 있도록 한다.

전략적 의미:

- 앱 기능을 schema 기반 action/entity로 공개
- 자연어 요청과 앱 내부 행동 연결
- UI 중심 통합에서 capability 중심 통합으로 이동
- 시스템이 이해할 수 있는 명확한 계약이 경쟁력이 됨

### 2.3 Android AppFunctions

Android AppFunctions는 앱의 기능을 시스템 registry에 공개해 에이전트와 assistant가 도구처럼 발견하고 실행할 수 있도록 하는 플랫폼 API와 Jetpack 계층이다. 공식 문서는 이를 모바일 환경의 MCP 도구에 대응하는 구조로 설명한다.

2026-08 기준 주의사항:

- AppFunctions API는 experimental preview 단계
- Jetpack 구현은 alpha 단계
- Gemini 연동은 제한적 preview에서 확장 중
- API와 지원 범위가 변경될 가능성이 있음

따라서 지금 Mulberry의 핵심 도메인을 Android 전용 AppFunctions에 직접 결합해서는 안 된다. 공통 Capability Contract를 먼저 만들고 Android는 Adapter로 연결해야 한다.

## 3. 과장해서 해석하지 않을 항목

“앱의 종말”은 기술 방향을 설명하는 표현이지 앱 설치·화면·브랜드 경험·백엔드가 사라진다는 뜻이 아니다.

다음 요소는 계속 필요하다.

- 서비스 제공자의 업무 시스템
- 인증·권한·동의
- 복잡한 정보 탐색용 GUI
- 오류 수정과 사용자 확인 화면
- 결제·계약·취소·환불
- 책임 주체와 고객지원
- 감사·보안·법적 기록

또한 다음 주장은 공식 자료로 별도 확인하기 전까지 전략 기준의 확정 사실로 사용하지 않는다.

- 특정 기간 Huawei의 시장점유율 1위 여부
- JD.com이 정확히 200개 이상의 상황별 카드를 연결했다는 수치
- 특정 AI 모델이 모든 HarmonyOS 실행 흐름의 단일 두뇌라는 표현
- 앱 또는 Super App이 단기간 내 사라진다는 전망

기술 방향과 홍보성 수치를 분리한다.

## 4. Mulberry Open Reception 목표 구조

```text
PC / Mobile / Kakao / future OS Agent
                ↓
          Channel Adapter
                ↓
          Open Reception
      intent · Case · consent
                ↓
       Capability Registry
                ↓
       candidate + evidence
                ↓
      User Choice / Human Gate
                ↓
          Service Adapter
                ↓
       result · audit · status
```

### 책임

| 계층 | 책임 |
|---|---|
| Channel Adapter | 입력 형식 변환, 서명, replay 방어, idempotency |
| Reception Core | 의도·Case·상태·동의·공개 진행상황 |
| Capability Registry | 사용 가능한 기능, Provider, schema, risk 탐색 |
| Matching v0.4 | 정책·증거·권한·감독 기반 후보 추천 |
| Human Approval | 담당 확정, 위임, 고위험 실행 승인 |
| Service Adapter | 공급자별 API 차이 격리 |
| Action Gateway | 승인된 실행, 재검증, 결과·실패·보상 처리 |
| Audit | 요청·추천·승인·실행의 상관관계 기록 |

Open Reception은 AI가 모든 결정을 내리는 Super Agent가 아니라 **신뢰·동의·라우팅·승인 계층**이다.

## 5. 공통 Capability Contract

OS별 개발에 앞서 Mulberry 내부 표준 Capability 계약을 정의한다.

| 필드 | 목적 |
|---|---|
| `capability_id` | 기능의 안정된 식별자 |
| `version` | 계약과 구현 버전 |
| `provider_id` | 실제 서비스 제공 주체 |
| `input_schema` | 허용 입력과 필수값 |
| `output_schema` | 결과와 오류 형식 |
| `permissions` | Passport·Mandate 권한 |
| `risk_level` | 자동·추천·승인 필요 수준 |
| `consent_scope` | 사용자 동의 목적과 데이터 |
| `idempotency_policy` | 중복 예약·주문 방지 |
| `evidence_policy` | 추천 근거와 출처 |
| `approval_policy` | Human 승인 조건 |
| `timeout_retry_policy` | 제한시간·재시도·dead-letter |
| `compensation_policy` | 취소·복구·보상 절차 |
| `audit_event_schema` | 요청부터 결과까지 추적 |
| `availability` | 운영 상태와 지원 채널 |

Capability Contract는 MAS, MAGS, MASP, Mulberry Event Schema와 정렬한다.

## 6. PC와 Mobile 적용 원칙

### PC Web

- 복잡한 Case 검토, 근거 비교, Human 승인에 적합
- 운영자와 Steward 업무 화면의 기준 인터페이스
- 접근성, 키보드, 큰 화면 정보 구조 지원

### Mobile Web / PWA

- 설치 없는 접수·상태 확인의 기준 진입점
- Kakao·QR·문자 링크에서 동일한 Reception Core 사용
- 개인정보 입력 최소화
- 모바일 브라우저 종료·재진입·네트워크 단절 처리

### OS Adapter

장기적으로 다음 Adapter를 검토한다.

- Apple App Intents Adapter
- Android AppFunctions Adapter
- HarmonyOS Atomic Service Adapter
- MCP-compatible external agent adapter
- Raspberry Pi / Local Edge Reception Adapter

OS Adapter에는 정책·점수·권한 로직을 넣지 않는다. 모든 Adapter는 동일한 Capability Contract와 Reception Core를 호출한다.

## 7. 단계별 개발 방향

### Stage 0 — Reception Core v0.1

현재 진행 단계.

- Case 상태와 허용 전이
- 익명 Visitor identity
- Passport user와 Visitor 분리
- Human Gate
- 민감정보 비저장 Guard
- correlation ID

### Stage 1 — PC·Mobile Web Reception

- 반응형 Web Reception
- Case 접수·확인·제출
- 공개 가능한 진행상태 조회
- 접근성·모바일 브라우저 검증
- 외부 실행 없음

### Stage 2 — Capability Registry

- 조회·추천 가능한 capability 등록
- Provider·schema·risk·permission 버전 관리
- 승인되지 않은 capability 비활성
- 처음에는 read-only·recommendation-only

### Stage 3 — Service Adapter Sandbox

- 공급자별 API Adapter
- synthetic data와 dry-run
- idempotency·timeout·retry·failure 테스트
- 실제 주문·예약·메시지 금지

### Stage 4 — OS Agent Adapter

- App Intents, AppFunctions, Atomic Service mapping
- OS별 schema 변환
- 사용자 확인과 플랫폼 권한 점검
- Adapter 장애가 Core 정책을 우회하지 못하도록 계약 테스트

### Stage 5 — 제한적 실행

- 낮은 위험의 접수·예약 후보부터 단계적 허용
- 승인 직전 Passport·Mandate·risk 재검증
- 결제·계약은 AP2·Smart Mandate와 별도 Human 승인
- rollback·compensation·Kill Switch 필수

## 8. 고정 안전 원칙

1. **User sovereignty**  
   사용자는 추천 후보, 근거, 제외 사유를 보고 다른 후보를 선택할 수 있어야 한다.

2. **Human authority**  
   고위험 배정·위임·결제·계약·외부 실행은 Human 승인 없이는 진행하지 않는다.

3. **Policy single source**  
   Channel·OS Adapter가 Matching·Spirit Score·권한 정책을 재구현하지 않는다.

4. **Data minimization**  
   서비스 실행에 불필요한 원 대화, 채널 ID, 감정·심리 추론을 저장하지 않는다.

5. **Consent and purpose limitation**  
   동의한 목적·기간·데이터 범위를 넘는 재사용을 금지한다.

6. **Explainable routing**  
   Provider 선택과 추천의 근거를 감사 가능한 형태로 남긴다.

7. **Idempotency and recovery**  
   재시도 시 중복 주문·예약·메시지가 발생하지 않아야 하며 실패는 안전한 보류로 끝나야 한다.

8. **No silent identity merge**  
   PC·Mobile·Kakao 등 서로 다른 채널 계정을 사용자 확인 없이 병합하지 않는다.

9. **Adapter portability**  
   플랫폼 종속 기능은 교체 가능한 Adapter에 제한한다.

10. **Human-gated deployment**  
    Draft PR, CI 통과 또는 후보 환경 생성은 운영 배포 승인을 의미하지 않는다.

## 9. 경쟁력과 플랫폼 권력에 대한 판단

에이전트 시대의 플랫폼 권력은 다음을 장악하는 주체로 이동한다.

1. 사용자의 첫 번째 의도를 받는가
2. 어떤 서비스가 선택되는지를 결정하는가
3. 결제와 실행까지 완수하는가

Mulberry는 이 권력을 불투명하게 독점하는 모델을 지향하지 않는다.

차별화 원칙:

- 지역 사업자와 협동조합에 공정한 접근 기회
- 추천 근거와 이해충돌 표시
- 사용자 선택권
- Smart Mandate 기반 제한 권한
- Human 승인과 Kill Switch
- 사회적 환원과 감사 가능성
- 특정 OS·Super App·AI 공급자에 종속되지 않는 계약

따라서 Open Reception의 전략적 위치는 다음과 같다.

> **사용자 주권을 보존하면서 지역 서비스와 AI Agent를 연결하는 신뢰 가능한 Agent Gateway**

## 10. 기술 의사결정 기준

새 기능을 제안할 때 아래 질문에 모두 답해야 한다.

- 이것은 Core인가, Capability인가, Adapter인가?
- 사용자의 명시적 의도와 동의가 있는가?
- 추천과 실행이 분리되어 있는가?
- 어떤 Human 승인이 필요한가?
- 최소 데이터만 사용하는가?
- Provider 선택 근거를 설명할 수 있는가?
- 중복 실행·실패·취소·복구가 정의되어 있는가?
- 특정 OS가 없어도 동일한 Core 계약이 유지되는가?
- 감사 이벤트와 correlation ID가 연결되는가?
- Kill Switch로 즉시 중단할 수 있는가?

답이 불명확하면 구현보다 계약과 안전 경계를 먼저 작성한다.

## 11. 현재 결론

Open Reception의 현재 방향은 AI Phone과 Agent Interface 시대의 구조와 일치한다.

단기 우선순위는 OS별 앱이나 Super Agent 제작이 아니다.

1. Reception Core v0.1 완성
2. 공통 Capability Contract 정의
3. PC·Mobile Web을 기준 인터페이스로 확립
4. Service Adapter를 sandbox에서 검증
5. App Intents·AppFunctions·Atomic Service는 후속 Adapter로 연결
6. 실제 실행은 AP2·Smart Mandate·Human Approval 이후 단계적으로 허용

이 문서는 미래 트렌드를 이유로 기존 안전 경계를 완화하지 않는다. 기술 변화가 빨라질수록 Mulberry는 계약, 사용자 선택, Human 책임, 감사 가능성을 더 강하게 유지한다.

## 12. 공식 참고자료

- Huawei HarmonyOS Atomic Service  
  https://developer.huawei.com/consumer/cn/harmonyos/fa
- Huawei Atomic Service development guide  
  https://developer.huawei.com/consumer/cn/doc/atomic-guides/atomic-service-development
- Huawei ASCF conversion guidance  
  https://developer.huawei.com/consumer/cn/doc/atomic-faqs/faqs-product-30
- Huawei Atomic Service and App relationship  
  https://developer.huawei.com/consumer/cn/doc/atomic-faqs/faqs-operational-1
- Huawei Xiaoyi system AI assistant  
  https://consumer.huawei.com/cn/mobileservices/celia/
- Apple App Intents  
  https://developer.apple.com/documentation/appintents
- Apple Intelligence developer overview  
  https://developer.apple.com/apple-intelligence/
- Android AppFunctions overview  
  https://developer.android.com/ai/appfunctions
- Android AppFunctions integration guide  
  https://developer.android.com/ai/appfunctions/add-appfunctions
- Android platform AppFunctions API  
  https://developer.android.com/reference/android/app/appfunctions/package-summary
