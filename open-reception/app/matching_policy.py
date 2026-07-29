from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal, Mapping


RiskLevel = Literal["low", "medium", "high"]
SupervisionLevel = Literal["standard", "steward", "human"]

DOMAIN_PACK_VERSION = "food-desert-v1"
MATCHING_POLICY_VERSION = "luna-matching-v0.4"


@dataclass(frozen=True)
class RequestPolicy:
    request_type: str
    required_competencies: tuple[str, ...]
    required_permissions: tuple[str, ...]
    maximum_risk: RiskLevel
    supervision_level: SupervisionLevel
    junior_eligible: bool


@dataclass(frozen=True)
class DomainPack:
    domain: str
    version: str
    matching_policy_version: str
    request_policies: Mapping[str, RequestPolicy]

    def policy_for(self, request_type: str) -> RequestPolicy:
        try:
            return self.request_policies[request_type]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported request type for {self.domain}: {request_type}"
            ) from exc


FOOD_DESERT_DOMAIN_PACK = DomainPack(
    domain="food-desert",
    version=DOMAIN_PACK_VERSION,
    matching_policy_version=MATCHING_POLICY_VERSION,
    request_policies=MappingProxyType(
        {
            "food_access_research": RequestPolicy(
                request_type="food_access_research",
                required_competencies=("food-desert", "research"),
                required_permissions=("research",),
                maximum_risk="low",
                supervision_level="standard",
                junior_eligible=True,
            ),
            "membership_guidance": RequestPolicy(
                request_type="membership_guidance",
                required_competencies=("food-desert", "membership-guidance"),
                required_permissions=("recommend",),
                maximum_risk="medium",
                supervision_level="steward",
                junior_eligible=False,
            ),
            "joint_purchase_draft": RequestPolicy(
                request_type="joint_purchase_draft",
                required_competencies=("food-desert", "joint-purchase"),
                required_permissions=("draft",),
                maximum_risk="high",
                supervision_level="human",
                junior_eligible=False,
            ),
        }
    ),
)

DOMAIN_PACKS: Mapping[str, DomainPack] = MappingProxyType(
    {FOOD_DESERT_DOMAIN_PACK.domain: FOOD_DESERT_DOMAIN_PACK}
)


def get_domain_pack(domain: str) -> DomainPack:
    try:
        return DOMAIN_PACKS[domain]
    except KeyError as exc:
        raise ValueError(f"Unsupported matching domain: {domain}") from exc
