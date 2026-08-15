import ast
import base64
import json
from pathlib import Path

from app.engine import start_session

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
FORBIDDEN_IMPORTS = {
    "alembic",
    "anthropic",
    "google",
    "httpx",
    "openai",
    "psycopg",
    "redis",
    "requests",
    "sqlalchemy",
}
FORBIDDEN_BROWSER_STORAGE = (
    "document.cookie",
    "localStorage",
    "sessionStorage",
    "indexedDB",
)


def _python_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
    return imports


def test_runtime_has_no_database_external_ai_or_http_client_imports():
    imports: set[str] = set()
    for path in APP.rglob("*.py"):
        imports |= _python_imports(path)
    assert imports.isdisjoint(FORBIDDEN_IMPORTS)


def test_browser_does_not_use_persistent_storage_or_absolute_api_urls():
    javascript = (APP / "static" / "app.js").read_text(encoding="utf-8")
    assert all(name not in javascript for name in FORBIDDEN_BROWSER_STORAGE)
    assert "fetch('http://" not in javascript
    assert 'fetch("http://' not in javascript
    assert "fetch('https://" not in javascript
    assert 'fetch("https://' not in javascript


def test_signed_session_contains_only_minimum_nonpersonal_fields():
    token = start_session("judgement", "reflection", now=1_000)["session"]
    body = token.split(".", 1)[0]
    payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
    assert set(payload) == {"card", "persona", "turn", "issued_at"}
    assert "message" not in payload
    assert "user" not in payload
    assert "name" not in payload


def test_service_is_not_wired_into_root_compose():
    compose = (ROOT.parent / "docker-compose.yml").read_text(encoding="utf-8")
    assert "special-reception:" not in compose
