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
