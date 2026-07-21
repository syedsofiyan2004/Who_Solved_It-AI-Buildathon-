from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select
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
    ReviewDecision,
    Solution,
    Technology,
    Team,
    VerificationReview,
    VisibilityLevel,
)
from app.schemas.repository import (
    AttachmentResponse,
    ChallengeCreate,
    ChallengeDetail,
    ChallengeSummary,
    ChallengeUpdate,
    ArchiveRequest,
    ProfileResponse,
    ProfileUpdate,
    ReviewCreate,
    SolutionInput,
)
from app.services.audit import audit_event
from app.services.repository import (
    can_view_challenge,
    can_review,
    load_challenge,
    load_solution,
    not_found,
    require_edit_challenge,
    require_view_challenge,
    sanitized_filename,
    set_submitted,
)

router = APIRouter(tags=["knowledge repository"])


def _profile_response(profile: EmployeeProfile) -> dict:
    return ProfileResponse.model_validate(profile).model_dump(mode="json")


def _solution_input(solution: Solution) -> SolutionInput:
    return SolutionInput(
        root_cause=solution.root_cause,
        resolution_steps=solution.resolution_steps,
        code_snippets=solution.code_snippets,
        prevention_notes=solution.prevention_notes,
        solved_at=solution.solved_at,
    )


def _detail(db: Session, challenge: Challenge) -> dict:
    solution = load_solution(db, challenge.id)
    technology_ids = list(db.scalars(select(ChallengeTechnology.technology_id).where(ChallengeTechnology.challenge_id == challenge.id)))
    attachment_count = db.scalar(select(func.count(Attachment.id)).where(Attachment.challenge_id == challenge.id, Attachment.deleted_at.is_(None))) or 0
    return ChallengeDetail(
        id=challenge.id,
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
        attachment_count=attachment_count,
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


@router.get("/profiles/me", response_model=dict)
def get_my_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.scalar(select(EmployeeProfile).where(EmployeeProfile.user_id == current_user.id, EmployeeProfile.deleted_at.is_(None)))
    if profile is None:
        raise not_found()
    return {"data": _profile_response(profile), "meta": {}}


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
        setattr(profile, field, value)
    profile.updated_at = datetime.now(UTC)
    audit_event(db, request, action="profile_updated", outcome="succeeded", actor_user_id=current_user.id, entity_type="employee_profile", entity_id=current_user.id)
    db.commit()
    db.refresh(profile)
    return {"data": _profile_response(profile), "meta": {}}


@router.get("/profiles/{user_id}", response_model=dict)
def get_profile(user_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.scalar(select(EmployeeProfile).where(EmployeeProfile.user_id == user_id, EmployeeProfile.deleted_at.is_(None)))
    if profile is None:
        raise not_found()
    return {"data": _profile_response(profile), "meta": {}}


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
    return {"data": _detail(db, challenge), "meta": {}}


@router.get("/challenges/{challenge_id}", response_model=dict)
def get_challenge(challenge_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    challenge = load_challenge(db, challenge_id)
    require_view_challenge(db, current_user, challenge)
    return {"data": _detail(db, challenge), "meta": {}}


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
    changes = payload.model_dump(exclude_none=True, exclude={"expected_updated_at", "technology_ids", "solution"})
    for field, value in changes.items():
        setattr(challenge, field, value.strip() if isinstance(value, str) else value)
    if challenge.visibility == VisibilityLevel.DEPARTMENT and challenge.department_id is None:
        raise HTTPException(status_code=422, detail={"code": "validation_error", "message": "Department visibility requires a department."})
    if challenge.visibility == VisibilityLevel.TEAM and challenge.team_id is None:
        raise HTTPException(status_code=422, detail={"code": "validation_error", "message": "Team visibility requires a team."})
    _check_scope(db, challenge.department_id, challenge.team_id)
    solution = load_solution(db, challenge.id)
    if payload.solution is not None:
        for field, value in payload.solution.model_dump().items():
            setattr(solution, field, value)
    if payload.technology_ids is not None:
        _check_technologies(db, payload.technology_ids)
        db.query(ChallengeTechnology).filter(ChallengeTechnology.challenge_id == challenge.id).delete()
        for technology_id in set(payload.technology_ids):
            db.add(ChallengeTechnology(challenge_id=challenge.id, technology_id=technology_id))
    challenge.updated_by_user_id = current_user.id
    challenge.updated_at = datetime.now(UTC)
    audit_event(db, request, action="challenge_draft_updated", outcome="succeeded", actor_user_id=current_user.id, entity_type="challenge", entity_id=challenge.id)
    db.commit()
    db.refresh(challenge)
    return {"data": _detail(db, challenge), "meta": {}}


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
    return {"data": _detail(db, challenge), "meta": {}}


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
    return {"data": _detail(db, challenge), "meta": {}}


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
def review_challenge(payload: ReviewCreate, request: Request, current_user: User = Depends(require_roles(AppRole.REVIEWER, AppRole.ADMINISTRATOR)), db: Session = Depends(get_db)):
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
    audit_event(db, request, action="verification_review_recorded", outcome=payload.decision.value, actor_user_id=current_user.id, entity_type="solution", entity_id=solution.id)
    db.commit()
    db.refresh(review)
    return {"data": {"id": str(review.id), "solution_id": str(solution.id), "decision": review.decision.value, "created_at": review.created_at.isoformat()}, "meta": {}}
