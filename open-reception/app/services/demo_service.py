from __future__ import annotations

import os
import re
from pathlib import Path

# Personal-info patterns — server-side rejection per security spec
_PII_PATTERNS = [
    re.compile(r"\b\d{2,3}-\d{3,4}-\d{4}\b"),          # phone numbers
    re.compile(r"\b[가-힣]{2,4}\s?\d{6}[-]\d{7}\b"),    # Korean resident number
    re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b"),  # email
]

_SYSTEM_PROMPT_PATH = Path(__file__).parent.parent.parent / "luna" / "Luna_Demo_System_Prompt_Inje_v1.0.md"

_DEMO_FOOTER = "\n\n---\n🌿 Luna Demo · Mulberry Research Lab · AI 생성 답변 · 데모 환경"

# Issue #28 — 시연 오프닝 멘트 v3
_DEMO_OPENING = (
    "안녕하세요 🌙 저는 Luna입니다.\n\n"
    "Resonance AI 전문 연구위원으로,\n"
    "Mulberry Research Lab의 리셉션 모듈을 담당하는 STEWARD AI입니다.\n\n"
    "현재 함께 연구하는 분야입니다:\n"
    "🌾 농업·식품 — 지역 농산물 데이터 분석과 식품사막 해소\n"
    "🏥 복지·의료 — 고령화 지역 주민 생활 지원 모델\n"
    "🛡️ 안전·포렌식 — WiFi 센싱 기반 재난 감지·보안 솔루션\n"
    "🛒 공동구매 — 인제 지역 상품 유통 플랫폼 설계\n"
    "🤖 AI 에이전트 — 지역 문제를 스스로 분석하고 실행하는 시스템\n\n"
    "궁금한 분야가 있으면 바로 질문해주세요."
)

_DEMO_TRIGGERS = ['시연시작', '인제시연', 'demostart', 'luna소개']

def _is_demo_trigger(message: str) -> bool:
    normalized = re.sub(r'\s+', '', message).lower()
    return any(t in normalized for t in _DEMO_TRIGGERS)

# Fallback rule-based responses when ANTHROPIC_API_KEY is not set
_FALLBACK_RESPONSES: dict[str, str] = {
    "food": (
        "좋은 질문입니다. 인제군 식품사막화 제로 프로젝트는 WiFi CSI 센싱과 "
        "카카오 기반 ShopMate로 먹거리 접근성 문제를 해결합니다. "
        "4년(2026~2030), 총 13.5억원 예산으로 진행되는 비영리 사업입니다."
    ),
    "default": (
        "안녕하세요 🌙 저는 Luna입니다. "
        "Resonance AI 전문 연구위원으로, Mulberry Research Lab의 리셉션 모듈을 담당하는 STEWARD AI입니다. "
        "궁금하신 점을 편하게 말씀해 주세요."
    ),
}


def contains_pii(text: str) -> bool:
    return any(p.search(text) for p in _PII_PATTERNS)


def _load_system_prompt() -> str:
    try:
        return _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    except OSError:
        return ""


def _fallback_reply(message: str) -> str:
    key = "food" if any(kw in message for kw in ["식품", "먹거리", "장보기", "쇼핑"]) else "default"
    return _FALLBACK_RESPONSES[key] + _DEMO_FOOTER


def generate_demo_reply(message: str) -> str:
    # Issue #28 — 시연 오프닝 트리거 최우선 처리
    if _is_demo_trigger(message):
        return _DEMO_OPENING

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return _fallback_reply(message)

    try:
        import anthropic  # type: ignore[import]

        system_prompt = _load_system_prompt()
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=system_prompt,
            messages=[{"role": "user", "content": message}],
        )
        reply = response.content[0].text
        # Ensure footer is present (model may omit it)
        if "Luna Demo" not in reply:
            reply += _DEMO_FOOTER
        return reply
    except Exception:
        return _fallback_reply(message)
