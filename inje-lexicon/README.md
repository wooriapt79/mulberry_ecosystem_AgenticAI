# Inje Lexicon

AI Inje Tokenizer 의 지역 어휘 사전. Luna Open Reception 의 Domain Pack 에서 파생된다.

- 설계 문서: [`docs/luna-tokenizer-integration-v0.1.md`](../docs/luna-tokenizer-integration-v0.1.md)
- 원본 정책: [`open-reception/app/matching_policy.py`](../open-reception/app/matching_policy.py)

---

## 이 폴더가 하는 일

토크나이저의 L4(도메인 어휘) 레이어를 **추측이 아니라 거버넌스 모델에서** 만든다.
Luna Domain Pack (food-desert-v1)
│ 거버넌스 승인을 거친 도메인 개념 체계
▼
build_lexicon_seed.py
│ request_type / competency / permission 추출
▼
domain/food-desert.json
│ surface_forms 는 비어 있음 (verified: false)
▼
현장 검증 후 surface_forms 채움


---

## 중요한 원칙

### surface_forms 는 현장에서만 채운다

`surface_forms`(주민이 실제로 쓰는 표현)는 생성기가 **절대 임의로 채우지 않는다.**
인제 주민이 어떤 말을 쓰는지는 현장에서 확인해야 하며, 책상에서 채우면
검증되지 않은 추측이 사전에 굳는다.

`verified: false` 는 "아직 실제 발화로 확인되지 않았음"을 뜻한다.
`test_seed_entries_have_empty_surface_forms` 가 이 원칙을 강제한다.

### 개인정보를 담지 않는다

렉시콘은 어휘 사전이다. 주민 발화나 신원 정보를 담는 자료구조가 아니다.
발화 기여 데이터는 별도 채널(`utterance_contributions`)로 관리하며,
그 설계는 연결 설계 문서 4절을 따른다.

`test_lexicon_contains_no_personal_data_fields` 와 CI 가 이를 검사한다.

### 정책이 바뀌면 렉시콘도 바뀐다

Luna 의 `matching_policy.py` 가 갱신되면 CI 가 불일치를 감지해 실패한다.
이때 `DOMAIN_PACK_MIRROR` 와 버전 상수를 갱신한 뒤 렉시콘을 재생성해야 한다.

---

## 사용법

### 렉시콘 생성 / 재생성

```bash
cd inje-lexicon
python scripts/build_lexicon_seed.py
```

원본 경로는 자동 탐색한다 (`../open-reception/app/matching_policy.py`).
다른 경로를 쓰려면 인자로 넘긴다.

```bash
python scripts/build_lexicon_seed.py /path/to/matching_policy.py
```

### 동기화만 확인

```bash
python scripts/build_lexicon_seed.py --check-only
```

미러가 원본과 어긋나면 종료코드 1 을 반환한다. CI 가 이 명령을 쓴다.

### 테스트

```bash
python -m pytest tests/ -v
```

---

## 구조

inje-lexicon/
├── README.md
├── domain/
│ └── food-desert.json 생성물 (커밋 대상)
├── scripts/
│ └── build_lexicon_seed.py 생성기
└── tests/
└── test_lexicon_sync.py 동기화·불변식 검증


---

## 항목 스키마

```json
{
  "canonical": "joint_purchase_draft",
  "canonical_ko": "공동구매 초안",
  "surface_forms": [],
  "layer": "L4",
  "domain": "food-desert",
  "entry_type": "request_type",
  "evidence": "domain_pack",
  "verified": false
}
```

| 필드 | 의미 |
|---|---|
| `canonical` | Domain Pack 의 정규 식별자 |
| `canonical_ko` | 정규 개념의 한국어 명칭 (주민 표현 아님) |
| `surface_forms` | 주민이 실제로 쓰는 표현. 현장 검증 후에만 채움 |
| `layer` | 토크나이저 방법론의 레이어 (L1~L4) |
| `entry_type` | `request_type` / `competency` / `permission` |
| `evidence` | 근거 출처. `domain_pack` 은 자동 생성을 뜻함 |
| `verified` | 실제 발화로 확인되었는지 |

---

## 다음 단계

현재는 연결 설계 문서의 **A-1, A-2** 까지 구현되어 있다.

| 단계 | 내용 | 상태 |
|---|---|---|
| A-1 | Domain Pack → 시드 생성 | 완료 |
| A-2 | 스키마 확정 및 위치 결정 | 완료 |
| B-1 | 동의서 문안·철회 절차 | 미착수 (법률 검토 필요) |
| B-2 | Participation Passport 관계 정리 | 미착수 |
| B-3 | `utterance_contributions` 모델 | 미착수 |
| B-4 | 현장 수집 파일럿 | **B-1~B-3 완료 전 착수 금지** |
| C-1 | Luna 처리 경로 토큰 수 측정 | 토크나이저 Phase 2 대기 |

### surface_forms 를 채우기 시작할 때 주의

현재 `test_committed_lexicon_matches_generator` 는 커밋된 JSON 이
생성기 출력과 완전히 같아야 통과한다. 현장 검증 결과를 손으로 채우기 시작하면
이 테스트가 실패한다.

그 시점에 생성물과 수기 입력을 분리하거나, 병합 로직을 생성기에 넣어야 한다.
설계를 미리 정해두지 않고 테스트만 끄면 드리프트 검사가 무력화된다.
