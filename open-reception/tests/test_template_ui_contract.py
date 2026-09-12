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
