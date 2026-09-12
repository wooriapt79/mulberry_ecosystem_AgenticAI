import pytest
from pydantic import ValidationError

from app.main import (
    ChatInput,
    ProposalFeedback,
    SessionLocal,
    build_luna_system_prompt,
    classify_proposal_feedback,
    proposal_summary_text,
    record_proposal_feedback,
)


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


def test_feedback_classification_separates_questions_and_update_requests():
    assert classify_proposal_feedback("예산 근거가 무엇인가요?") == ("budget", "question")
    assert classify_proposal_feedback("KPI 항목을 추가해 주세요") == ("kpi", "proposal_update")


def test_feedback_record_keeps_region_and_review_state():
    with SessionLocal() as db:
        feedback = record_proposal_feedback(
            db,
            page="wanju",
            source="chat",
            question="KPI 항목을 추가해 주세요",
            response="검토 후보로 접수합니다.",
        )
        assert feedback.region == "wanju"
        assert feedback.category == "kpi"
        assert feedback.request_type == "proposal_update"
        assert feedback.status == "received"
        db.delete(db.get(ProposalFeedback, feedback.id))
        db.commit()
