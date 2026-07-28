"""phase 1 foundation schema

Revision ID: 202607200001
Revises:
Create Date: 2026-07-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202607200001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


APP_ROLE = postgresql.ENUM("employee", "reviewer", "administrator", name="app_role", create_type=False)
VISIBILITY_LEVEL = postgresql.ENUM(
    "company",
    "department",
    "team",
    "restricted",
    "administrator",
    name="visibility_level",
    create_type=False,
)
CONTENT_STATUS = postgresql.ENUM(
    "draft",
    "submitted",
    "changes_requested",
    "verified",
    "rejected",
    "archived",
    name="content_status",
    create_type=False,
)
REVIEW_DECISION = postgresql.ENUM(
    "verified",
    "changes_requested",
    "rejected",
    "revoked",
    name="review_decision",
    create_type=False,
)
ATTACHMENT_STATUS = postgresql.ENUM(
    "pending_scan",
    "available",
    "rejected",
    "deleted",
    name="attachment_status",
    create_type=False,
)
FEEDBACK_VALUE = postgresql.ENUM("helpful", "not_helpful", name="feedback_value", create_type=False)


def uuid_pk() -> sa.Column:
    return sa.Column(
        "id",
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )


def audit_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    ]


def soft_delete_column() -> sa.Column:
    return sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True)


def upgrade() -> None:
    op.execute('create extension if not exists "vector"')
    op.execute('create extension if not exists "citext"')
    op.execute('create extension if not exists "pg_trgm"')
    op.execute('create extension if not exists "pgcrypto"')

    bind = op.get_bind()
    APP_ROLE.create(bind, checkfirst=True)
    VISIBILITY_LEVEL.create(bind, checkfirst=True)
    CONTENT_STATUS.create(bind, checkfirst=True)
    REVIEW_DECISION.create(bind, checkfirst=True)
    ATTACHMENT_STATUS.create(bind, checkfirst=True)
    FEEDBACK_VALUE.create(bind, checkfirst=True)

    op.create_table(
        "departments",
        uuid_pk(),
        sa.Column("name", postgresql.CITEXT(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        *audit_columns(),
        soft_delete_column(),
        sa.UniqueConstraint("name", name="uq_departments_name"),
        sa.UniqueConstraint("slug", name="uq_departments_slug"),
    )
    op.create_index(
        "ix_departments_active",
        "departments",
        ["id"],
        postgresql_where=sa.text("deleted_at is null"),
    )

    op.create_table(
        "teams",
        uuid_pk(),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", postgresql.CITEXT(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        *audit_columns(),
        soft_delete_column(),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("department_id", "name", name="uq_teams_department_name"),
        sa.UniqueConstraint("slug", name="uq_teams_slug"),
    )
    op.create_index("ix_teams_department_id", "teams", ["department_id"])

    op.create_table(
        "users",
        uuid_pk(),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", APP_ROLE, nullable=False, server_default="employee"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        *audit_columns(),
        soft_delete_column(),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_active_role", "users", ["is_active", "role"])
    op.create_index(
        "ix_users_active_rows",
        "users",
        ["id"],
        postgresql_where=sa.text("deleted_at is null"),
    )

    op.create_table(
        "technologies",
        uuid_pk(),
        sa.Column("name", postgresql.CITEXT(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=True),
        *audit_columns(),
        soft_delete_column(),
        sa.UniqueConstraint("name", name="uq_technologies_name"),
        sa.UniqueConstraint("slug", name="uq_technologies_slug"),
    )
    op.create_index("ix_technologies_slug", "technologies", ["slug"])

    op.create_table(
        "employee_profiles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("job_title", sa.String(length=160), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contact_email", postgresql.CITEXT(), nullable=False),
        sa.Column("contact_handle", sa.String(length=160), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("avatar_key", sa.Text(), nullable=True),
        *audit_columns(),
        soft_delete_column(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_employee_profiles_department_id", "employee_profiles", ["department_id"])
    op.create_index("ix_employee_profiles_team_id", "employee_profiles", ["team_id"])

    op.create_table(
        "profile_skills",
        sa.Column("profile_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("technology_id", postgresql.UUID(as_uuid=True), nullable=False),
        *audit_columns(),
        sa.ForeignKeyConstraint(["profile_user_id"], ["employee_profiles.user_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["technology_id"], ["technologies.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("profile_user_id", "technology_id", name="pk_profile_skills"),
    )

    op.create_table(
        "challenges",
        uuid_pk(),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("problem_description", sa.Text(), nullable=False),
        sa.Column("symptoms", sa.Text(), nullable=False),
        sa.Column("exact_error_message", sa.Text(), nullable=True),
        sa.Column("environment", sa.Text(), nullable=True),
        sa.Column("status", CONTENT_STATUS, nullable=False, server_default="draft"),
        sa.Column("visibility", VISIBILITY_LEVEL, nullable=False, server_default="company"),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        *audit_columns(),
        soft_delete_column(),
        sa.Column("search_document", postgresql.TSVECTOR(), nullable=True),
        sa.CheckConstraint("length(trim(title)) > 0", name="ck_challenges_title_nonblank"),
        sa.CheckConstraint(
            "(visibility != 'department') or department_id is not null",
            name="ck_challenges_department_visibility_scope",
        ),
        sa.CheckConstraint(
            "(visibility != 'team') or team_id is not null",
            name="ck_challenges_team_visibility_scope",
        ),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_challenges_status_visibility_deleted", "challenges", ["status", "visibility", "deleted_at"])
    op.create_index("ix_challenges_owner_user_id", "challenges", ["owner_user_id"])
    op.create_index("ix_challenges_search_document", "challenges", ["search_document"], postgresql_using="gin")
    op.create_index(
        "ix_challenges_exact_error_trgm",
        "challenges",
        ["exact_error_message"],
        postgresql_using="gin",
        postgresql_ops={"exact_error_message": "gin_trgm_ops"},
    )

    op.create_table(
        "solutions",
        uuid_pk(),
        sa.Column("challenge_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("root_cause", sa.Text(), nullable=False),
        sa.Column("resolution_steps", postgresql.JSONB(), nullable=False),
        sa.Column("code_snippets", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("prevention_notes", sa.Text(), nullable=True),
        sa.Column("status", CONTENT_STATUS, nullable=False, server_default="draft"),
        sa.Column("solved_at", sa.Date(), nullable=True),
        sa.Column("primary_owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        *audit_columns(),
        soft_delete_column(),
        sa.CheckConstraint("length(trim(root_cause)) > 0", name="ck_solutions_root_cause_nonblank"),
        sa.CheckConstraint("jsonb_typeof(resolution_steps) = 'array'", name="ck_solutions_steps_array"),
        sa.CheckConstraint("jsonb_typeof(code_snippets) = 'array'", name="ck_solutions_code_snippets_array"),
        sa.ForeignKeyConstraint(["challenge_id"], ["challenges.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["primary_owner_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("challenge_id", name="uq_solutions_challenge_id"),
    )
    op.create_index("ix_solutions_challenge_id", "solutions", ["challenge_id"])
    op.create_index("ix_solutions_status", "solutions", ["status"])
    op.create_index("ix_solutions_primary_owner_user_id", "solutions", ["primary_owner_user_id"])

    op.create_table(
        "challenge_technologies",
        sa.Column("challenge_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("technology_id", postgresql.UUID(as_uuid=True), nullable=False),
        *audit_columns(),
        sa.ForeignKeyConstraint(["challenge_id"], ["challenges.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["technology_id"], ["technologies.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("challenge_id", "technology_id", name="pk_challenge_technologies"),
    )
    op.create_index("ix_challenge_technologies_technology_id", "challenge_technologies", ["technology_id"])

    op.create_table(
        "solution_contributors",
        sa.Column("solution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contribution_role", sa.String(length=40), nullable=False),
        *audit_columns(),
        sa.CheckConstraint(
            "contribution_role in ('primary', 'contributor', 'reviewer')",
            name="ck_solution_contributors_role",
        ),
        sa.ForeignKeyConstraint(["solution_id"], ["solutions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("solution_id", "user_id", name="pk_solution_contributors"),
    )

    op.create_table(
        "attachments",
        uuid_pk(),
        sa.Column("challenge_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uploaded_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.CHAR(length=64), nullable=False),
        sa.Column("status", ATTACHMENT_STATUS, nullable=False, server_default="pending_scan"),
        sa.Column("scan_result", sa.Text(), nullable=True),
        *audit_columns(),
        soft_delete_column(),
        sa.CheckConstraint("size_bytes > 0", name="ck_attachments_size_positive"),
        sa.ForeignKeyConstraint(["challenge_id"], ["challenges.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("storage_key", name="uq_attachments_storage_key"),
        sa.UniqueConstraint("challenge_id", "sha256", name="uq_attachments_challenge_sha256"),
    )

    op.create_table(
        "verification_reviews",
        uuid_pk(),
        sa.Column("solution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewer_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decision", REVIEW_DECISION, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("visibility_after", VISIBILITY_LEVEL, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("supersedes_review_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["solution_id"], ["solutions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reviewer_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["supersedes_review_id"], ["verification_reviews.id"], ondelete="RESTRICT"),
    )
    op.create_index(
        "ix_verification_reviews_solution_created",
        "verification_reviews",
        ["solution_id", sa.text("created_at desc")],
    )

    op.create_table(
        "search_queries",
        uuid_pk(),
        sa.Column("requested_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("filters", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("result_count", sa.SmallInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("top_solution_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("bedrock_generation_used", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("latency_ms >= 0", name="ck_search_queries_latency_nonnegative"),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["top_solution_id"], ["solutions.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_search_queries_user_created", "search_queries", ["requested_by_user_id", "created_at"])
    op.create_index("ix_search_queries_outcome_created", "search_queries", ["outcome", "created_at"])

    op.create_table(
        "feedback",
        uuid_pk(),
        sa.Column("solution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("submitted_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("search_query_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("value", FEEDBACK_VALUE, nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        *audit_columns(),
        sa.ForeignKeyConstraint(["solution_id"], ["solutions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["submitted_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["search_query_id"], ["search_queries.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_feedback_solution_value", "feedback", ["solution_id", "value"])
    op.create_index("ix_feedback_search_query_id", "feedback", ["search_query_id"])
    op.create_index(
        "uq_feedback_solution_user_query",
        "feedback",
        ["solution_id", "submitted_by_user_id", "search_query_id"],
        unique=True,
        postgresql_where=sa.text("search_query_id is not null"),
    )

    op.create_table(
        "audit_logs",
        uuid_pk(),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ip_hash", sa.CHAR(length=64), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_audit_logs_entity_created", "audit_logs", ["entity_type", "entity_id", "created_at"])
    op.create_index("ix_audit_logs_actor_created", "audit_logs", ["actor_user_id", "created_at"])
    op.create_index("ix_audit_logs_request_id", "audit_logs", ["request_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_request_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_created", table_name="audit_logs")
    op.drop_index("ix_audit_logs_entity_created", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("uq_feedback_solution_user_query", table_name="feedback")
    op.drop_index("ix_feedback_search_query_id", table_name="feedback")
    op.drop_index("ix_feedback_solution_value", table_name="feedback")
    op.drop_table("feedback")
    op.drop_index("ix_search_queries_outcome_created", table_name="search_queries")
    op.drop_index("ix_search_queries_user_created", table_name="search_queries")
    op.drop_table("search_queries")
    op.drop_index("ix_verification_reviews_solution_created", table_name="verification_reviews")
    op.drop_table("verification_reviews")
    op.drop_table("attachments")
    op.drop_table("solution_contributors")
    op.drop_index("ix_challenge_technologies_technology_id", table_name="challenge_technologies")
    op.drop_table("challenge_technologies")
    op.drop_index("ix_solutions_primary_owner_user_id", table_name="solutions")
    op.drop_index("ix_solutions_status", table_name="solutions")
    op.drop_index("ix_solutions_challenge_id", table_name="solutions")
    op.drop_table("solutions")
    op.drop_index("ix_challenges_exact_error_trgm", table_name="challenges")
    op.drop_index("ix_challenges_search_document", table_name="challenges")
    op.drop_index("ix_challenges_owner_user_id", table_name="challenges")
    op.drop_index("ix_challenges_status_visibility_deleted", table_name="challenges")
    op.drop_table("challenges")
    op.drop_table("profile_skills")
    op.drop_index("ix_employee_profiles_team_id", table_name="employee_profiles")
    op.drop_index("ix_employee_profiles_department_id", table_name="employee_profiles")
    op.drop_table("employee_profiles")
    op.drop_index("ix_technologies_slug", table_name="technologies")
    op.drop_table("technologies")
    op.drop_index("ix_users_active_rows", table_name="users")
    op.drop_index("ix_users_active_role", table_name="users")
    op.drop_table("users")
    op.drop_index("ix_teams_department_id", table_name="teams")
    op.drop_table("teams")
    op.drop_index("ix_departments_active", table_name="departments")
    op.drop_table("departments")

    bind = op.get_bind()
    FEEDBACK_VALUE.drop(bind, checkfirst=True)
    ATTACHMENT_STATUS.drop(bind, checkfirst=True)
    REVIEW_DECISION.drop(bind, checkfirst=True)
    CONTENT_STATUS.drop(bind, checkfirst=True)
    VISIBILITY_LEVEL.drop(bind, checkfirst=True)
    APP_ROLE.drop(bind, checkfirst=True)
