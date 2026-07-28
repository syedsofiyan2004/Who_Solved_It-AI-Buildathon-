"""allow incomplete solution drafts

Revision ID: 202607220007
Revises: 202607220006
Create Date: 2026-07-22
"""

from alembic import op

revision = "202607220007"
down_revision = "202607220006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_solutions_root_cause_nonblank", "solutions", type_="check")
    op.create_check_constraint(
        "ck_solutions_root_cause_required_after_draft",
        "solutions",
        "status IN ('draft', 'changes_requested') OR length(trim(root_cause)) > 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_solutions_root_cause_required_after_draft", "solutions", type_="check")
    op.create_check_constraint(
        "ck_solutions_root_cause_nonblank",
        "solutions",
        "length(trim(root_cause)) > 0",
    )
