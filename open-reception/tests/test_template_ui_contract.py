from pathlib import Path


TEMPLATES = (
    Path(__file__).parents[1] / "app" / "templates" / "luna_site_renewal_white_ko_en.html",
    Path(__file__).parents[1] / "app" / "templates" / "luna_site_renewal_white_wanju.html",
)


def test_column_menu_has_a_single_toggle_implementation():
    for template in TEMPLATES:
        html = template.read_text(encoding="utf-8")
        assert html.count("function toggleSubNav") == 1
        assert html.count('onclick="toggleSubNav(this)"') == 1
        assert 'aria-expanded="false"' in html


def test_hero_pillars_are_text_only_and_keep_the_origin_statement():
    for template in TEMPLATES:
        html = template.read_text(encoding="utf-8")
        assert 'class="hs-icon"' not in html
        assert html.count("이것이 우리의 모든 것의 시작이야.") == 1
        expected_initiative = (
            "AI Inje Initiative — 인제만의 AI와 AI Agent 경제 플랫폼."
            if template.name == "luna_site_renewal_white_ko_en.html"
            else "AI Wanju Initiative — 완주만의 AI와 AI Agent 경제 플랫폼."
        )
        assert html.count(expected_initiative) == 1
        for title in ("농업·식품", "복지·의료", "안전·포렌식", "공동구매", "AI 에이전트"):
            assert title in html



def test_chat_save_control_is_text_only_visible_and_session_backed():
    for template in TEMPLATES:
        html = template.read_text(encoding="utf-8")
        assert 'id="qaSaveBar" style="display:flex' in html
        assert 'id="qaSaveBtn" onclick="saveChatLog()" disabled' in html
        assert "현재 대화 저장" in html
        assert "💾 대화 저장" not in html
        assert "💾 다시 저장" not in html
        assert "'luna_chat_session_' + _chatPage" in html
        assert "restoreChatSession();" in html


def test_file_analysis_calls_backend_with_the_active_region():
    for template in TEMPLATES:
        html = template.read_text(encoding="utf-8")
        assert "fetch('/api/analyze-file'" in html
        assert "formData.append('page', window.location.pathname.includes('wanju') ? 'wanju' : 'inje')" in html
        assert "(백엔드 API 연동 후 구현)" not in html


def test_summary_mobile_toc_does_not_clear_the_visible_chapter():
    static_dir = Path(__file__).parents[1] / "app" / "static"
    for name in ("inje_proposal_summary_toc_v2.html", "wanju_proposal_summary_toc_v2.html"):
        html = (static_dir / name).read_text(encoding="utf-8")
        toc_guard = "if (id === 'toc')"
        assert toc_guard in html
        assert html.index(toc_guard) < html.index("document.querySelectorAll('article')")
        assert "link.classList.toggle('active'" in html


def test_region_specific_hero_copy_does_not_cross_regions():
    inje = TEMPLATES[0].read_text(encoding="utf-8")
    wanju = TEMPLATES[1].read_text(encoding="utf-8")
    assert "AI Wanju Initiative — 완주만의 AI와 AI Agent 경제 플랫폼." not in inje
    assert "AI Inje Initiative — 인제만의 AI와 AI Agent 경제 플랫폼." not in wanju


def test_mobile_report_output_uses_vertical_visible_layout():
    for template in TEMPLATES:
        html = template.read_text(encoding="utf-8")
        assert 'class="report-output-panel"' in html
        assert "#sec-report {\n    flex-direction: column;" in html
        assert ".report-output-panel {\n    flex: 0 0 auto !important;" in html
        assert ".report-preview {\n    flex: 0 0 auto;\n    overflow: visible;" in html
        assert "requestAnimationFrame(() =>" in html


def test_chat_answers_use_safe_structured_renderer():
    for template in TEMPLATES:
        html = template.read_text(encoding="utf-8")
        assert "function normalizeChatText(raw)" in html
        assert "function renderChatContent(container, raw)" in html
        assert "function createChatMessage(role, content)" in html
        assert "appendChatInline(title, heading[1])" in html
        assert "document.createElement(nextType)" in html
        assert '<div class="msg-bub">${html}</div>' not in html
        assert ".msg-bub .msg-section-title" in html
        assert ".msg-bub p { margin: 0 0 10px; }" in html


def test_sidebar_is_compact_and_team_footer_is_text_only():
    for template in TEMPLATES:
        html = template.read_text(encoding="utf-8")
        assert "width: 190px; height: 190px;" in html
        assert "overflow-y: auto; min-height: 150px;" in html
        assert 'class="team-members-text">Luna · Trang · KODA · FAMA</div>' in html
        assert 'class="team-pill ' not in html
        assert 'href="/static/mulberry_lab_team_directory_v2.html"' in html


def test_team_directory_uses_municipal_language_and_no_external_font():
    directory = Path(__file__).parents[1] / "app" / "static" / "mulberry_lab_team_directory_v2.html"
    html = directory.read_text(encoding="utf-8")
    assert "지자체 프로젝트 운영 팀" in html
    assert "지자체 제안·Q&amp;A·운영 지원" in html
    assert "지자체 Open Reception 실시간 Q&amp;A 담당" in html
    assert "인제 회의 핵심 팀" not in html
    assert "외부 연구 파트너" not in html
    assert "공식 제휴 관계를 뜻하지 않습니다." in html
    assert "cdn.jsdelivr.net" not in html
