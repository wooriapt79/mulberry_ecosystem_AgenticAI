"""Verify that the configured database can downgrade to v0.2 and return to v0.3."""
import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

ROOT = Path(__file__).resolve().parents[1]
config = Config(str(ROOT / "alembic.ini"))
config.set_main_option("script_location", str(ROOT / "migrations"))
config.set_main_option("prepend_sys_path", str(ROOT))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{ROOT / 'open_reception.sqlite3'}")
os.environ.setdefault("DATABASE_URL", DATABASE_URL)
engine = create_engine(DATABASE_URL)


def columns(table: str) -> set[str]:
    return {column["name"] for column in inspect(engine).get_columns(table)}


command.upgrade(config, "head")
command.downgrade(config, "base")
assert "event_hash" not in columns("audit_events")
assert "status_reason" not in columns("human_passports")
assert "human_passport_status_history" not in inspect(engine).get_table_names()

command.upgrade(config, "head")
assert {"sequence", "previous_hash", "event_hash"} <= columns("audit_events")
assert {"status_reason", "status_changed_at"} <= columns("human_passports")
assert "human_passport_status_history" in inspect(engine).get_table_names()
with engine.connect() as connection:
    revision = connection.execute(text(
        "SELECT version_num FROM alembic_version"
    )).scalar_one()
assert revision == "0001_v03"
