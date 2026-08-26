from __future__ import annotations

import re

# Personal-info patterns — server-side rejection per security spec
_PII_PATTERNS = [
    re.compile(r"\b\d{2,3}-\d{3,4}-\d{4}\b"),          # phone numbers
    re.compile(r"\b[가-힣]{2,4}\s?\d{6}[-]\d{7}\b"),    # Korean resident number
    re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b"),  # email
]

# Keyword → domain mapping for rule-based routing
_DOMAIN_KEYWORDS: list[tuple[list[str], str]] = [
    (["식품", "먹거리", "밥", "급식", "농산물", "장보기"], "food-desert"),
    (["외로움", "혼자", "고립", "이웃", "친구", "말벗"], "membership-guidance"),
    (["홍천", "인제", "양양", "지역", "마을", "군청"], "reception"),
    (["AI", "인공지능", "에이전트", "서비스", "프로그램"], "reception"),
]


def contains_pii(text: str) -> bool:
    return any(p.search(text) for p in _PII_PATTERNS)


def _infer_domain(message: str) -> str:
    for keywords, domain in _DOMAIN_KEYWORDS:
        if any(kw in message for kw in keywords):
            return domain
    return "reception"


# Rule-based response templates (no LLM call in demo — DRY_RUN=true preserved)
_RESPONSES: dict[str, list[str]] = {
    "food-desert": [
        "안녕하세요! 저는 Luna입니다. 지역 먹거리 접근성 문제를 함께 고민하고 있어요. "
        "홍천·인제·양양 지역의 식품 사막화 현황과 Mulberry의 협력 방안을 말씀드릴 수 있습니다. "
        "더 구체적으로 어떤 부분이 궁금하신가요?",
    ],
    "membership-guidance": [
        "안녕하세요! Luna입니다. 외로움과 고립 문제는 정말 중요한 과제예요. "
        "Mulberry는 지역 커뮤니티 연결과 AI 말벗 서비스로 함께 해결책을 찾고 있습니다. "
        "어떤 도움이 필요하신지 편하게 말씀해 주세요.",
    ],
    "reception": [
        "안녕하세요! 저는 Mulberry AI 에이전트 Luna입니다. "
        "홍천·인제·양양 지역 주민 여러분의 생활 편의와 복지를 위해 활동하고 있어요. "
        "궁금하신 점이나 도움 요청 사항을 말씀해 주시면 최선을 다해 안내드리겠습니다.",
    ],
}


def generate_demo_reply(message: str) -> str:
    domain = _infer_domain(message)
    replies = _RESPONSES.get(domain, _RESPONSES["reception"])
    return replies[0]
