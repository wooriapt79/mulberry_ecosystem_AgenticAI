from fastapi.testclient import TestClient

from app.main import app, prepare_public_html


FORBIDDEN_PUBLIC_MARKERS = (
    "anthropic",
    "claude",
    "api.anthropic.com",
)


def test_public_html_strips_development_notes_and_compacts_assets():
    source = """
    <!-- TRANG: internal deployment note -->
    <style>
      /* TODO: tune layout */
      .card { color: red; padding: 1rem; }
    </style>
    <script>
      // KODA: temporary diagnostic
      const label = "public";

      window.label = label;
    </script>
    <main>Public content</main>
    """

    public = prepare_public_html(source)

    assert "<!--" not in public
    assert "TRANG" not in public
    assert "TODO" not in public
    assert "KODA" not in public
    assert ".card{color:red;padding:1rem;}" in public
    assert '\n\n' not in public
    assert "Public content" in public


def test_reception_html_does_not_expose_provider_implementation():
    with TestClient(app) as client:
        for path in ("/inje", "/wanju"):
            response = client.get(path)
            assert response.status_code == 200
            lowered = response.text.lower()
            assert "<!--" not in lowered
            for marker in FORBIDDEN_PUBLIC_MARKERS:
                assert marker not in lowered


def test_unavailable_service_responses_are_provider_neutral(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with TestClient(app) as client:
        chat = client.post("/api/chat", json={"message": "질문", "page": "inje"})
        analysis = client.post(
            "/api/analyze-file",
            data={"page": "inje"},
            files={"file": ("note.txt", b"test", "text/plain")},
        )

    assert chat.status_code == 200
    assert analysis.status_code == 200
    for payload in (chat.json(), analysis.json()):
        public_text = str(payload).lower()
        assert "api 키" not in public_text
        for marker in FORBIDDEN_PUBLIC_MARKERS:
            assert marker not in public_text
