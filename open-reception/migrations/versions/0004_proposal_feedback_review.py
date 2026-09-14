"""add proposal feedback review workflow fields

Revision ID: 0004_feedback_review
Revises: 0003_feedback
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_feedback_review"
down_revision = "0003_feedback"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("proposal_feedback") as batch_op:
        batch_op.add_column(
            sa.Column("reviewer_note", sa.String(), nullable=False, server_default="")
        )
        batch_op.add_column(
            sa.Column("escalation_status", sa.String(), nullable=False, server_default="none")
        )
        batch_op.create_index(
            "ix_proposal_feedback_escalation_status",
            ["escalation_status"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("proposal_feedback") as batch_op:
        batch_op.drop_index("ix_proposal_feedback_escalation_status")
        batch_op.drop_column("escalation_status")
        batch_op.drop_column("reviewer_note")
