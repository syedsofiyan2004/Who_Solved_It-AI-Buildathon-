from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.repository import AttachmentStatus, ContentStatus, ReviewDecision, VisibilityLevel


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    display_name: str
    job_title: str
    department_id: UUID
    team_id: UUID
    bio: str | None


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=160)
    job_title: str | None = Field(default=None, min_length=1, max_length=160)
    bio: str | None = Field(default=None, max_length=4000)
    contact_handle: str | None = Field(default=None, max_length=160)


class SolutionInput(BaseModel):
    root_cause: str = Field(min_length=1, max_length=20_000)
    resolution_steps: list[str] = Field(min_length=1, max_length=50)
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
    problem_description: str = Field(min_length=1, max_length=30_000)
    symptoms: str = Field(min_length=1, max_length=20_000)
    exact_error_message: str | None = Field(default=None, max_length=20_000)
    environment: str | None = Field(default=None, max_length=20_000)
    visibility: VisibilityLevel = VisibilityLevel.COMPANY
    department_id: UUID | None = None
    team_id: UUID | None = None
    technology_ids: list[UUID] = Field(default_factory=list, max_length=20)
    solution: SolutionInput

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
    problem_description: str | None = Field(default=None, min_length=1, max_length=30_000)
    symptoms: str | None = Field(default=None, min_length=1, max_length=20_000)
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


class ChallengeDetail(ChallengeSummary):
    problem_description: str
    symptoms: str
    exact_error_message: str | None
    environment: str | None
    department_id: UUID | None
    team_id: UUID | None
    solution: SolutionInput
    technology_ids: list[UUID]
    attachment_count: int


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
