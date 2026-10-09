import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config


test_db = Path(__file__).parent / "test.sqlite3"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{test_db}")
os.environ.setdefault("ADMIN_BOOTSTRAP_TOKEN", "bootstrap-token-for-tests-only-000000")
os.environ.setdefault("LOGIN_MAX_FAILURES", "3")

if os.environ["DATABASE_URL"].startswith("sqlite") and test_db.exists():
    test_db.unlink()


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    command.upgrade(config, "head")
    yield


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """각 테스트 후 slowapi in-memory 레이트리밋 카운터를 초기화한다.

    모듈 전역 limiter가 TestClient 간에 상태를 공유하므로,
    레이트리밋과 무관한 테스트가 429를 받아 실패하는 것을 방지한다.
    """
    yield
    try:
        from app.main import limiter
        storage = limiter._limiter.storage
        if hasattr(storage, "storage"):
            storage.storage.clear()
    except Exception:
        pass
