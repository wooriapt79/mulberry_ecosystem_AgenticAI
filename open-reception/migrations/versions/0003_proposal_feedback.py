"""Add regional proposal feedback records.

Revision ID: 0003_feedback
Revises: 0002_v04
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_feedback"
down_revision = "0002_v04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "proposal_feedback",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("region", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("request_type", sa.String(), nullable=False),
        sa.Column("question", sa.String(), nullable=False),
        sa.Column("response", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_proposal_feedback_region", "proposal_feedback", ["region"])
    op.create_index("ix_proposal_feedback_category", "proposal_feedback", ["category"])
    op.create_index("ix_proposal_feedback_request_type", "proposal_feedback", ["request_type"])
    op.create_index("ix_proposal_feedback_status", "proposal_feedback", ["status"])


def downgrade() -> None:
    op.drop_index("ix_proposal_feedback_status", table_name="proposal_feedback")
    op.drop_index("ix_proposal_feedback_request_type", table_name="proposal_feedback")
    op.drop_index("ix_proposal_feedback_category", table_name="proposal_feedback")
    op.drop_index("ix_proposal_feedback_region", table_name="proposal_feedback")
    op.drop_table("proposal_feedback")
