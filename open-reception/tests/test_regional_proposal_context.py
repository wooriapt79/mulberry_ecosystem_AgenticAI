import pytest
from pydantic import ValidationError

from app.main import ChatInput, build_luna_system_prompt, proposal_summary_text


def test_chat_input_accepts_only_supported_regions():
    assert ChatInput(message="예산은?", page="inje").page == "inje"
    assert ChatInput(message="실증 지역은?", page="wanju").page == "wanju"

    with pytest.raises(ValidationError):
        ChatInput(message="질문", page="other")


def test_inje_prompt_uses_completed_inje_summary():
    prompt = build_luna_system_prompt("inje")

    assert "현재 질의 대상은 인제군" in prompt
    assert "완료 제안서 서머리" in prompt
    assert "기린면·북면" in prompt
    assert "완주군만의 AI" not in prompt


def test_wanju_prompt_uses_consultation_draft_without_inje_copy_artifacts():
    prompt = build_luna_system_prompt("wanju")

    assert "현재 질의 대상은 완주군" in prompt
    assert "의견수렴 초안" in prompt
    assert "딸기 · 포도 · 인삼" in prompt
    assert "곰취 · 황태" not in prompt
    assert "처음부터 인제를 기억합니다" not in prompt


def test_summary_extractor_ignores_script_and_style_content():
    summary = proposal_summary_text("wanju")

    assert "AI Wanju 2030" in summary
    assert "function openCh" not in summary
    assert "@media" not in summary
