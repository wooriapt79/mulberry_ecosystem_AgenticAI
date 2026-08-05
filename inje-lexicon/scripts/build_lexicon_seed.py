# -*- coding: utf-8 -*-
"""Build the AI Inje L4 lexicon seed from Luna's governed Domain Pack."""

from __future__ import annotations

import ast
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SOURCE_DOMAIN_PACK_VERSION = "food-desert-v1"
SOURCE_POLICY_VERSION = "luna-matching-v0.4"
LEXICON_VERSION = "inje-food-desert-v0.1"

DOMAIN_PACK_MIRROR: dict[str, dict[str, Any]] = {
    "food_access_research": {"required_competencies": ["food-desert", "research"],
        "required_permissions": ["research"], "maximum_risk": "low",
        "supervision_level": "standard", "junior_eligible": True},
    "membership_guidance": {"required_competencies": ["food-desert", "membership-guidance"],
        "required_permissions": ["recommend"], "maximum_risk": "medium",
        "supervision_level": "steward", "junior_eligible": False},
    "joint_purchase_draft": {"required_competencies": ["food-desert", "joint-purchase"],
        "required_permissions": ["draft"], "maximum_risk": "high",
        "supervision_level": "human", "junior_eligible": False},
}

CANONICAL_KO = {"food_access_research": "식품 접근성 조사", "membership_guidance": "가입 안내",
    "joint_purchase_draft": "공동구매 초안", "food-desert": "식품사막",
    "research": "조사", "membership-guidance": "가입 안내",
    "joint-purchase": "공동구매", "recommend": "추천", "draft": "초안 작성"}


@dataclass
class LexiconEntry:
    canonical: str
    canonical_ko: str
    surface_forms: list[str]
    layer: str
    domain: str
    entry_type: str
    evidence: str
    verified: bool


def _literal(node: ast.AST) -> Any:
    """Read only policy literals; never execute repository source."""
    return ast.literal_eval(node)


def extract_policy_snapshot(path: Path) -> tuple[str, str, dict[str, dict[str, Any]]]:
    """Structurally extract versions and every RequestPolicy field from source."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    versions: dict[str, str] = {}
    policies: dict[str, dict[str, Any]] = {}

    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in {"DOMAIN_PACK_VERSION", "MATCHING_POLICY_VERSION"}:
                versions[name] = _literal(node.value)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key_node, value_node in zip(node.keys, node.values):
            if key_node is None or not isinstance(value_node, ast.Call):
                continue
            if not isinstance(value_node.func, ast.Name) or value_node.func.id != "RequestPolicy":
                continue
            key = _literal(key_node)
            fields = {kw.arg: _literal(kw.value) for kw in value_node.keywords if kw.arg}
            request_type = fields.pop("request_type", None)
            if request_type != key:
                raise ValueError(f"RequestPolicy key/request_type mismatch: {key!r} != {request_type!r}")
            for list_field in ("required_competencies", "required_permissions"):
                fields[list_field] = list(fields[list_field])
            policies[key] = fields

    missing = {"DOMAIN_PACK_VERSION", "MATCHING_POLICY_VERSION"} - versions.keys()
    if missing or not policies:
        raise ValueError(f"Incomplete Domain Pack source; missing={sorted(missing)}, policies={len(policies)}")
    return versions["DOMAIN_PACK_VERSION"], versions["MATCHING_POLICY_VERSION"], policies


def build_entries() -> list[LexiconEntry]:
    seen: dict[str, LexiconEntry] = {}
    def add(canonical: str, entry_type: str) -> None:
        if canonical not in seen:
            seen[canonical] = LexiconEntry(canonical, CANONICAL_KO.get(canonical, ""), [],
                "L4", "food-desert", entry_type, "domain_pack", False)
    for request_type, policy in DOMAIN_PACK_MIRROR.items():
        add(request_type, "request_type")
        for value in policy["required_competencies"]: add(value, "competency")
        for value in policy["required_permissions"]: add(value, "permission")
    return [seen[key] for key in sorted(seen)]


LEXICON_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = LEXICON_ROOT.parent


def default_output_path() -> Path:
    return LEXICON_ROOT / "domain" / "food-desert.json"


def default_source_path() -> Path:
    return REPO_ROOT / "open-reception" / "app" / "matching_policy.py"


def build_lexicon() -> dict[str, Any]:
    entries = build_entries()
    return {"lexicon_version": LEXICON_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_domain_pack": SOURCE_DOMAIN_PACK_VERSION,
        "source_policy_version": SOURCE_POLICY_VERSION,
        "generator": "build_lexicon_seed.py",
        "notes": "Domain Pack-derived seed. surface_forms remain empty until field verification.",
        "statistics": {"total": len(entries), "verified": 0, "unverified": len(entries),
                       "with_surface_forms": 0},
        "entries": [asdict(entry) for entry in entries]}


def verify_sync(matching_policy_path: Path) -> tuple[bool, str]:
    if not matching_policy_path.exists():
        return False, f"원본을 찾을 수 없습니다: {matching_policy_path}"
    try:
        domain_version, policy_version, source_policies = extract_policy_snapshot(matching_policy_path)
    except (SyntaxError, ValueError, KeyError) as exc:
        return False, f"원본 구조를 안전하게 해석하지 못했습니다: {exc}"
    problems = []
    if domain_version != SOURCE_DOMAIN_PACK_VERSION:
        problems.append(f"DOMAIN_PACK_VERSION: source={domain_version}, mirror={SOURCE_DOMAIN_PACK_VERSION}")
    if policy_version != SOURCE_POLICY_VERSION:
        problems.append(f"MATCHING_POLICY_VERSION: source={policy_version}, mirror={SOURCE_POLICY_VERSION}")
    if source_policies != DOMAIN_PACK_MIRROR:
        source_keys, mirror_keys = set(source_policies), set(DOMAIN_PACK_MIRROR)
        if source_keys != mirror_keys:
            problems.append(f"request_type set: source={sorted(source_keys)}, mirror={sorted(mirror_keys)}")
        for key in sorted(source_keys & mirror_keys):
            if source_policies[key] != DOMAIN_PACK_MIRROR[key]:
                problems.append(f"policy fields changed for {key}: source={source_policies[key]}, mirror={DOMAIN_PACK_MIRROR[key]}")
    return (False, "\n".join(f"  - {p}" for p in problems)) if problems else (True, "원본과 미러의 전체 구조가 일치합니다.")


def main() -> int:
    args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    check_only = "--check-only" in sys.argv
    policy_path = Path(args[0]) if args else default_source_path()
    ok, message = verify_sync(policy_path)
    print(message)
    if not ok: return 1
    if check_only: return 0
    lexicon = build_lexicon()
    output = default_output_path(); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(lexicon, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"generated {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
