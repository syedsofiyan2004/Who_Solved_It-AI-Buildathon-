from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import forbidden_error
from app.core.security import get_current_user, require_roles
from app.database.session import get_db
from app.models.auth import AppRole, User
from app.models.repository import (
    Attachment,
    AttachmentStatus,
    Challenge,
    ChallengeTechnology,
    ContentStatus,
    Department,
    EmployeeProfile,
    Feedback,
    FeedbackValue,
    ReviewDecision,
    SearchQuery,
    Solution,
    SolutionEmbedding,
    Team,
    Technology,
    VerificationReview,
    VisibilityLevel,
)
from app.schemas.repository import (
    ArchiveRequest,
    AttachmentResponse,
    ChallengeCreate,
    ChallengeDetail,
    ChallengeSummary,
    ChallengeUpdate,
    FeedbackCreate,
    FeedbackResponse,
    FeedbackSummary,
    ProfileDirectoryItem,
    ProfileResponse,
    ProfileSolution,
    ProfileUpdate,
    RelatedSolution,
    ReviewCreate,
    ReviewHistoryItem,
    SolutionInput,
)
from app.services.audit import audit_event
from app.services.embeddings import (
    BedrockEmbeddingAdapter,
    EmbeddingContentRejected,
    EmbeddingUnavailable,
    NvidiaEmbeddingAdapter,
    embed_verified_solution,
)
from app.services.repository import (
    can_edit_challenge,
    can_review,
    can_view_challenge,
    load_challenge,
    load_solution,
    not_found,
    require_edit_challenge,
    require_view_challenge,
    sanitized_filename,
    set_submitted,
)
from app.services.search import _technology_names

router = APIRouter(tags=["knowledge repository"])


def _embedding_adapter(settings: Settings):
    if settings.effective_ai_provider == "nvidia":
        return NvidiaEmbeddingAdapter(settings)
    if settings.effective_ai_provider == "bedrock":
        return BedrockEmbeddingAdapter(settings)
    raise EmbeddingUnavailable("Semantic search is disabled until an embedding provider is configured.")


def _initials(display_name: str) -> str:
    parts = [part for part in display_name.replace("-", " ").split() if part]
    return "".join(part[0].upper() for part in parts[:2]) or "?"


def _technology_map(db: Session, challenge_ids: list[UUID]) -> dict[UUID, list[str]]:
    if not challenge_ids:
        return {}
    rows = db.execute(
        select(ChallengeTechnology.challenge_id, func.array_agg(Technology.name))
        .join(Technology, Technology.id == ChallengeTechnology.technology_id)
        .where(ChallengeTechnology.challenge_id.in_(challenge_ids), Technology.deleted_at.is_(None))
        .group_by(ChallengeTechnology.challenge_id)
    ).all()
    return {challenge_id: _technology_names(names) for challenge_id, names in rows}


def _profile_response(db: Session, viewer: User, profile: EmployeeProfile) -> dict:
    team = db.get(Team, profile.team_id)
    department = db.get(Department, profile.department_id)
    challenge_rows = db.execute(
        select(Challenge, Solution)
        .join(Solution, Solution.challenge_id == Challenge.id)
        .where(
            Challenge.owner_user_id == profile.user_id,
            Challenge.deleted_at.is_(None),
            Solution.deleted_at.is_(None),
        )
        .order_by(Challenge.updated_at.desc())
    ).all()
    visible_rows = [row for row in challenge_rows if can_view_challenge(db, viewer, row.Challenge)]
    verified_rows = [row for row in visible_rows if row.Challenge.status == ContentStatus.VERIFIED]
    technology_names = _technology_map(db, [row.Challenge.id for row in visible_rows])
    verified_solutions = [
        ProfileSolution(
            challenge_id=row.Challenge.id,
            solution_id=row.Solution.id,
            title=row.Challenge.title,
            status=row.Challenge.status,
            visibility=row.Challenge.visibility,
            solved_at=row.Solution.solved_at,
            updated_at=row.Challenge.updated_at,
            technologies=technology_names.get(row.Challenge.id, []),
        )
        for row in verified_rows
    ]
    technologies = sorted(
        {
            technology
            for row in verified_rows
            for technology in technology_names.get(row.Challenge.id, [])
        }
    )
    verified_solution_ids = [row.Solution.id for row in verified_rows]
    helpful_count = 0
    if verified_solution_ids:
        helpful_count = db.scalar(
            select(func.count(Feedback.id)).where(
                Feedback.solution_id.in_(verified_solution_ids),
                Feedback.value.in_([FeedbackValue.HELPFUL, FeedbackValue.RESOLVED_MY_ISSUE]),
            )
        ) or 0
    return ProfileResponse(
        user_id=profile.user_id,
        display_name=profile.display_name,
        job_title=profile.job_title,
        team=team.name if team else "",
        department=department.name if department else "",
        department_id=profile.department_id,
        team_id=profile.team_id,
        contact_email=profile.contact_email,
        contact_handle=profile.contact_handle,
        skills=list(profile.skills or []),
        technologies=technologies,
        avatar_key=profile.avatar_key,
        initials=_initials(profile.display_name),
        bio=profile.bio,
        verified_solutions=verified_solutions,
        contribution_count=len(visible_rows),
        helpful_contribution_count=helpful_count,
    ).model_dump(mode="json")


def _solution_input(solution: Solution) -> SolutionInput:
    return SolutionInput(
        root_cause=solution.root_cause,
        resolution_steps=solution.resolution_steps,
        code_snippets=solution.code_snippets,
        prevention_notes=solution.prevention_notes,
        solved_at=solution.solved_at,
    )


def _feedback_summary(db: Session, user: User, solution_id: UUID) -> FeedbackSummary:
    rows = db.scalars(select(Feedback).where(Feedback.solution_id == solution_id)).all()
    current = next((item for item in rows if item.submitted_by_user_id == user.id), None)
    return FeedbackSummary(
        helpful=sum(1 for item in rows if item.value == FeedbackValue.HELPFUL),
        not_helpful=sum(1 for item in rows if item.value == FeedbackValue.NOT_HELPFUL),
        resolved_my_issue=sum(1 for item in rows if item.value == FeedbackValue.RESOLVED_MY_ISSUE),
        current_user_feedback=FeedbackResponse(
            id=current.id,
            solution_id=current.solution_id,
            value=current.value,
            comment=current.comment,
            updated_at=current.updated_at,
        ) if current else None,
    )


def _detail(db: Session, viewer: User, challenge: Challenge) -> dict:
    solution = load_solution(db, challenge.id)
    technology_ids = list(db.scalars(select(ChallengeTechnology.technology_id).where(ChallengeTechnology.challenge_id == challenge.id)))
    technology_names = _technology_map(db, [challenge.id]).get(challenge.id, [])
    attachments = list(
        db.scalars(
            select(Attachment)
            .where(Attachment.challenge_id == challenge.id, Attachment.deleted_at.is_(None))
            .order_by(Attachment.id)
        )
    )
    review_rows = db.execute(
        select(VerificationReview, EmployeeProfile)
        .join(EmployeeProfile, EmployeeProfile.user_id == VerificationReview.reviewer_user_id)
        .where(VerificationReview.solution_id == solution.id)
        .order_by(VerificationReview.created_at.desc())
    ).all()
    # Historical verification decisions remain visible in review_history, but
    # only a currently verified record may expose active verification metadata.
    verified_review = (
        next((row for row in review_rows if row.VerificationReview.decision == ReviewDecision.VERIFIED), None)
        if challenge.status == ContentStatus.VERIFIED
        else None
    )
    related_rows: list[Challenge] = []
    if technology_ids:
        related_candidates = db.scalars(
            select(Challenge)
            .join(ChallengeTechnology, ChallengeTechnology.challenge_id == Challenge.id)
            .where(
                Challenge.id != challenge.id,
                Challenge.status == ContentStatus.VERIFIED,
                Challenge.deleted_at.is_(None),
                ChallengeTechnology.technology_id.in_(technology_ids),
            )
            .group_by(Challenge.id)
            .order_by(func.count(ChallengeTechnology.technology_id).desc(), Challenge.updated_at.desc())
            .limit(12)
        ).all()
        related_rows = [candidate for candidate in related_candidates if can_view_challenge(db, viewer, candidate)][:3]
    related_technology_names = _technology_map(db, [row.id for row in related_rows])
    return ChallengeDetail(
        id=challenge.id,
        solution_id=solution.id,
        title=challenge.title,
        status=challenge.status,
        visibility=challenge.visibility,
        owner_user_id=challenge.owner_user_id,
        updated_at=challenge.updated_at,
        problem_description=challenge.problem_description,
        symptoms=challenge.symptoms,
        exact_error_message=challenge.exact_error_message,
        environment=challenge.environment,
        department_id=challenge.department_id,
        team_id=challenge.team_id,
        solution=_solution_input(solution),
        technology_ids=technology_ids,
        technologies=technology_names,
        attachment_count=len(attachments),
        attachments=[AttachmentResponse.model_validate(attachment) for attachment in attachments],
        review_history=[
            ReviewHistoryItem(
                id=review.id,
                reviewer_user_id=review.reviewer_user_id,
                reviewer_name=profile.display_name,
                decision=review.decision,
                notes=review.notes,
                visibility_after=review.visibility_after,
                created_at=review.created_at,
            )
            for review, profile in review_rows
        ],
        verified_by_user_id=verified_review.EmployeeProfile.user_id if verified_review else None,
        verified_by_name=verified_review.EmployeeProfile.display_name if verified_review else None,
        last_verified_at=verified_review.VerificationReview.created_at if verified_review else None,
        related_solutions=[
            RelatedSolution(
                challenge_id=row.id,
                title=row.title,
                updated_at=row.updated_at,
                technologies=related_technology_names.get(row.id, []),
            )
            for row in related_rows
        ],
        can_edit=can_edit_challenge(viewer, challenge),
        feedback=_feedback_summary(db, viewer, solution.id),
    ).model_dump(mode="json")


def _check_technologies(db: Session, technology_ids: list[UUID]) -> None:
    if not technology_ids:
        return
    found = set(db.scalars(select(Technology.id).where(Technology.id.in_(technology_ids), Technology.deleted_at.is_(None))))
    if found != set(technology_ids):
        raise HTTPException(status_code=422, detail={"code": "validation_error", "message": "One or more technologies are unavailable."})


def _check_scope(db: Session, department_id: UUID | None, team_id: UUID | None) -> None:
    if department_id is not None and db.get(Department, department_id) is None:
        raise HTTPException(status_code=422, detail={"code": "validation_error", "message": "The department is unavailable."})
    if team_id is not None:
        team = db.get(Team, team_id)
        if team is None or (department_id is not None and team.department_id != department_id):
            raise HTTPException(status_code=422, detail={"code": "validation_error", "message": "The team is unavailable for the selected department."})


def _has_searchable_content_change(challenge: Challenge, solution: Solution, payload: ChallengeUpdate) -> bool:
    challenge_fields = ("title", "problem_description", "symptoms", "exact_error_message", "environment")
    for field in challenge_fields:
        if field in payload.model_fields_set and getattr(challenge, field) != getattr(payload, field):
            return True
    if payload.solution is not None:
        for field, value in payload.solution.model_dump().items():
            if getattr(solution, field) != value:
                return True
    return payload.technology_ids is not None


def _try_embed_verified_solution(db: Session, settings: Settings, solution: Solution) -> str:
    if not settings.embeddings_enabled:
        return "disabled_until_configured"
    try:
        embed_verified_solution(db, solution_id=solution.id, adapter=_embedding_adapter(settings))
    except EmbeddingContentRejected:
        return "content_rejected"
    except EmbeddingUnavailable:
        return "unavailable"
    return "generated"


@router.get("/profiles/me", response_model=dict)
def get_my_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.scalar(select(EmployeeProfile).where(EmployeeProfile.user_id == current_user.id, EmployeeProfile.deleted_at.is_(None)))
    if profile is None:
        raise not_found()
    return {"data": _profile_response(db, current_user, profile), "meta": {}}


@router.get("/profiles", response_model=dict)
def list_profiles(
    query: str | None = Query(default=None, max_length=120),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    statement = (
        select(EmployeeProfile, Department, Team)
        .join(User, User.id == EmployeeProfile.user_id)
        .join(Department, Department.id == EmployeeProfile.department_id)
        .join(Team, Team.id == EmployeeProfile.team_id)
        .where(User.is_active.is_(True), EmployeeProfile.deleted_at.is_(None))
        .order_by(Department.name, Team.name, EmployeeProfile.display_name)
        .limit(120)
    )
    normalized = " ".join((query or "").split())
    if normalized:
        pattern = f"%{normalized}%"
        statement = statement.where(
            EmployeeProfile.display_name.ilike(pattern)
            | EmployeeProfile.job_title.ilike(pattern)
            | Department.name.ilike(pattern)
            | Team.name.ilike(pattern)
        )
    rows = db.execute(statement).all()
    data = [
        ProfileDirectoryItem(
            user_id=profile.user_id,
            display_name=profile.display_name,
            job_title=profile.job_title,
            team=team.name,
            department=department.name,
            contact_email=profile.contact_email,
            contact_handle=profile.contact_handle,
            skills=profile.skills or [],
            avatar_key=profile.avatar_key,
            initials=_initials(profile.display_name),
        ).model_dump(mode="json")
        for profile, department, team in rows
    ]
    return {"data": data, "meta": {"total": len(data)}}


@router.patch("/profiles/me", response_model=dict)
def update_my_profile(
    payload: ProfileUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.scalar(select(EmployeeProfile).where(EmployeeProfile.user_id == current_user.id, EmployeeProfile.deleted_at.is_(None)))
    if profile is None:
        raise not_found()
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "skills" and value is None:
            continue
        setattr(profile, field, value)
    profile.updated_at = datetime.now(UTC)
    audit_event(db, request, action="profile_updated", outcome="succeeded", actor_user_id=current_user.id, entity_type="employee_profile", entity_id=current_user.id)
    db.commit()
    db.refresh(profile)
    return {"data": _profile_response(db, current_user, profile), "meta": {}}


@router.get("/profiles/{user_id}", response_model=dict)
def get_profile(user_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.scalar(select(EmployeeProfile).where(EmployeeProfile.user_id == user_id, EmployeeProfile.deleted_at.is_(None)))
    if profile is None:
        raise not_found()
    return {"data": _profile_response(db, current_user, profile), "meta": {}}


@router.get("/technologies", response_model=dict)
def list_technologies(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    technologies = db.scalars(select(Technology).where(Technology.deleted_at.is_(None)).order_by(Technology.name)).all()
    return {"data": [{"id": str(item.id), "name": item.name, "slug": item.slug, "category": item.category} for item in technologies], "meta": {"page": 1, "page_size": len(technologies), "total": len(technologies), "has_next": False}}


@router.post("/challenges", status_code=201, response_model=dict)
def create_challenge(
    payload: ChallengeCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_technologies(db, payload.technology_ids)
    profile = db.scalar(select(EmployeeProfile).where(EmployeeProfile.user_id == current_user.id, EmployeeProfile.deleted_at.is_(None)))
    department_id = payload.department_id or (profile.department_id if profile else None)
    team_id = payload.team_id or (profile.team_id if profile else None)
    _check_scope(db, department_id, team_id)
    if payload.visibility == VisibilityLevel.DEPARTMENT and department_id is None:
        raise HTTPException(status_code=422, detail={"code": "validation_error", "message": "Department visibility requires an organization scope."})
    if payload.visibility == VisibilityLevel.TEAM and team_id is None:
        raise HTTPException(status_code=422, detail={"code": "validation_error", "message": "Team visibility requires an organization scope."})
    challenge = Challenge(
        title=payload.title.strip(), problem_description=payload.problem_description.strip(), symptoms=payload.symptoms.strip(),
        exact_error_message=payload.exact_error_message, environment=payload.environment, status=ContentStatus.DRAFT,
        visibility=payload.visibility, department_id=department_id, team_id=team_id, owner_user_id=current_user.id,
        created_by_user_id=current_user.id, updated_by_user_id=current_user.id,
    )
    db.add(challenge)
    db.flush()
    solution = Solution(challenge_id=challenge.id, root_cause=payload.solution.root_cause.strip(), resolution_steps=payload.solution.resolution_steps, code_snippets=payload.solution.code_snippets, prevention_notes=payload.solution.prevention_notes, solved_at=payload.solution.solved_at, status=ContentStatus.DRAFT, primary_owner_user_id=current_user.id)
    db.add(solution)
    for technology_id in set(payload.technology_ids):
        db.add(ChallengeTechnology(challenge_id=challenge.id, technology_id=technology_id))
    audit_event(db, request, action="challenge_draft_created", outcome="succeeded", actor_user_id=current_user.id, entity_type="challenge", entity_id=challenge.id)
    db.commit()
    db.refresh(challenge)
    return {"data": _detail(db, current_user, challenge), "meta": {}}


@router.get("/challenges/{challenge_id}", response_model=dict)
def get_challenge(challenge_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    challenge = load_challenge(db, challenge_id)
    require_view_challenge(db, current_user, challenge)
    return {"data": _detail(db, current_user, challenge), "meta": {}}


@router.get("/challenges", response_model=dict)
def list_challenges(
    status: ContentStatus | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(Challenge).where(Challenge.deleted_at.is_(None)).order_by(Challenge.updated_at.desc())
    if status is not None:
        query = query.where(Challenge.status == status)
    candidates = db.scalars(query).all()
    authorized = [item for item in candidates if can_view_challenge(db, current_user, item)]
    start = (page - 1) * page_size
    rows = [ChallengeSummary(id=item.id, title=item.title, status=item.status, visibility=item.visibility, owner_user_id=item.owner_user_id, updated_at=item.updated_at).model_dump(mode="json") for item in authorized[start : start + page_size]]
    return {"data": rows, "meta": {"page": page, "page_size": page_size, "total": len(authorized), "has_next": start + page_size < len(authorized)}}


@router.patch("/challenges/{challenge_id}", response_model=dict)
def update_challenge(
    challenge_id: UUID,
    payload: ChallengeUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    challenge = load_challenge(db, challenge_id)
    require_edit_challenge(current_user, challenge)
    if challenge.updated_at != payload.expected_updated_at:
        raise HTTPException(status_code=409, detail={"code": "state_conflict", "message": "This draft was updated elsewhere. Refresh and try again."})
    solution = load_solution(db, challenge.id)
    searchable_content_changed = _has_searchable_content_change(challenge, solution, payload)
    changes = payload.model_dump(exclude_none=True, exclude={"expected_updated_at", "technology_ids", "solution"})
    for field, value in changes.items():
        setattr(challenge, field, value.strip() if isinstance(value, str) else value)
    if challenge.visibility == VisibilityLevel.DEPARTMENT and challenge.department_id is None:
        raise HTTPException(status_code=422, detail={"code": "validation_error", "message": "Department visibility requires a department."})
    if challenge.visibility == VisibilityLevel.TEAM and challenge.team_id is None:
        raise HTTPException(status_code=422, detail={"code": "validation_error", "message": "Team visibility requires a team."})
    _check_scope(db, challenge.department_id, challenge.team_id)
    if payload.solution is not None:
        for field, value in payload.solution.model_dump().items():
            setattr(solution, field, value)
    if payload.technology_ids is not None:
        _check_technologies(db, payload.technology_ids)
        db.query(ChallengeTechnology).filter(ChallengeTechnology.challenge_id == challenge.id).delete()
        for technology_id in set(payload.technology_ids):
            db.add(ChallengeTechnology(challenge_id=challenge.id, technology_id=technology_id))
    if searchable_content_changed and challenge.status == ContentStatus.VERIFIED:
        challenge.status = ContentStatus.SUBMITTED
        solution.status = ContentStatus.SUBMITTED
        challenge.submitted_at = datetime.now(UTC)
        db.execute(delete(SolutionEmbedding).where(SolutionEmbedding.solution_id == solution.id))
    challenge.updated_by_user_id = current_user.id
    challenge.updated_at = datetime.now(UTC)
    audit_event(db, request, action="challenge_draft_updated", outcome="succeeded", actor_user_id=current_user.id, entity_type="challenge", entity_id=challenge.id)
    db.commit()
    db.refresh(challenge)
    return {"data": _detail(db, current_user, challenge), "meta": {}}


@router.post("/challenges/{challenge_id}/archive", response_model=dict)
def archive_challenge(
    challenge_id: UUID,
    payload: ArchiveRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    challenge = load_challenge(db, challenge_id)
    if current_user.role != AppRole.ADMINISTRATOR and (current_user.id != challenge.owner_user_id or challenge.status == ContentStatus.VERIFIED):
        raise forbidden_error()
    solution = load_solution(db, challenge.id)
    now = datetime.now(UTC)
    challenge.status = ContentStatus.ARCHIVED
    challenge.archived_at = now
    challenge.updated_by_user_id = current_user.id
    solution.status = ContentStatus.ARCHIVED
    audit_event(db, request, action="challenge_archived", outcome="succeeded", actor_user_id=current_user.id, entity_type="challenge", entity_id=challenge.id, metadata={"reason": payload.reason.strip()})
    db.commit()
    db.refresh(challenge)
    return {"data": _detail(db, current_user, challenge), "meta": {}}


@router.post("/challenges/{challenge_id}/submit", response_model=dict)
def submit_challenge(challenge_id: UUID, request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    challenge = load_challenge(db, challenge_id)
    require_edit_challenge(current_user, challenge)
    solution = load_solution(db, challenge.id)
    if not all([challenge.title.strip(), challenge.problem_description.strip(), challenge.symptoms.strip(), solution.root_cause.strip(), solution.resolution_steps]):
        raise HTTPException(status_code=422, detail={"code": "validation_error", "message": "Complete the required fields before submitting."})
    set_submitted(challenge, solution, current_user.id)
    audit_event(db, request, action="challenge_submitted", outcome="succeeded", actor_user_id=current_user.id, entity_type="challenge", entity_id=challenge.id)
    db.commit()
    db.refresh(challenge)
    return {"data": _detail(db, current_user, challenge), "meta": {}}


@router.post("/feedback", status_code=201, response_model=dict)
def record_feedback(
    payload: FeedbackCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    solution = db.get(Solution, payload.solution_id)
    if solution is None or solution.deleted_at is not None:
        raise not_found()
    challenge = load_challenge(db, solution.challenge_id)
    require_view_challenge(db, current_user, challenge)
    if payload.search_query_id is not None:
        query = db.get(SearchQuery, payload.search_query_id)
        if query is None or query.requested_by_user_id != current_user.id:
            raise not_found()
    feedback = db.scalar(
        select(Feedback).where(
            Feedback.solution_id == solution.id,
            Feedback.submitted_by_user_id == current_user.id,
        )
    )
    if feedback is None:
        feedback = Feedback(
            solution_id=solution.id,
            submitted_by_user_id=current_user.id,
            search_query_id=payload.search_query_id,
            value=payload.value,
            comment=payload.comment,
        )
        db.add(feedback)
    else:
        feedback.search_query_id = payload.search_query_id
        feedback.value = payload.value
        feedback.comment = payload.comment
        feedback.updated_at = datetime.now(UTC)
    audit_event(
        db,
        request,
        action="solution_feedback_recorded",
        outcome=payload.value.value,
        actor_user_id=current_user.id,
        entity_type="solution",
        entity_id=solution.id,
    )
    db.commit()
    db.refresh(feedback)
    return {
        "data": FeedbackResponse(
            id=feedback.id,
            solution_id=feedback.solution_id,
            value=feedback.value,
            comment=feedback.comment,
            updated_at=feedback.updated_at,
        ).model_dump(mode="json"),
        "meta": {},
    }


@router.post("/challenges/{challenge_id}/attachments", status_code=201, response_model=dict)
async def upload_attachment(
    challenge_id: UUID,
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    challenge = load_challenge(db, challenge_id)
    require_edit_challenge(current_user, challenge)
    if file.content_type not in settings.allowed_upload_types:
        raise HTTPException(status_code=415, detail={"code": "unsupported_file_type", "message": "This file type is not allowed."})
    content = await file.read(settings.max_upload_size_mb * 1024 * 1024 + 1)
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail={"code": "attachment_too_large", "message": "This file is larger than the allowed size."})
    if file.content_type == "application/pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=415, detail={"code": "unsupported_file_type", "message": "This file content does not match its type."})
    if file.content_type in {"text/plain", "text/markdown"}:
        try:
            content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(status_code=415, detail={"code": "unsupported_file_type", "message": "Text uploads must use UTF-8."}) from exc
    filename = sanitized_filename(file.filename)
    storage_key = f"{challenge.id}/{uuid4()}-{filename}"
    storage_path = Path(settings.upload_directory) / storage_key
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    storage_path.write_bytes(content)
    attachment = Attachment(challenge_id=challenge.id, uploaded_by_user_id=current_user.id, storage_key=storage_key, original_filename=filename, content_type=file.content_type, size_bytes=len(content), sha256=sha256(content).hexdigest(), status=AttachmentStatus.PENDING_SCAN)
    db.add(attachment)
    db.flush()
    audit_event(db, request, action="attachment_uploaded", outcome="pending_scan", actor_user_id=current_user.id, entity_type="attachment", entity_id=attachment.id)
    try:
        db.commit()
    except Exception:
        db.rollback()
        storage_path.unlink(missing_ok=True)
        raise
    db.refresh(attachment)
    return {"data": AttachmentResponse.model_validate(attachment).model_dump(mode="json"), "meta": {}}


@router.get("/challenges/{challenge_id}/attachments/{attachment_id}")
def download_attachment(challenge_id: UUID, attachment_id: UUID, request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    challenge = load_challenge(db, challenge_id)
    require_view_challenge(db, current_user, challenge)
    attachment = db.scalar(select(Attachment).where(Attachment.id == attachment_id, Attachment.challenge_id == challenge.id, Attachment.deleted_at.is_(None)))
    if attachment is None or attachment.status != AttachmentStatus.AVAILABLE:
        raise not_found()
    path = Path(settings.upload_directory) / attachment.storage_key
    if not path.is_file():
        raise not_found()
    audit_event(db, request, action="attachment_downloaded", outcome="succeeded", actor_user_id=current_user.id, entity_type="attachment", entity_id=attachment.id)
    db.commit()
    return FileResponse(path, media_type=attachment.content_type, filename=attachment.original_filename)


@router.get("/reviews/queue", response_model=dict)
def review_queue(current_user: User = Depends(require_roles(AppRole.REVIEWER, AppRole.ADMINISTRATOR)), db: Session = Depends(get_db)):
    submitted = db.scalars(select(Challenge).where(Challenge.status == ContentStatus.SUBMITTED, Challenge.deleted_at.is_(None)).order_by(Challenge.submitted_at)).all()
    rows = [ChallengeSummary(id=item.id, title=item.title, status=item.status, visibility=item.visibility, owner_user_id=item.owner_user_id, updated_at=item.updated_at).model_dump(mode="json") for item in submitted if can_review(db, current_user, item)]
    return {"data": rows, "meta": {"page": 1, "page_size": len(rows), "total": len(rows), "has_next": False}}


@router.post("/reviews", status_code=201, response_model=dict)
def review_challenge(
    payload: ReviewCreate,
    request: Request,
    current_user: User = Depends(require_roles(AppRole.REVIEWER, AppRole.ADMINISTRATOR)),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    solution = db.scalar(select(Solution).where(Solution.id == payload.solution_id, Solution.deleted_at.is_(None)))
    if solution is None:
        raise not_found()
    challenge = load_challenge(db, solution.challenge_id)
    if challenge.status != ContentStatus.SUBMITTED or not can_review(db, current_user, challenge):
        raise forbidden_error()
    review = VerificationReview(solution_id=solution.id, reviewer_user_id=current_user.id, decision=payload.decision, notes=payload.notes, visibility_after=payload.visibility_after)
    db.add(review)
    if payload.visibility_after is not None:
        challenge.visibility = payload.visibility_after
    if payload.decision == ReviewDecision.VERIFIED:
        challenge.status = ContentStatus.VERIFIED
        solution.status = ContentStatus.VERIFIED
    elif payload.decision == ReviewDecision.CHANGES_REQUESTED:
        challenge.status = ContentStatus.CHANGES_REQUESTED
        solution.status = ContentStatus.CHANGES_REQUESTED
    elif payload.decision == ReviewDecision.REJECTED:
        challenge.status = ContentStatus.REJECTED
        solution.status = ContentStatus.REJECTED
    else:
        challenge.status = ContentStatus.ARCHIVED
        solution.status = ContentStatus.ARCHIVED
    challenge.updated_by_user_id = current_user.id
    embedding_status = "not_applicable"
    if payload.decision == ReviewDecision.VERIFIED:
        db.flush()
        embedding_status = _try_embed_verified_solution(db, settings, solution)
    audit_event(
        db,
        request,
        action="verification_review_recorded",
        outcome=payload.decision.value,
        actor_user_id=current_user.id,
        entity_type="solution",
        entity_id=solution.id,
        metadata={"embedding_status": embedding_status},
    )
    db.commit()
    db.refresh(review)
    return {
        "data": {
            "id": str(review.id),
            "solution_id": str(solution.id),
            "decision": review.decision.value,
            "created_at": review.created_at.isoformat(),
            "embedding_status": embedding_status,
        },
        "meta": {},
    }
