# -*- coding: utf-8 -*-
"""
Domain Pack → 렉시콘 시드 생성기 (연결 지점 A-1)

Luna Open Reception의 Domain Pack 정의에서 AI Inje Tokenizer의
L4(도메인 어휘) 레이어 시드를 생성한다.

설계 근거:
    open-reception/app/matching_policy.py 의 FOOD_DESERT_DOMAIN_PACK 은
    거버넌스 승인을 거친 도메인 개념 체계다. 이를 토크나이저 렉시콘의
    출발점으로 삼으면, L4 어휘가 추측이 아니라 정책에서 파생된다.

중요한 설계 결정:
    surface_forms(주민이 실제로 쓰는 표현)는 **비워둔 채로 생성한다.**
    인제 주민이 어떤 말을 쓰는지는 현장에서 확인해야 하며,
    책상에서 채우면 검증되지 않은 추측이 사전에 굳어진다.
    verified=False 가 그 상태를 명시한다.

개인정보:
    본 스크립트는 Domain Pack 정의(코드 상수)만 읽는다.
    주민 발화나 접수 기록에 접근하지 않는다. 개인정보 위험 없음.

작성: SIL 이음
날짜: 2026-08-03
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ============================================================
# Domain Pack 정의 미러
# ============================================================
# 원본: open-reception/app/matching_policy.py
#
# 왜 import 하지 않고 미러링하는가:
#   렉시콘 생성기는 mulberry-research-lab 쪽에서 돌 수도 있어
#   open-reception 패키지에 의존하지 않는 편이 낫다.
#   대신 SOURCE_POLICY_VERSION 을 고정해, 원본이 바뀌면
#   불일치를 감지할 수 있게 한다 (verify_sync() 참조).

SOURCE_DOMAIN_PACK_VERSION = "food-desert-v1"
SOURCE_POLICY_VERSION = "luna-matching-v0.4"
LEXICON_VERSION = "inje-food-desert-v0.1"

# Domain Pack 의 request_policies 에서 추출한 정규 개념들
DOMAIN_PACK_MIRROR: dict[str, dict[str, Any]] = {
    "food_access_research": {
        "required_competencies": ["food-desert", "research"],
        "required_permissions": ["research"],
        "maximum_risk": "low",
        "supervision_level": "standard",
        "junior_eligible": True,
    },
    "membership_guidance": {
        "required_competencies": ["food-desert", "membership-guidance"],
        "required_permissions": ["recommend"],
        "maximum_risk": "medium",
        "supervision_level": "steward",
        "junior_eligible": False,
    },
    "joint_purchase_draft": {
        "required_competencies": ["food-desert", "joint-purchase"],
        "required_permissions": ["draft"],
        "maximum_risk": "high",
        "supervision_level": "human",
        "junior_eligible": False,
    },
}

# 정규 개념의 한국어 대응.
# 이것은 "주민이 쓰는 말"이 아니라 "정책 개념의 한국어 명칭"이다.
# 주민 표현은 surface_forms 에 별도로 들어가며, 현장 확인 전에는 비어 있다.
CANONICAL_KO: dict[str, str] = {
    "food_access_research": "식품 접근성 조사",
    "membership_guidance": "가입 안내",
    "joint_purchase_draft": "공동구매 초안",
    # competency / permission 어휘
    "food-desert": "식품사막",
    "research": "조사",
    "membership-guidance": "가입 안내",
    "joint-purchase": "공동구매",
    "recommend": "추천",
    "draft": "초안 작성",
}


# ============================================================
# 렉시콘 항목 정의
# ============================================================

@dataclass
class LexiconEntry:
    """
    렉시콘 항목 하나.

    Attributes:
        canonical:      정규 개념 식별자 (Domain Pack 원문)
        canonical_ko:   정규 개념의 한국어 명칭
        surface_forms:  주민이 실제로 사용하는 표현들.
                        현장 검증 전에는 빈 리스트다.
        layer:          토크나이저 방법론의 레이어 (L1~L4)
        domain:         도메인 식별자
        entry_type:     request_type | competency | permission
        evidence:       이 항목의 근거 출처
        verified:       실제 발화로 확인되었는지 여부
    """
    canonical: str
    canonical_ko: str
    surface_forms: list[str]
    layer: str
    domain: str
    entry_type: str
    evidence: str
    verified: bool


def build_entries() -> list[LexiconEntry]:
    """
    Domain Pack 미러에서 렉시콘 항목들을 생성한다.

    세 종류의 정규 개념을 추출한다:
        1. request_type   — 요청 유형
        2. competency     — 필요 역량
        3. permission     — 필요 권한

    Returns:
        중복 제거된 LexiconEntry 리스트 (canonical 기준 정렬)
    """
    seen: dict[str, LexiconEntry] = {}

    def add(canonical: str, entry_type: str) -> None:
        """중복 없이 항목을 추가한다."""
        if canonical in seen:
            return
        seen[canonical] = LexiconEntry(
            canonical=canonical,
            canonical_ko=CANONICAL_KO.get(canonical, ""),
            surface_forms=[],          # 현장 확인 전까지 비워둔다
            layer="L4",                # 도메인 어휘 레이어
            domain="food-desert",
            entry_type=entry_type,
            evidence="domain_pack",
            verified=False,            # 실제 발화 확인 전
        )

    for request_type, policy in DOMAIN_PACK_MIRROR.items():
        add(request_type, "request_type")
        for competency in policy["required_competencies"]:
            add(competency, "competency")
        for permission in policy["required_permissions"]:
            add(permission, "permission")

    return [seen[k] for k in sorted(seen)]


LEXICON_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = LEXICON_ROOT.parent


def default_output_path() -> Path:
    """생성물 경로. 스크립트 위치 기준이므로 어디서 실행해도 같은 곳에 쓴다."""
    return LEXICON_ROOT / "domain" / "food-desert.json"


def default_source_path() -> Path:
    """Luna Domain Pack 원본 경로."""
    return REPO_ROOT / "open-reception" / "app" / "matching_policy.py"


def build_lexicon() -> dict[str, Any]:
    """
    완성된 렉시콘 문서를 만든다.

    source_* 필드는 추적성을 위해 반드시 포함한다.
    Domain Pack 이나 정책이 갱신되면 렉시콘도 갱신 대상임을 알 수 있어야 한다.
    """
    entries = build_entries()

    return {
        "lexicon_version": LEXICON_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_domain_pack": SOURCE_DOMAIN_PACK_VERSION,
        "source_policy_version": SOURCE_POLICY_VERSION,
        "generator": "build_lexicon_seed.py",
        "notes": (
            "Domain Pack 에서 자동 생성된 시드입니다. "
            "surface_forms 는 현장 확인 후에만 채웁니다. "
            "verified=false 인 항목은 실제 발화로 확인되지 않았습니다."
        ),
        "statistics": {
            "total": len(entries),
            "verified": sum(1 for e in entries if e.verified),
            "unverified": sum(1 for e in entries if not e.verified),
            "with_surface_forms": sum(1 for e in entries if e.surface_forms),
        },
        "entries": [asdict(e) for e in entries],
    }


def verify_sync(matching_policy_path: Path) -> tuple[bool, str]:
    """
    원본 Domain Pack 과 미러가 일치하는지 확인한다.

    open-reception/app/matching_policy.py 가 갱신되었는데
    이 스크립트의 미러가 그대로면 렉시콘이 낡은 정책을 반영하게 된다.
    CI 에서 이 함수를 호출해 불일치를 잡는 것을 권장한다.

    Args:
        matching_policy_path: matching_policy.py 경로

    Returns:
        (일치 여부, 메시지)
    """
    if not matching_policy_path.exists():
        return False, f"원본을 찾을 수 없습니다: {matching_policy_path}"

    source = matching_policy_path.read_text(encoding="utf-8")

    problems: list[str] = []

    # 버전 상수 확인
    if f'DOMAIN_PACK_VERSION = "{SOURCE_DOMAIN_PACK_VERSION}"' not in source:
        problems.append(
            f"DOMAIN_PACK_VERSION 불일치 — 미러는 {SOURCE_DOMAIN_PACK_VERSION} 기준"
        )
    if f'MATCHING_POLICY_VERSION = "{SOURCE_POLICY_VERSION}"' not in source:
        problems.append(
            f"MATCHING_POLICY_VERSION 불일치 — 미러는 {SOURCE_POLICY_VERSION} 기준"
        )

    # request_type 이 추가/삭제되었는지 확인
    for request_type in DOMAIN_PACK_MIRROR:
        if f'"{request_type}"' not in source:
            problems.append(f"원본에서 사라진 request_type: {request_type}")

    if problems:
        return False, "\n".join(f"  - {p}" for p in problems)

    return True, "원본과 미러가 일치합니다."


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check_only = "--check-only" in sys.argv

    print("=" * 62)
    title = "Domain Pack 동기화 확인" if check_only else "Domain Pack → 렉시콘 시드 생성"
    print(f"{title} (연결 지점 A-1)")
    print("=" * 62)

    # 1. 원본 동기화 확인 (경로가 주어진 경우)
    if args:
        policy_path = Path(args[0])
        ok, message = verify_sync(policy_path)
        print(f"\n[동기화 확인] {policy_path}")
        print(message if ok else f"불일치 감지:\n{message}")
        if not ok:
            print("\n미러를 갱신한 뒤 다시 실행하세요.")
            return 1
    else:
        policy_path = default_source_path()
        if policy_path.exists():
            ok, message = verify_sync(policy_path)
            print(f"\n[동기화 확인] {policy_path}")
            print(message if ok else f"불일치 감지:\n{message}")
            if not ok:
                print("\n미러를 갱신한 뒤 다시 실행하세요.")
                return 1
        else:
            print(f"\n[동기화 확인] 건너뜀 — 원본 없음: {policy_path}")

    if check_only:
        print("\n--check-only: 동기화 확인만 수행하고 종료합니다.")
        return 0

    # 2. 렉시콘 생성
    lexicon = build_lexicon()

    out_path = default_output_path()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(lexicon, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # 3. 결과 출력
    stats = lexicon["statistics"]
    print(f"\n[생성 완료] {out_path}")
    print(f"  총 항목      : {stats['total']}")
    print(f"  검증됨       : {stats['verified']}")
    print(f"  미검증       : {stats['unverified']}")
    print(f"  표현 보유    : {stats['with_surface_forms']}")

    print("\n[항목 목록]")
    by_type: dict[str, list[str]] = {}
    for e in lexicon["entries"]:
        by_type.setdefault(e["entry_type"], []).append(
            f"{e['canonical']} ({e['canonical_ko']})"
        )
    for entry_type in sorted(by_type):
        print(f"  {entry_type}:")
        for label in by_type[entry_type]:
            print(f"    - {label}")

    print("\n" + "=" * 62)
    print("다음 단계: surface_forms 를 현장에서 채웁니다.")
    print("책상에서 채우지 마세요. verified=false 가 그 이유입니다.")
    print("=" * 62)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
