import pytest

from app.matching_policy import (
    DOMAIN_PACK_VERSION,
    FOOD_DESERT_DOMAIN_PACK,
    MATCHING_POLICY_VERSION,
    get_domain_pack,
)


def test_food_desert_domain_pack_has_versioned_request_contracts():
    pack = get_domain_pack("food-desert")

    assert pack.version == DOMAIN_PACK_VERSION == "food-desert-v1"
    assert pack.matching_policy_version == MATCHING_POLICY_VERSION == "luna-matching-v0.4"
    assert tuple(pack.request_policies) == (
        "food_access_research",
        "membership_guidance",
        "joint_purchase_draft",
    )


@pytest.mark.parametrize(
    ("request_type", "maximum_risk", "supervision_level", "junior_eligible"),
    [
        ("food_access_research", "low", "standard", True),
        ("membership_guidance", "medium", "steward", False),
        ("joint_purchase_draft", "high", "human", False),
    ],
)
def test_request_policy_declares_risk_and_supervision(
    request_type,
    maximum_risk,
    supervision_level,
    junior_eligible,
):
    policy = FOOD_DESERT_DOMAIN_PACK.policy_for(request_type)

    assert policy.maximum_risk == maximum_risk
    assert policy.supervision_level == supervision_level
    assert policy.junior_eligible is junior_eligible
    assert policy.required_competencies
    assert policy.required_permissions


def test_unknown_domain_and_request_type_are_rejected():
    with pytest.raises(ValueError, match="Unsupported matching domain"):
        get_domain_pack("unknown")

    with pytest.raises(ValueError, match="Unsupported request type"):
        FOOD_DESERT_DOMAIN_PACK.policy_for("unknown")


def test_domain_pack_is_immutable():
    with pytest.raises(TypeError):
        FOOD_DESERT_DOMAIN_PACK.request_policies["new"] = object()
