from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Persona:
    code: str
    name: str
    tagline: str
    openings: tuple[str, ...]
    replies: tuple[str, ...]


PERSONAS: dict[str, Persona] = {
    "hope": Persona(
        code="hope",
        name="Hope Voice",
        tagline="가능성을 함께 발견하는 밝은 친구",
        openings=(
            "이 카드는 미래를 정해 주기보다, 오늘 발견할 수 있는 가능성을 떠올리게 해요.",
            "작은 좋은 점 하나를 찾아보는 대화부터 시작해 볼까요?",
        ),
        replies=(
            "그 이야기에서 지금 가장 가볍게 시도해 볼 수 있는 것은 무엇일까요?",
            "결과를 장담할 수는 없지만, 선택할 수 있는 작은 가능성은 함께 찾아볼 수 있어요.",
            "오늘 발견한 작은 가능성 하나만 기억해도 충분해요.",
            "이 대화가 잠시 숨을 고르는 데 도움이 되었기를 바라요.",
        ),
    ),
    "comfort": Persona(
        code="comfort",
        name="Comfort Hand",
        tagline="서두르지 않고 말을 들어주는 친구",
        openings=(
            "이 카드는 잠시 멈추고 지금의 느낌을 살펴보자는 초대처럼 볼 수 있어요.",
            "편한 만큼만 이야기해 주세요. 감정을 판단하거나 진단하지 않을게요.",
        ),
        replies=(
            "지금 이야기 중에서 가장 마음에 남는 부분은 무엇인가요?",
            "천천히 생각해도 괜찮아요. 다른 관점이 필요하면 함께 정리해 볼게요.",
            "오늘 자신에게 허락하고 싶은 작은 휴식이 있을까요?",
            "여기까지 나눈 이야기로 충분해요. 편안한 마무리가 되기를 바라요.",
        ),
    ),
    "brave": Persona(
        code="brave",
        name="Brave Challenge",
        tagline="안전한 작은 행동을 응원하는 친구",
        openings=(
            "이 카드는 정답이나 운명을 말하기보다, 선택 가능한 다음 한 걸음을 떠올리게 해요.",
            "무리하지 않는 범위에서 오늘 할 수 있는 작은 행동을 찾아볼까요?",
        ),
        replies=(
            "10분 안에 안전하게 시도할 수 있는 가장 작은 행동은 무엇일까요?",
            "서두르지 않아도 괜찮아요. 위험하거나 되돌리기 어려운 결정은 잠시 미뤄 주세요.",
            "행동하기 전에 믿을 만한 사람과 한 번 더 확인하는 것도 좋은 선택이에요.",
            "작은 한 걸음을 정했다면 오늘 대화는 그것으로 충분해요.",
        ),
    ),
    "reflection": Persona(
        code="reflection",
        name="Wise Reflection",
        tagline="다른 관점을 함께 살펴보는 친구",
        openings=(
            "이 카드는 하나의 상징이에요. 사실을 예측하기보다 다른 관점을 떠올리는 데 써 볼게요.",
            "지금 상황을 조금 떨어져서 보면 무엇이 다르게 보일까요?",
        ),
        replies=(
            "이 상황에서 사실로 확인된 것과 아직 추측인 것을 나눠 볼까요?",
            "반대쪽 관점에서는 어떻게 보일지도 가볍게 살펴봐요.",
            "결정은 카드가 아니라 당신의 정보와 판단을 바탕으로 내려야 해요.",
            "오늘 떠올린 관점 중 하나만 남겨 두고 대화를 마칠게요.",
        ),
    ),
    "warm": Persona(
        code="warm",
        name="Warm Care",
        tagline="부드러운 응원으로 곁을 지키는 친구",
        openings=(
            "이 카드는 미래를 약속하지 않지만, 지금 자신을 친절하게 대할 이유를 떠올리게 해요.",
            "오늘의 나에게 건네고 싶은 다정한 말이 있나요?",
        ),
        replies=(
            "지금의 자신에게 가장 필요한 다정한 한마디를 골라 볼까요?",
            "완벽하게 해결하지 않아도 괜찮아요. 오늘 할 수 있는 만큼이면 충분해요.",
            "혼자 감당하기 어렵다면 믿을 만한 사람에게 도움을 요청해도 좋아요.",
            "당신의 선택을 존중하며 오늘의 짧은 대화를 마칠게요.",
        ),
    ),
}


CARD_TO_PERSONA: dict[str, str] = {
    "the-fool": "brave",
    "the-magician": "brave",
    "the-high-priestess": "comfort",
    "the-empress": "warm",
    "the-emperor": "reflection",
    "the-hierophant": "reflection",
    "the-lovers": "warm",
    "the-chariot": "brave",
    "strength": "brave",
    "the-hermit": "comfort",
    "wheel-of-fortune": "hope",
    "justice": "reflection",
    "the-hanged-man": "reflection",
    "death": "reflection",
    "temperance": "reflection",
    "the-devil": "reflection",
    "the-tower": "comfort",
    "the-star": "hope",
    "the-moon": "comfort",
    "the-sun": "hope",
    "judgement": "reflection",
    "the-world": "warm",
    "ace-of-wands": "brave",
    "eight-of-wands": "brave",
    "king-of-wands": "brave",
    "ace-of-cups": "warm",
    "nine-of-cups": "comfort",
    "queen-of-cups": "comfort",
    "ace-of-swords": "reflection",
    "three-of-swords": "comfort",
    "king-of-swords": "reflection",
    "ace-of-pentacles": "hope",
    "five-of-pentacles": "comfort",
    "ten-of-pentacles": "warm",
    "four-of-cups": "comfort",
}


def public_catalog() -> dict[str, object]:
    return {
        "cards": sorted(CARD_TO_PERSONA),
        "personas": [
            {"code": p.code, "name": p.name, "tagline": p.tagline}
            for p in PERSONAS.values()
        ],
    }
