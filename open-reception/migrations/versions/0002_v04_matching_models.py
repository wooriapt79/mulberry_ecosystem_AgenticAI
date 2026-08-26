"""v0.4 matching recommendation and human decision models

Revision ID: 0002_v04
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_v04"
down_revision = "0001_v03"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "matching_recommendations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "request_id",
            sa.String(),
            sa.ForeignKey("matching_requests.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("domain_pack_version", sa.String(), nullable=False),
        sa.Column("policy_version", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("rationale", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_matching_recommendations_request_id",
        "matching_recommendations",
        ["request_id"],
        unique=True,
    )
    op.create_table(
        "matching_candidates",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "recommendation_id",
            sa.String(),
            sa.ForeignKey("matching_recommendations.id"),
            nullable=False,
        ),
        sa.Column(
            "agent_passport_id",
            sa.String(),
            sa.ForeignKey("ai_passports.id"),
            nullable=False,
        ),
        sa.Column("agent_kind", sa.String(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("eligible", sa.Boolean(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("exclusion_reasons", sa.JSON(), nullable=False),
        sa.Column("supervisor_agent_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "recommendation_id",
            "agent_passport_id",
            name="uq_matching_candidate_recommendation_agent",
        ),
    )
    op.create_index(
        "ix_matching_candidates_recommendation_id",
        "matching_candidates",
        ["recommendation_id"],
    )
    op.create_table(
        "matching_decisions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "recommendation_id",
            sa.String(),
            sa.ForeignKey("matching_recommendations.id"),
            nullable=False,
        ),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("from_status", sa.String(), nullable=False),
        sa.Column("to_status", sa.String(), nullable=False),
        sa.Column("decided_by", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_matching_decisions_recommendation_id",
        "matching_decisions",
        ["recommendation_id"],
    )


def downgrade():
    op.drop_index(
        "ix_matching_decisions_recommendation_id",
        table_name="matching_decisions",
    )
    op.drop_table("matching_decisions")
    op.drop_index(
        "ix_matching_candidates_recommendation_id",
        table_name="matching_candidates",
    )
    op.drop_table("matching_candidates")
    op.drop_index(
        "ix_matching_recommendations_request_id",
        table_name="matching_recommendations",
    )
    op.drop_table("matching_recommendations")
