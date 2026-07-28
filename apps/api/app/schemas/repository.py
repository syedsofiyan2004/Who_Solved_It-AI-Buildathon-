from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.repository import (
    AttachmentStatus,
    ContentStatus,
    FeedbackValue,
    ReviewDecision,
    VisibilityLevel,
)


class ProfileResponse(BaseModel):
    user_id: UUID
    display_name: str
    job_title: str
    team: str
    department: str
    department_id: UUID
    team_id: UUID
    contact_email: str
    contact_handle: str | None
    skills: list[str]
    technologies: list[str]
    avatar_key: str | None
    initials: str
    bio: str | None
    verified_solutions: list["ProfileSolution"]
    contribution_count: int
    helpful_contribution_count: int | None


class ProfileDirectoryItem(BaseModel):
    user_id: UUID
    display_name: str
    job_title: str
    team: str
    department: str
    contact_email: str
    contact_handle: str | None
    skills: list[str]
    avatar_key: str | None
    initials: str


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=160)
    job_title: str | None = Field(default=None, min_length=1, max_length=160)
    bio: str | None = Field(default=None, max_length=4000)
    contact_handle: str | None = Field(default=None, max_length=160)
    skills: list[str] | None = Field(default=None, max_length=20)

    @field_validator("skills")
    @classmethod
    def clean_skills(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        cleaned = []
        for value in values:
            normalized = " ".join(value.split())
            if not normalized or len(normalized) > 80:
                raise ValueError("Skills must be non-empty and no longer than 80 characters.")
            if normalized not in cleaned:
                cleaned.append(normalized)
        return cleaned


class ProfileSolution(BaseModel):
    challenge_id: UUID
    solution_id: UUID
    title: str
    status: ContentStatus
    visibility: VisibilityLevel
    solved_at: date | None
    updated_at: datetime
    technologies: list[str]


class SolutionInput(BaseModel):
    root_cause: str = Field(default="", max_length=20_000)
    resolution_steps: list[str] = Field(default_factory=list, max_length=50)
    code_snippets: list[str] = Field(default_factory=list, max_length=20)
    prevention_notes: str | None = Field(default=None, max_length=20_000)
    solved_at: date | None = None

    @field_validator("resolution_steps", "code_snippets")
    @classmethod
    def nonblank_entries(cls, values: list[str]) -> list[str]:
        if any(not value.strip() or len(value) > 20_000 for value in values):
            raise ValueError("List entries must be non-empty and within the allowed length.")
        return [value.strip() for value in values]


class ChallengeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    problem_description: str = Field(default="", max_length=30_000)
    symptoms: str = Field(default="", max_length=20_000)
    exact_error_message: str | None = Field(default=None, max_length=20_000)
    environment: str | None = Field(default=None, max_length=20_000)
    visibility: VisibilityLevel = VisibilityLevel.COMPANY
    department_id: UUID | None = None
    team_id: UUID | None = None
    technology_ids: list[UUID] = Field(default_factory=list, max_length=20)
    solution: SolutionInput = Field(default_factory=SolutionInput)

    @model_validator(mode="after")
    def validate_scope(self):
        if self.visibility == VisibilityLevel.DEPARTMENT and self.department_id is None:
            raise ValueError("Department visibility requires a department.")
        if self.visibility == VisibilityLevel.TEAM and self.team_id is None:
            raise ValueError("Team visibility requires a team.")
        return self


class ChallengeUpdate(BaseModel):
    expected_updated_at: datetime
    title: str | None = Field(default=None, min_length=1, max_length=240)
    # Drafts are intentionally allowed to remain incomplete. The submit
    # endpoint performs the strict completeness check before review.
    problem_description: str | None = Field(default=None, max_length=30_000)
    symptoms: str | None = Field(default=None, max_length=20_000)
    exact_error_message: str | None = Field(default=None, max_length=20_000)
    environment: str | None = Field(default=None, max_length=20_000)
    visibility: VisibilityLevel | None = None
    department_id: UUID | None = None
    team_id: UUID | None = None
    technology_ids: list[UUID] | None = Field(default=None, max_length=20)
    solution: SolutionInput | None = None

    @model_validator(mode="after")
    def has_change(self):
        changed = self.model_dump(exclude={"expected_updated_at"}, exclude_none=True)
        if not changed:
            raise ValueError("At least one editable field is required.")
        return self


class ChallengeSummary(BaseModel):
    id: UUID
    title: str
    status: ContentStatus
    visibility: VisibilityLevel
    owner_user_id: UUID
    updated_at: datetime


class RelatedSolution(BaseModel):
    challenge_id: UUID
    title: str
    updated_at: datetime
    technologies: list[str]


class ChallengeDetail(ChallengeSummary):
    solution_id: UUID
    problem_description: str
    symptoms: str
    exact_error_message: str | None
    environment: str | None
    department_id: UUID | None
    team_id: UUID | None
    solution: SolutionInput
    technology_ids: list[UUID]
    technologies: list[str]
    attachment_count: int
    attachments: list["AttachmentResponse"] = Field(default_factory=list)
    review_history: list["ReviewHistoryItem"] = Field(default_factory=list)
    verified_by_user_id: UUID | None
    verified_by_name: str | None
    last_verified_at: datetime | None
    related_solutions: list["RelatedSolution"] = Field(default_factory=list)
    can_edit: bool
    feedback: "FeedbackSummary"


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_filename: str
    content_type: str
    size_bytes: int
    status: AttachmentStatus


class ReviewCreate(BaseModel):
    solution_id: UUID
    decision: ReviewDecision
    notes: str | None = Field(default=None, max_length=10_000)
    visibility_after: VisibilityLevel | None = None

    @model_validator(mode="after")
    def review_notes_required_when_needed(self):
        if self.decision in {ReviewDecision.CHANGES_REQUESTED, ReviewDecision.REJECTED} and not self.notes:
            raise ValueError("Notes are required for this review decision.")
        return self


class ReviewHistoryItem(BaseModel):
    id: UUID
    reviewer_user_id: UUID
    reviewer_name: str
    decision: ReviewDecision
    notes: str | None
    visibility_after: VisibilityLevel | None
    created_at: datetime


class FeedbackCreate(BaseModel):
    solution_id: UUID
    search_query_id: UUID | None = None
    value: FeedbackValue
    comment: str | None = Field(default=None, max_length=1000)


class FeedbackResponse(BaseModel):
    id: UUID
    solution_id: UUID
    value: FeedbackValue
    comment: str | None
    updated_at: datetime


class FeedbackSummary(BaseModel):
    helpful: int
    not_helpful: int
    resolved_my_issue: int
    current_user_feedback: FeedbackResponse | None


class ArchiveRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)


class SearchSort(str, Enum):
    RELEVANCE = "relevance"
    NEWEST = "newest"


class SearchFilters(BaseModel):
    technology_ids: list[UUID] = Field(default_factory=list, max_length=20)
    department_id: UUID | None = None
    team_id: UUID | None = None
    verified_only: bool = True
    visibility: VisibilityLevel | None = None


class SearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=1000)
    filters: SearchFilters = Field(default_factory=SearchFilters)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=20)
    sort: SearchSort = SearchSort.RELEVANCE
    include_summary: bool = False

    @field_validator("query")
    @classmethod
    def normalized_query(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if len(normalized) < 3:
            raise ValueError("Search queries must contain at least 3 non-space characters.")
        return normalized


class SearchResultSolver(BaseModel):
    user_id: UUID
    display_name: str
    job_title: str
    team: str | None = None
    department: str | None = None
    avatar_key: str | None = None
    initials: str | None = None
    contact_email: str | None = None
    contact_handle: str | None = None


class SearchResult(BaseModel):
    challenge_id: UUID
    solution_id: UUID
    title: str
    problem_excerpt: str
    root_cause_excerpt: str
    resolution_steps: list[str]
    exact_error_message: str | None
    status: ContentStatus
    visibility: VisibilityLevel
    solved_at: date | None
    updated_at: datetime
    technologies: list[str]
    solver: SearchResultSolver
    match_reasons: list[str] = Field(max_length=3)
    score: float


class SearchLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    query: str
    result_count: int
    outcome: str
    latency_ms: int
    created_at: datetime
