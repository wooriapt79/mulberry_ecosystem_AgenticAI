import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import (
    ChatInput,
    ProposalFeedback,
    SessionLocal,
    app,
    build_luna_system_prompt,
    classify_proposal_feedback,
    csv_safe_cell,
    list_proposal_feedback,
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


def test_feedback_review_page_is_noindex_and_uses_session_only_token_storage():
    with TestClient(app) as client:
        response = client.get("/admin/proposal-feedback-review")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-robots-tag"] == "noindex, nofollow"
    assert "sessionStorage.getItem" in response.text
    assert "proposal_review_token" in response.text
    assert "localStorage" not in response.text
    assert "/api/proposal-feedback" in response.text
    assert "textContent" in response.text


def test_feedback_review_filters_keep_regions_and_update_requests_separate():
    created_ids = []
    with SessionLocal() as db:
        inje = record_proposal_feedback(
            db,
            page="inje",
            source="chat",
            question="예산 근거가 무엇인가요?",
            response="인제 답변",
        )
        wanju = record_proposal_feedback(
            db,
            page="wanju",
            source="file_analysis",
            question="KPI 항목을 추가해 주세요",
            response="완주 검토 후보",
        )
        created_ids.extend([inje.id, wanju.id])

        records = list_proposal_feedback(
            region="wanju",
            review_status="received",
            category="kpi",
            request_type="proposal_update",
            created_from=None,
            admin=None,
            db=db,
        )

        assert [item["id"] for item in records] == [wanju.id]
        assert records[0]["region"] == "wanju"
        assert records[0]["request_type"] == "proposal_update"

        for feedback_id in created_ids:
            db.delete(db.get(ProposalFeedback, feedback_id))
        db.commit()


def test_first_account_setup_page_keeps_credentials_out_of_source_and_storage():
    with TestClient(app) as client:
        response = client.get("/admin/first-account-setup")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["pragma"] == "no-cache"
    assert response.headers["x-robots-tag"] == "noindex, nofollow"
    assert "/auth/bootstrap" in response.text
    assert "ADMIN_BOOTSTRAP_TOKEN" in response.text
    assert "localStorage" not in response.text
    assert "sessionStorage" not in response.text
    assert "chongchongsaigon" not in response.text


def test_feedback_review_discards_superseded_filters_and_reports_failed_updates():
    with TestClient(app) as client:
        response = client.get("/admin/proposal-feedback-review")

    assert response.status_code == 200
    assert "AbortController" in response.text
    assert "feedbackRequestSequence" in response.text
    assert "controller.signal" in response.text
    assert "상태가 저장되지 않았습니다." in response.text


def test_feedback_review_phase_two_controls_are_present_and_text_safe():
    with TestClient(app) as client:
        response = client.get("/admin/proposal-feedback-review")

    assert response.status_code == 200
    assert "담당자 검토 메모" in response.text
    assert "Human 연결 요청" in response.text
    assert "제안서 반영 후보만" in response.text
    assert "/api/proposal-feedback/export" in response.text
    assert "textContent" in response.text
    assert "innerHTML" not in response.text


def test_csv_export_neutralizes_spreadsheet_formulas():
    for value in ("=1+1", "+cmd", "-2+3", "@SUM(A1:A2)", "  =HYPERLINK('x')", "\t=1"):
        assert csv_safe_cell(value).startswith("'")

    assert csv_safe_cell("일반 질의") == "일반 질의"
    assert csv_safe_cell(None) == ""


def test_workflow_changes_send_only_dirty_notes_and_preserve_filter_drafts():
    with TestClient(app) as client:
        response = client.get("/admin/proposal-feedback-review")

    assert response.status_code == 200
    assert "const noteDrafts=new Map()" in response.text
    assert "if(draft&&draft.dirty)" in response.text
    assert "payload.review_revision=draft.baseRevision" in response.text
    assert "noteDrafts.delete(id)" in response.text
    assert "noteDrafts.clear()" in response.text
    assert "function isActiveSession(requestToken)" in response.text
    assert "if(!isActiveSession(requestToken))return;" in response.text
    assert "finally{if(isActiveSession(requestToken))showLogin" in response.text
    assert "authHeaders({},requestToken)" in response.text
    assert "let loginRequestSequence=0;" in response.text
    assert "if(requestSequence!==loginRequestSequence)return;" in response.text
    blob_read = response.text.index("const blob=await response.blob();")
    assert blob_read >= 0
    assert response.text.index("if(!isActiveSession(requestToken))return;", blob_read) > blob_read
    assert "catch(error){if(isActiveSession(requestToken))setError(error.message)}" in response.text
    assert "finally{if(isActiveSession(requestToken))button.disabled=false}" in response.text
    assert "existingDraft.baseRevision=record.review_revision" in response.text
    assert "currentDraft.value===submittedDraft.value" in response.text
    assert "currentDraft.baseRevision=savedRecord.review_revision" in response.text
    assert "다른 검토자의 최신 메모:" in response.text
    assert "{status:next,reviewer_note:note.value}" not in response.text
    assert "{escalation_status:next,reviewer_note:note.value}" not in response.text
    assert "작성 중인 초안은 유지됐습니다." in response.text
