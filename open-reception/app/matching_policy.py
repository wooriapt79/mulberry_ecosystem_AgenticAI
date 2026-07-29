from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Literal, Mapping


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


RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


@dataclass(frozen=True)
class CandidateEvaluation:
    eligible: bool
    score: float | None
    evidence: Mapping[str, object]
    exclusion_reasons: tuple[str, ...]


def evaluate_candidate(
    *,
    policy: RequestPolicy,
    request_risk: RiskLevel,
    mandate_permissions: Iterable[str],
    agent_id: str,
    agent_level: str,
    agent_domains: Iterable[str],
    passport_permissions: Iterable[str],
    spirit_score: float,
    agent_status: str,
    supervisor_active: bool,
) -> CandidateEvaluation:
    domains = set(agent_domains)
    permissions = set(passport_permissions)
    mandate = set(mandate_permissions)
    required_permissions = set(policy.required_permissions) | mandate
    required_competencies = set(policy.required_competencies)
    reasons: list[str] = []

    if agent_status != "active":
        reasons.append("agent_inactive")
    if spirit_score < 0.4:
        reasons.append("spirit_score_below_threshold")
    if not required_competencies.issubset(domains):
        reasons.append("competency_evidence_missing")
    if not required_permissions.issubset(permissions):
        reasons.append("permission_scope_mismatch")
    if RISK_ORDER[request_risk] > RISK_ORDER[policy.maximum_risk]:
        reasons.append("request_risk_exceeds_policy")
    if agent_level == "junior":
        if not policy.junior_eligible:
            reasons.append("junior_not_eligible")
        if not supervisor_active:
            reasons.append("active_supervisor_required")

    evidence = MappingProxyType(
        {
            "agent_id": agent_id,
            "competencies": sorted(required_competencies & domains),
            "permissions": sorted(required_permissions & permissions),
            "spirit_score": spirit_score,
            "request_risk": request_risk,
            "supervisor_active": supervisor_active,
        }
    )
    if reasons:
        return CandidateEvaluation(False, None, evidence, tuple(sorted(reasons)))

    level_score = 0.6 if agent_level == "junior" else 1.0
    risk_score = 1.0 if request_risk == "low" else (0.8 if request_risk == "medium" else 0.6)
    score = round(0.35 + 0.20 * level_score + 0.20 * risk_score + 0.25 * spirit_score, 3)
    return CandidateEvaluation(True, score, evidence, ())
