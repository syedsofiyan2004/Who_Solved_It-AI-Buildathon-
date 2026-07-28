"""support resolved feedback and one current record

Revision ID: 202607220008
Revises: 202607220007
Create Date: 2026-07-22
"""

from alembic import op

revision = "202607220008"
down_revision = "202607220007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE feedback_value ADD VALUE IF NOT EXISTS 'resolved_my_issue'")
    op.create_index(
        "uq_feedback_solution_user_current",
        "feedback",
        ["solution_id", "submitted_by_user_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_feedback_solution_user_current", table_name="feedback")
