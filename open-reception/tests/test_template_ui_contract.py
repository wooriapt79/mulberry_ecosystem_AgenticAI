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


def test_inje_proposal_library_has_explicit_public_documents():
    html = TEMPLATES[0].read_text(encoding="utf-8")
    assert 'id="proposalLibrary"' in html
    assert "function openProposalLibrary()" in html
    assert 'href="/static/AI_Inje_Initiative_Summary_v15.pdf"' in html
    assert 'href="/static/AI%20Inje%20Initiative.pdf"' in html
    assert html.count("PDF 다운로드") == 2
    assert "자료 보기·다운로드" in html


def test_wanju_does_not_expose_inje_documents():
    html = TEMPLATES[1].read_text(encoding="utf-8")
    assert "제안서 준비 중 · Q&A 반영 후 공개" in html
    assert "AI_Inje_Initiative_Summary_v15.pdf" not in html
    assert "AI%20Inje%20Initiative.pdf" not in html
    assert 'id="proposalLibrary"' not in html


def test_summary_pages_do_not_repeat_global_footer_navigation():
    static_dir = Path(__file__).parents[1] / "app" / "static"
    for name in ("inje_proposal_summary_toc_v2.html", "wanju_proposal_summary_toc_v2.html"):
        html = (static_dir / name).read_text(encoding="utf-8")
        assert f'<p class="ver">{name}</p>' not in html
        article_count = html.count("<article ")
        assert html.count("onclick=\"openCh('toc')\"") == article_count


def test_kebin_economy_column_is_linked_per_municipality():
    inje = TEMPLATES[0].read_text(encoding="utf-8")
    wanju = TEMPLATES[1].read_text(encoding="utf-8")
    path = "/static/agent_kebin_municipal_economy_v1.html"
    assert path + "?from=inje" in inje
    assert path + "?from=wanju" in wanju
    assert path + "?from=wanju" not in inje
    assert path + "?from=inje" not in wanju


def test_kebin_economy_column_defines_new_terms_with_caveats():
    column = Path(__file__).parents[1] / "app" / "static" / "agent_kebin_municipal_economy_v1.html"
    html = column.read_text(encoding="utf-8")
    for term in ("AI Agent 경제", "토큰경제", "지역 토크나이저", "Local AI Credit", "Human Approval"):
        assert term in html
    assert "공식 경제학 용어나 금융상품 명칭이 아니라" in html
    assert "투자성·가격상승을 전제로 하지 않습니다" in html
    assert "개인정보가 불필요한 제안 Q&amp;A" not in html
    assert "개인정보가 불필요한 제안 Q&A" in html


def test_column_menu_lists_arka_and_kebin_once():
    for template in TEMPLATES:
        html = template.read_text(encoding="utf-8")
        assert html.count('class="sub-nav-item"') == 2
        assert html.count("Arka Column <small") == 1
        assert html.count("KeBin Column <small") == 1
        assert "AI 경제와 Agent Venture" in html
        assert "AI 시대의 지자체 경제용어" in html


def test_arka_columns_use_standard_mobile_navigation():
    static_dir = Path(__file__).parents[1] / "app" / "static"
    for name in ("agent_venture_arka_v2.html", "agent_wanju_venture_arka_v2.html"):
        html = (static_dir / name).read_text(encoding="utf-8")
        assert 'class="menu" id="menuBtn"' in html
        assert "right: 16px; bottom: 16px;" in html
        assert "width: 46px; height: 46px;" in html
        assert "border: 0; border-radius: 50%;" in html
        assert "width: 280px; z-index: 960;" in html
        assert "body.nav-open aside.rail { left: 0; }" in html
        assert "function toggleNav()" in html
        assert "event.key === 'Escape'" in html
        assert 'class="ham-btn"' not in html


def test_inje_proposal_library_panel_has_opaque_white_background():
    html = TEMPLATES[0].read_text(encoding="utf-8")
    panel_css = html.split(".proposal-library-panel {", 1)[1].split("}", 1)[0]
    assert "background: #ffffff;" in panel_css
    assert "background: var(--bg-primary);" not in panel_css


def test_luna_opens_capability_panel_with_current_scope():
    for template in TEMPLATES:
        html = template.read_text(encoding="utf-8")
        assert 'id="capabilityModal"' in html
        assert html.count("openCapabilityPanel()") >= 3
        assert "Open Reception 기능 보기" in html
        assert "지자체 제안서 Q&amp;A 리셉션" in html
        assert "설계된 확장 기능" in html
        assert "나머지 기능은 지자체 협의와 운영 승인에 따라" in html
        assert ".capability-panel {" in html
        assert "background: #ffffff;" in html


def test_capability_panel_remains_accessible_when_luna_card_is_hidden_on_mobile():
    for template in TEMPLATES:
        html = template.read_text(encoding="utf-8")
        assert ".luna-card { display: none !important; }" in html
        assert 'class="nav-item mobile-capability-item"' in html
        assert ".mobile-capability-item { display: none; }" in html
        assert ".mobile-capability-item { display: flex; }" in html


def test_mobile_menu_button_and_proposal_divider_are_clear():
    for template in TEMPLATES:
        html = template.read_text(encoding="utf-8")
        assert "width: 44px; height: 44px;" in html
        assert "font-size: 28px; cursor: pointer;" in html
        proposal_css = html.split(".proposal-section {", 1)[1].split("}", 1)[0]
        assert "padding: 8px 0 32px;" in proposal_css
        assert "border-bottom: 1px solid #d1d5db;" in proposal_css


def test_team_directory_home_link_returns_to_source_municipality():
    inje = TEMPLATES[0].read_text(encoding="utf-8")
    wanju = TEMPLATES[1].read_text(encoding="utf-8")
    assert 'href="/static/mulberry_lab_team_directory_v2.html?from=inje"' in inje
    assert 'href="/static/mulberry_lab_team_directory_v2.html?from=wanju"' in wanju
    assert "?from=wanju" not in inje
    assert "?from=inje" not in wanju

    directory = Path(__file__).parents[1] / "app" / "static" / "mulberry_lab_team_directory_v2.html"
    html = directory.read_text(encoding="utf-8")
    assert 'id="directoryHomeLink" href="/inje">메인 홈</a>' in html
    assert "sourcePage === 'wanju' ? '/wanju' : '/inje'" in html
