"""Kakao Skill Server webhook handler — Issue #143.

POST /kakao/webhook

카카오 채널 타로 결과 후 흐름:
  타로 결과 → [🔄 다시 뽑기] [💬 AI 친구와 이야기하기]
  → 페르소나 선택 (quickReply 5개)
  → 5턴 채팅 (세션 토큰을 clientExtra로 전달)
  → DANGER_KEYWORDS 감지 → 위기 안내 + 세션 종료

KeBin 안전 원칙: 예언·진단 단정 금지, 무저장·무외부전송, Phase A 직접 선택
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from .engine import SessionError, continue_session, start_session

router = APIRouter(prefix="/kakao", tags=["kakao"])

# ────────────────────────────────────────────────────────────────
# 상수
# ────────────────────────────────────────────────────────────────
DANGER_KEYWORDS = [
    "죽고 싶", "끝내버리고 싶", "살아있는 게 의미없",
    "폐를 끼쳐", "아무도 날 원하지 않", "자해", "자살",
]

CRISIS_TEXT = (
    "지금 많이 힘드시죠.\n"
    "전문 상담사와 이야기해보세요.\n"
    "📞 자살예방상담전화: 1393 (24시간)\n"
    "📞 정신건강 위기상담: 1577-0199"
)

PERSONA_CHOICES = [
    {"label": "🌟 Hope Voice", "code": "hope",       "desc": "밝고 희망차게"},
    {"label": "💙 Comfort Hand", "code": "comfort",   "desc": "따뜻하게 위로"},
    {"label": "⚡ Brave Challenge", "code": "brave",  "desc": "도전하고 싶을 때"},
    {"label": "🌙 Wise Reflection", "code": "reflection", "desc": "깊이 생각하고 싶을 때"},
    {"label": "💕 Warm Care",   "code": "warm",       "desc": "그냥 곁에 있어줄 친구"},
]


# ────────────────────────────────────────────────────────────────
# Kakao 응답 헬퍼
# ────────────────────────────────────────────────────────────────
def _text_response(text: str, quick_replies: list[dict] | None = None) -> dict:
    """카카오 simpleText 응답 포맷."""
    response: dict = {
        "version": "2.0",
        "template": {
            "outputs": [{"simpleText": {"text": text}}],
        },
    }
    if quick_replies:
        response["template"]["quickReplies"] = quick_replies
    return response


def _quick_reply(label: str, action: str = "message", message: str | None = None,
                 extra: dict | None = None) -> dict:
    qr: dict = {"label": label, "action": action}
    if message:
        qr["messageText"] = message
    if extra:
        qr["extra"] = extra
    return qr


def _is_danger(text: str) -> bool:
    return any(kw in text for kw in DANGER_KEYWORDS)


# ────────────────────────────────────────────────────────────────
# 타로 결과 → 버튼 2개 응답 (외부에서 호출)
# ────────────────────────────────────────────────────────────────
def tarot_result_buttons(card_code: str) -> dict:
    """타로 결과 후 호출. 다시뽑기 + AI 친구 버튼 2개 반환."""
    return _text_response(
        "카드 해석이 완료됐어요 ✨\n어떻게 할까요?",
        quick_replies=[
            _quick_reply("🔄 다시 뽑기",   message="다시 뽑기"),
            _quick_reply("💬 AI 친구와 이야기하기",
                         message="AI 친구와 이야기하기",
                         extra={"card": card_code}),
        ],
    )


# ────────────────────────────────────────────────────────────────
# Webhook 엔드포인트
# ────────────────────────────────────────────────────────────────
@router.post("/webhook")
async def kakao_webhook(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid JSON")

    # 발화문과 clientExtra 추출
    action = body.get("action", {})
    user_request = body.get("userRequest", {})
    utterance: str = user_request.get("utterance", "").strip()
    extra: dict = action.get("clientExtra") or {}

    # ── 위험 신호 최우선 감지 ──────────────────────────────────
    if _is_danger(utterance):
        return JSONResponse(_text_response(CRISIS_TEXT))

    # ── AI 친구와 이야기하기 → 페르소나 선택 화면 ──────────────
    if utterance == "AI 친구와 이야기하기" or extra.get("show_persona_select"):
        card_code = extra.get("card", "the-fool")
        qrs = [
            _quick_reply(
                p["label"],
                message=p["label"],
                extra={"card": card_code, "persona": p["code"], "action": "start_chat"},
            )
            for p in PERSONA_CHOICES
        ]
        return JSONResponse(_text_response(
            "어떤 친구와 이야기하고 싶으세요? 💫\n\n"
            + "\n".join(f"{p['label']} — {p['desc']}" for p in PERSONA_CHOICES),
            quick_replies=qrs,
        ))

    # ── 페르소나 선택 → 세션 시작 (Turn 1) ────────────────────
    if extra.get("action") == "start_chat":
        card_code = extra.get("card", "the-fool")
        persona_code = extra.get("persona", "hope")
        try:
            result = start_session(card_code, persona_code)
        except SessionError as exc:
            return JSONResponse(_text_response(f"오류가 발생했어요: {exc}"))

        reply = result["reply"]
        session_token = result["session"]
        persona_name = result["persona"]["name"]
        return JSONResponse(_text_response(
            f"[{persona_name}] Turn 1/5\n\n{reply}",
            quick_replies=[
                _quick_reply("다음 →", message="다음",
                             extra={"session": session_token, "action": "chat"}),
            ],
        ))

    # ── 진행 중 채팅 (Turn 2~5) ────────────────────────────────
    if extra.get("action") == "chat":
        session_token = extra.get("session", "")
        message = utterance if utterance not in {"다음"} else "(계속)"
        try:
            result = continue_session(session_token, message)
        except SessionError as exc:
            err = str(exc)
            if err in {"session complete", "expired session"}:
                return JSONResponse(_text_response(
                    "오늘 대화 고마워요 💙 언제든 또 와요!\n\n"
                    "⚠️ 이 대화는 재미와 자기성찰을 위한 익명 체험이며 예언·진단·상담 서비스가 아닙니다."
                ))
            return JSONResponse(_text_response(f"오류가 발생했어요: {err}"))

        reply = result["reply"]
        turn = result["turn"]
        complete = result["complete"]
        safety_route = result.get("safety_route")

        if safety_route == "high_risk":
            return JSONResponse(_text_response(CRISIS_TEXT))

        if complete:
            return JSONResponse(_text_response(
                f"[Turn {turn}/5]\n\n{reply}\n\n"
                "오늘 대화 고마워요 💙 언제든 또 와요!\n\n"
                "⚠️ 이 대화는 재미와 자기성찰을 위한 익명 체험이며 예언·진단·상담 서비스가 아닙니다.",
                quick_replies=[
                    _quick_reply("💬 다른 친구 만나기", message="AI 친구와 이야기하기",
                                 extra={"show_persona_select": True}),
                ],
            ))

        next_token = result["session"]
        remaining = result["remaining_turns"]
        return JSONResponse(_text_response(
            f"[Turn {turn}/5]\n\n{reply}",
            quick_replies=[
                _quick_reply(f"다음 → (남은 {remaining}턴)", message="다음",
                             extra={"session": next_token, "action": "chat"}),
            ],
        ))

    # ── 기본: 타로 시작 안내 ───────────────────────────────────
    return JSONResponse(_text_response(
        "타로 카드를 뽑은 후 'AI 친구와 이야기하기'를 눌러주세요 🔮"
    ))
