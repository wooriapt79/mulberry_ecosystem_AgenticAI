"""v0.3 data and append-only audit controls

Revision ID: 0001_v03
"""
from alembic import op
from datetime import timezone
import hashlib
import json
import sqlalchemy as sa
from uuid import uuid4

revision = "0001_v03"
down_revision = None
branch_labels = None
depends_on = None


def _columns(inspector, table):
    return {column["name"] for column in inspector.get_columns(table)}


def _utc(value):
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _create_empty_database_baseline(bind):
    """Create the frozen v0.2 schema when upgrading an empty database."""
    metadata = sa.MetaData()
    users = sa.Table(
        "users", metadata,
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("disabled", sa.Boolean(), nullable=False),
        sa.Column("failed_login_count", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    sa.Table(
        "bootstrap_consumptions", metadata,
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("consumed_by", sa.String(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=False),
    )
    sa.Table(
        "sessions", metadata,
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey(users.c.id), nullable=False, index=True),
        sa.Column("token_hash", sa.String(), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_by", sa.String()),
        sa.Column("revoke_reason", sa.String()),
    )
    passports = sa.Table(
        "human_passports", metadata,
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey(users.c.id), nullable=False, unique=True),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("domains", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("policy_version", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    sa.Table(
        "steward_human_applications", metadata,
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey(users.c.id), nullable=False, index=True),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("statement", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("reviewed_by", sa.String()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
    )
    sa.Table(
        "ai_passports", metadata,
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("level", sa.String(), nullable=False),
        sa.Column("domains", sa.JSON(), nullable=False),
        sa.Column("permissions", sa.JSON(), nullable=False),
        sa.Column("spirit_score", sa.Float(), nullable=False),
        sa.Column("mentor_agent", sa.String()),
        sa.Column("origin_agent", sa.String()),
        sa.Column("status", sa.String(), nullable=False),
    )
    sa.Table(
        "matching_requests", metadata,
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("requester_id", sa.String(), sa.ForeignKey(users.c.id), nullable=False, index=True),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("risk", sa.String(), nullable=False),
        sa.Column("required_permissions", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("approved_by", sa.String()),
    )
    sa.Table(
        "audit_events", metadata,
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("actor_id", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("target_type", sa.String(), nullable=False),
        sa.Column("target_id", sa.String(), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    sa.Table(
        "kill_switches", metadata,
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("changed_by", sa.String(), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
    )
    metadata.create_all(bind)
    return passports


def upgrade():
    bind = op.get_bind()
    # Supports both an empty database and an existing v0.2 create_all database
    # without importing mutable application metadata into migration history.
    _create_empty_database_baseline(bind)
    inspector = sa.inspect(bind)
    passport_columns = _columns(inspector, "human_passports")
    with op.batch_alter_table("human_passports") as batch:
        if "status_reason" not in passport_columns:
            batch.add_column(sa.Column("status_reason", sa.String(), nullable=True))
        if "status_changed_at" not in passport_columns:
            batch.add_column(sa.Column("status_changed_at", sa.DateTime(timezone=True), nullable=True))
    inspector = sa.inspect(bind)
    if "human_passport_status_history" not in inspector.get_table_names():
        op.create_table(
            "human_passport_status_history",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("passport_id", sa.String(), sa.ForeignKey("human_passports.id"), nullable=False),
            sa.Column("from_status", sa.String()),
            sa.Column("to_status", sa.String(), nullable=False),
            sa.Column("reason", sa.String(), nullable=False),
            sa.Column("changed_by", sa.String(), nullable=False),
            sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(
            "ix_human_passport_status_history_passport_id",
            "human_passport_status_history", ["passport_id"],
        )
    passports = sa.table(
        "human_passports",
        sa.column("id", sa.String()),
        sa.column("status", sa.String()),
        sa.column("status_changed_at", sa.DateTime(timezone=True)),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    passport_history = sa.table(
        "human_passport_status_history",
        sa.column("id", sa.String()),
        sa.column("passport_id", sa.String()),
        sa.column("from_status", sa.String()),
        sa.column("to_status", sa.String()),
        sa.column("reason", sa.String()),
        sa.column("changed_by", sa.String()),
        sa.column("changed_at", sa.DateTime(timezone=True)),
    )
    for passport in bind.execute(sa.select(passports)).mappings():
        changed_at = _utc(passport["created_at"])
        bind.execute(
            passports.update().where(passports.c.id == passport["id"]).values(
                status_changed_at=changed_at,
            )
        )
        existing_history = bind.execute(
            sa.select(passport_history.c.id).where(
                passport_history.c.passport_id == passport["id"]
            )
        ).first()
        if not existing_history:
            bind.execute(passport_history.insert().values(
                id=str(uuid4()),
                passport_id=passport["id"],
                from_status=None,
                to_status=passport["status"],
                reason="migration backfill",
                changed_by="system:migration",
                changed_at=changed_at,
            ))
    with op.batch_alter_table("human_passports") as batch:
        batch.alter_column(
            "status_changed_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
        )
    if "audit_chain_heads" not in inspector.get_table_names():
        op.create_table(
            "audit_chain_heads",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("sequence", sa.Integer(), nullable=False),
            sa.Column("event_hash", sa.String(64), nullable=False),
        )
    audit_columns = _columns(sa.inspect(bind), "audit_events")
    with op.batch_alter_table("audit_events") as batch:
        if "sequence" not in audit_columns:
            batch.add_column(sa.Column("sequence", sa.Integer(), nullable=True))
        if "previous_hash" not in audit_columns:
            batch.add_column(sa.Column("previous_hash", sa.String(64), nullable=True))
        if "event_hash" not in audit_columns:
            batch.add_column(sa.Column("event_hash", sa.String(64), nullable=True))
    audit_events = sa.table(
        "audit_events",
        sa.column("id", sa.String()),
        sa.column("actor_id", sa.String()),
        sa.column("action", sa.String()),
        sa.column("target_type", sa.String()),
        sa.column("target_id", sa.String()),
        sa.column("detail", sa.JSON()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("sequence", sa.Integer()),
        sa.column("previous_hash", sa.String()),
        sa.column("event_hash", sa.String()),
    )
    previous_hash = "0" * 64
    sequence = 0
    rows = bind.execute(sa.select(audit_events).order_by(
        audit_events.c.created_at, audit_events.c.id
    )).mappings().all()
    for row in rows:
        sequence += 1
        created_at = _utc(row["created_at"])
        canonical = json.dumps({
            "id": row["id"],
            "sequence": sequence,
            "actor_id": row["actor_id"],
            "action": row["action"],
            "target_type": row["target_type"],
            "target_id": row["target_id"],
            "detail": row["detail"] or {},
            "created_at": created_at.isoformat(),
            "previous_hash": previous_hash,
        }, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        event_hash = hashlib.sha256(canonical.encode()).hexdigest()
        bind.execute(
            audit_events.update().where(audit_events.c.id == row["id"]).values(
                sequence=sequence, previous_hash=previous_hash, event_hash=event_hash,
            )
        )
        previous_hash = event_hash
    chain_heads = sa.table(
        "audit_chain_heads",
        sa.column("id", sa.String()),
        sa.column("sequence", sa.Integer()),
        sa.column("event_hash", sa.String()),
    )
    if not bind.execute(sa.select(chain_heads.c.id).where(chain_heads.c.id == "global")).first():
        bind.execute(chain_heads.insert().values(
            id="global", sequence=sequence, event_hash=previous_hash,
        ))
    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("audit_events")}
    if "ix_audit_events_sequence" not in indexes:
        op.create_index("ix_audit_events_sequence", "audit_events", ["sequence"], unique=True)
    if "ix_audit_events_event_hash" not in indexes:
        op.create_index("ix_audit_events_event_hash", "audit_events", ["event_hash"], unique=True)
    with op.batch_alter_table("audit_events") as batch:
        batch.alter_column("sequence", existing_type=sa.Integer(), nullable=False)
        batch.alter_column("previous_hash", existing_type=sa.String(64), nullable=False)
        batch.alter_column("event_hash", existing_type=sa.String(64), nullable=False)
    if bind.dialect.name == "postgresql":
        op.execute("""
        CREATE OR REPLACE FUNCTION reject_append_only_mutation()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          RAISE EXCEPTION '% is append-only', TG_TABLE_NAME;
        END $$;
        DROP TRIGGER IF EXISTS audit_events_append_only ON audit_events;
        CREATE TRIGGER audit_events_append_only
        BEFORE UPDATE OR DELETE ON audit_events
        FOR EACH ROW EXECUTE FUNCTION reject_append_only_mutation();
        DROP TRIGGER IF EXISTS human_passport_status_history_append_only
          ON human_passport_status_history;
        CREATE TRIGGER human_passport_status_history_append_only
        BEFORE UPDATE OR DELETE ON human_passport_status_history
        FOR EACH ROW EXECUTE FUNCTION reject_append_only_mutation();
        """)
    elif bind.dialect.name == "sqlite":
        for table in ("audit_events", "human_passport_status_history"):
            for operation in ("UPDATE", "DELETE"):
                trigger = f"{table}_reject_{operation.lower()}"
                op.execute(f"""
                CREATE TRIGGER IF NOT EXISTS {trigger}
                BEFORE {operation} ON {table}
                BEGIN
                  SELECT RAISE(ABORT, '{table} is append-only');
                END
                """)


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS audit_events_append_only ON audit_events")
        op.execute("""
        DROP TRIGGER IF EXISTS human_passport_status_history_append_only
          ON human_passport_status_history
        """)
        op.execute("DROP FUNCTION IF EXISTS reject_append_only_mutation()")
    elif bind.dialect.name == "sqlite":
        for table in ("audit_events", "human_passport_status_history"):
            for operation in ("update", "delete"):
                op.execute(f"DROP TRIGGER IF EXISTS {table}_reject_{operation}")
    inspector = sa.inspect(bind)
    if "human_passport_status_history" in inspector.get_table_names():
        op.drop_table("human_passport_status_history")
    if "audit_chain_heads" in inspector.get_table_names():
        op.drop_table("audit_chain_heads")
    audit_indexes = {index["name"] for index in sa.inspect(bind).get_indexes("audit_events")}
    for index in ("ix_audit_events_event_hash", "ix_audit_events_sequence"):
        if index in audit_indexes:
            op.drop_index(index, table_name="audit_events")
    with op.batch_alter_table("audit_events") as batch:
        for column in ("event_hash", "previous_hash", "sequence"):
            if column in _columns(sa.inspect(bind), "audit_events"):
                batch.drop_column(column)
    with op.batch_alter_table("human_passports") as batch:
        for column in ("status_changed_at", "status_reason"):
            if column in _columns(sa.inspect(bind), "human_passports"):
                batch.drop_column(column)
