from datetime import datetime, timezone
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def test_existing_v02_database_upgrade_and_downgrade(tmp_path, monkeypatch):
    database = tmp_path / "legacy-v02.sqlite3"
    url = f"sqlite:///{database}"
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE human_passports (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR UNIQUE NOT NULL,
                display_name VARCHAR NOT NULL,
                domains JSON NOT NULL,
                status VARCHAR NOT NULL,
                policy_version VARCHAR NOT NULL,
                created_at DATETIME NOT NULL
            )
        """))
        connection.execute(text("""
            CREATE TABLE audit_events (
                id VARCHAR PRIMARY KEY,
                actor_id VARCHAR NOT NULL,
                action VARCHAR NOT NULL,
                target_type VARCHAR NOT NULL,
                target_id VARCHAR NOT NULL,
                detail JSON NOT NULL,
                created_at DATETIME NOT NULL
            )
        """))
        connection.execute(text("""
            INSERT INTO audit_events
            (id, actor_id, action, target_type, target_id, detail, created_at)
            VALUES
            ('legacy-event', 'system', 'legacy.created', 'system', 'legacy', '{}', :created_at)
        """), {"created_at": datetime(2026, 7, 25, tzinfo=timezone.utc)})

    monkeypatch.setenv("DATABASE_URL", url)
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    command.upgrade(config, "head")
    columns = {column["name"] for column in inspect(engine).get_columns("audit_events")}
    assert {"sequence", "previous_hash", "event_hash"} <= columns
    with engine.connect() as connection:
        migrated = connection.execute(text("""
            SELECT sequence, previous_hash, event_hash FROM audit_events
            WHERE id = 'legacy-event'
        """)).mappings().one()
        assert migrated["sequence"] == 1
        assert migrated["previous_hash"] == "0" * 64
        assert len(migrated["event_hash"]) == 64

    command.downgrade(config, "base")
    columns = {column["name"] for column in inspect(engine).get_columns("audit_events")}
    assert "event_hash" not in columns
    assert "status_reason" not in {
        column["name"] for column in inspect(engine).get_columns("human_passports")
    }
