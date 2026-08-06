# -*- coding: utf-8 -*-
"""
렉시콘 동기화 검증 테스트

두 가지 드리프트를 잡는다.

1. 정책 드리프트
   Luna 의 Domain Pack 이 갱신되었는데 렉시콘 생성기의 미러가 그대로인 경우.
   이 상태로 렉시콘을 만들면 낡은 정책을 반영한 어휘가 생긴다.

2. 산출물 드리프트
   커밋된 food-desert.json 이 현재 생성기의 출력과 다른 경우.
   누군가 JSON 을 손으로 고쳤거나, 생성기를 바꾸고 재생성하지 않았을 때 발생한다.

두 검사 모두 CI 에서 자동 실행된다.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

LEXICON_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = LEXICON_ROOT.parent

sys.path.insert(0, str(LEXICON_ROOT / "scripts"))

from build_lexicon_seed import (  # noqa: E402
    DOMAIN_PACK_MIRROR,
    SOURCE_DOMAIN_PACK_VERSION,
    SOURCE_POLICY_VERSION,
    build_lexicon,
    default_output_path,
    default_source_path,
    verify_sync,
)


# ============================================================
# 1. 정책 드리프트 검사
# ============================================================

def test_domain_pack_mirror_matches_source():
    """
    생성기의 Domain Pack 미러가 Luna 원본과 일치해야 한다.

    실패하면: open-reception/app/matching_policy.py 가 바뀐 것이다.
    build_lexicon_seed.py 의 DOMAIN_PACK_MIRROR 와 버전 상수를 갱신한 뒤
    렉시콘을 재생성해야 한다.
    """
    source = default_source_path()
    if not source.exists():
        pytest.skip(f"Luna 원본을 찾을 수 없습니다 (submodule 미초기화?): {source}")

    ok, message = verify_sync(source)
    assert ok, f"Domain Pack 미러가 원본과 어긋났습니다:\n{message}"


def test_all_mirrored_request_types_exist_in_source():
    """미러의 request_type 이 전부 원본에 존재해야 한다."""
    source = default_source_path()
    if not source.exists():
        pytest.skip("Luna 원본 없음")

    text = source.read_text(encoding="utf-8")
    missing = [rt for rt in DOMAIN_PACK_MIRROR if f'"{rt}"' not in text]
    assert not missing, f"원본에 없는 request_type: {missing}"


# ============================================================
# 2. 산출물 드리프트 검사
# ============================================================

def _strip_volatile(lexicon: dict) -> dict:
    """
    실행할 때마다 달라지는 필드를 제거한다.

    generated_at 은 매 실행마다 바뀌므로 비교 대상에서 뺀다.
    이걸 빼지 않으면 테스트가 항상 실패한다.
    """
    trimmed = dict(lexicon)
    trimmed.pop("generated_at", None)
    return trimmed


def test_committed_lexicon_matches_generator():
    """
    커밋된 JSON 이 현재 생성기 출력과 같아야 한다.

    실패하면: 생성기를 바꾸고 재생성하지 않았거나,
    JSON 을 손으로 수정한 것이다.

    주의: surface_forms 를 현장 검증 후 손으로 채우기 시작하면
    이 테스트는 그 시점에 설계를 다시 봐야 한다.
    (생성물과 수기 입력을 분리하거나, 병합 로직을 생성기에 넣어야 함)
    """
    out_path = default_output_path()
    assert out_path.exists(), (
        f"렉시콘 산출물이 없습니다: {out_path}\n"
        "scripts/build_lexicon_seed.py 를 실행해 생성하세요."
    )

    committed = json.loads(out_path.read_text(encoding="utf-8"))
    regenerated = build_lexicon()

    assert _strip_volatile(committed) == _strip_volatile(regenerated), (
        "커밋된 렉시콘이 생성기 출력과 다릅니다.\n"
        "scripts/build_lexicon_seed.py 를 다시 실행해 재생성하세요."
    )


# ============================================================
# 3. 렉시콘 구조 불변식
# ============================================================

def test_lexicon_records_source_versions():
    """추적성: 어떤 정책 버전에서 파생됐는지 기록되어야 한다."""
    lexicon = build_lexicon()
    assert lexicon["source_domain_pack"] == SOURCE_DOMAIN_PACK_VERSION
    assert lexicon["source_policy_version"] == SOURCE_POLICY_VERSION


def test_seed_entries_are_unverified():
    """
    Domain Pack 에서 자동 생성된 항목은 verified=False 여야 한다.

    자동 생성물은 실제 주민 발화로 확인된 것이 아니다.
    verified=True 는 현장 검증을 거친 항목에만 붙일 수 있다.
    """
    lexicon = build_lexicon()
    wrongly_verified = [
        e["canonical"]
        for e in lexicon["entries"]
        if e["evidence"] == "domain_pack" and e["verified"]
    ]
    assert not wrongly_verified, (
        f"현장 검증 없이 verified=True 인 항목: {wrongly_verified}"
    )


def test_seed_entries_have_empty_surface_forms():
    """
    자동 생성 시점에는 surface_forms 가 비어 있어야 한다.

    주민이 실제로 쓰는 표현은 현장에서 확인해야 하며,
    생성기가 임의로 채우면 검증되지 않은 추측이 사전에 굳는다.
    """
    lexicon = build_lexicon()
    prefilled = [
        e["canonical"]
        for e in lexicon["entries"]
        if e["evidence"] == "domain_pack" and e["surface_forms"]
    ]
    assert not prefilled, (
        f"생성기가 surface_forms 를 임의로 채웠습니다: {prefilled}"
    )


def test_entry_identifiers_are_unique():
    """canonical 식별자에 중복이 없어야 한다."""
    lexicon = build_lexicon()
    canonicals = [e["canonical"] for e in lexicon["entries"]]
    duplicates = {c for c in canonicals if canonicals.count(c) > 1}
    assert not duplicates, f"중복된 canonical: {duplicates}"


def test_statistics_match_entries():
    """통계 필드가 실제 항목과 일치해야 한다."""
    lexicon = build_lexicon()
    entries = lexicon["entries"]
    stats = lexicon["statistics"]

    assert stats["total"] == len(entries)
    assert stats["verified"] == sum(1 for e in entries if e["verified"])
    assert stats["unverified"] == sum(1 for e in entries if not e["verified"])
    assert stats["with_surface_forms"] == sum(1 for e in entries if e["surface_forms"])


# ============================================================
# 4. 개인정보 경계 검사
# ============================================================

def test_lexicon_contains_no_personal_data_fields():
    """
    렉시콘에 개인정보 관련 필드가 없어야 한다.

    렉시콘은 Domain Pack 에서 파생된 어휘 사전이며,
    주민 발화나 신원 정보를 담는 자료구조가 아니다.
    발화 기여는 별도의 utterance_contributions 로 관리한다.
    """
    forbidden_keys = {
        "requester_id", "contributor_id", "user_id",
        "original_text", "utterance", "speaker",
        "phone", "address", "name",
    }
    lexicon = build_lexicon()

    for entry in lexicon["entries"]:
        leaked = forbidden_keys & set(entry.keys())
        assert not leaked, (
            f"렉시콘 항목에 개인정보성 필드가 있습니다: {leaked}\n"
            "발화 데이터는 utterance_contributions 로 분리해야 합니다."
        )
