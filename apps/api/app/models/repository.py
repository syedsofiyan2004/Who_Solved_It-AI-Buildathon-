from datetime import date, datetime
from enum import Enum
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import UserDefinedType

from app.models.base import Base


class ContentStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    CHANGES_REQUESTED = "changes_requested"
    VERIFIED = "verified"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class VisibilityLevel(str, Enum):
    COMPANY = "company"
    DEPARTMENT = "department"
    TEAM = "team"
    RESTRICTED = "restricted"
    ADMINISTRATOR = "administrator"


class ReviewDecision(str, Enum):
    VERIFIED = "verified"
    CHANGES_REQUESTED = "changes_requested"
    REJECTED = "rejected"
    REVOKED = "revoked"


class AttachmentStatus(str, Enum):
    PENDING_SCAN = "pending_scan"
    AVAILABLE = "available"
    REJECTED = "rejected"
    DELETED = "deleted"


class FeedbackValue(str, Enum):
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    RESOLVED_MY_ISSUE = "resolved_my_issue"


CONTENT_STATUS_ENUM = SAEnum(
    ContentStatus, name="content_status", values_callable=lambda statuses: [item.value for item in statuses], create_type=False
)
VISIBILITY_ENUM = SAEnum(
    VisibilityLevel, name="visibility_level", values_callable=lambda levels: [item.value for item in levels], create_type=False
)
REVIEW_DECISION_ENUM = SAEnum(
    ReviewDecision, name="review_decision", values_callable=lambda decisions: [item.value for item in decisions], create_type=False
)
ATTACHMENT_STATUS_ENUM = SAEnum(
    AttachmentStatus, name="attachment_status", values_callable=lambda statuses: [item.value for item in statuses], create_type=False
)
FEEDBACK_VALUE_ENUM = SAEnum(
    FeedbackValue, name="feedback_value", values_callable=lambda values: [item.value for item in values], create_type=False
)


class PgVector(UserDefinedType):
    cache_ok = True

    def get_col_spec(self, **kw):
        return "vector"

    def bind_processor(self, dialect):
        def process(value):
            if value is None or isinstance(value, str):
                return value
            return "[" + ",".join(format(float(item), ".10g") for item in value) + "]"
        return process


class Department(Base):
    __tablename__ = "departments"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)


class Team(Base):
    __tablename__ = "teams"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    department_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("departments.id"))
    name: Mapped[str] = mapped_column(nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)


class EmployeeProfile(Base):
    __tablename__ = "employee_profiles"
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    job_title: Mapped[str] = mapped_column(String(160), nullable=False)
    department_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("departments.id"))
    team_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("teams.id"))
    contact_email: Mapped[str] = mapped_column(nullable=False)
    contact_handle: Mapped[str | None] = mapped_column(String(160))
    skills: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="'[]'::jsonb")
    bio: Mapped[str | None] = mapped_column(Text)
    avatar_key: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Technology(Base):
    __tablename__ = "technologies"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(80))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Challenge(Base):
    __tablename__ = "challenges"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    problem_description: Mapped[str] = mapped_column(Text, nullable=False)
    symptoms: Mapped[str] = mapped_column(Text, nullable=False)
    exact_error_message: Mapped[str | None] = mapped_column(Text)
    environment: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ContentStatus] = mapped_column(CONTENT_STATUS_ENUM, nullable=False)
    visibility: Mapped[VisibilityLevel] = mapped_column(VISIBILITY_ENUM, nullable=False)
    department_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("departments.id"))
    team_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("teams.id"))
    owner_user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_by_user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by_user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    search_document: Mapped[object | None] = mapped_column(TSVECTOR)


class Solution(Base):
    __tablename__ = "solutions"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    challenge_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False)
    root_cause: Mapped[str] = mapped_column(Text, nullable=False)
    resolution_steps: Mapped[list] = mapped_column(JSONB, nullable=False)
    code_snippets: Mapped[list] = mapped_column(JSONB, nullable=False)
    prevention_notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ContentStatus] = mapped_column(CONTENT_STATUS_ENUM, nullable=False)
    solved_at: Mapped[date | None] = mapped_column(Date)
    primary_owner_user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ChallengeTechnology(Base):
    __tablename__ = "challenge_technologies"
    challenge_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("challenges.id", ondelete="CASCADE"), primary_key=True)
    technology_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("technologies.id"), primary_key=True)


class SolutionContributor(Base):
    __tablename__ = "solution_contributors"
    solution_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("solutions.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    contribution_role: Mapped[str] = mapped_column(String(40), nullable=False)


class Attachment(Base):
    __tablename__ = "attachments"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    challenge_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False)
    uploaded_by_user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[AttachmentStatus] = mapped_column(ATTACHMENT_STATUS_ENUM, nullable=False)
    scan_result: Mapped[str | None] = mapped_column(Text)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class VerificationReview(Base):
    __tablename__ = "verification_reviews"
    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    solution_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("solutions.id"), nullable=False)
    reviewer_user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    decision: Mapped[ReviewDecision] = mapped_column(REVIEW_DECISION_ENUM, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    visibility_after: Mapped[VisibilityLevel | None] = mapped_column(VISIBILITY_ENUM)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SearchQuery(Base):
    __tablename__ = "search_queries"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    requested_by_user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    filters: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="'{}'::jsonb")
    result_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    top_solution_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("solutions.id"))
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    bedrock_generation_used: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SolutionEmbedding(Base):
    __tablename__ = "solution_embeddings"
    __table_args__ = (UniqueConstraint("solution_id", "embedding_model", "content_hash", name="uq_solution_embeddings_content"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    solution_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("solutions.id", ondelete="CASCADE"), nullable=False)
    searchable_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(PgVector(), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(255), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    solution_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("solutions.id"), nullable=False)
    submitted_by_user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    search_query_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("search_queries.id"))
    value: Mapped[FeedbackValue] = mapped_column(FEEDBACK_VALUE_ENUM, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
