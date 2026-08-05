from pathlib import Path
import sys

LEXICON_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LEXICON_ROOT / "scripts"))

from build_lexicon_seed import DOMAIN_PACK_MIRROR, extract_policy_snapshot, verify_sync


def test_sync_detects_policy_field_change(tmp_path: Path):
    source = LEXICON_ROOT.parent / "open-reception/app/matching_policy.py"
    changed = source.read_text(encoding="utf-8").replace('maximum_risk="low"', 'maximum_risk="high"', 1)
    candidate = tmp_path / "matching_policy.py"; candidate.write_text(changed, encoding="utf-8")
    ok, message = verify_sync(candidate)
    assert not ok
    assert "food_access_research" in message


def test_snapshot_matches_all_mirrored_fields():
    source = LEXICON_ROOT.parent / "open-reception/app/matching_policy.py"
    _, _, policies = extract_policy_snapshot(source)
    assert policies == DOMAIN_PACK_MIRROR
