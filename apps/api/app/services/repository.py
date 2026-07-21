from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import forbidden_error
from app.models.auth import AppRole, User
from app.models.repository import (
    Challenge,
    ContentStatus,
    EmployeeProfile,
    Solution,
    SolutionContributor,
    VisibilityLevel,
)


def not_found() -> HTTPException:
    return HTTPException(status_code=404, detail={"code": "not_found", "message": "This resource is not available."})


def get_active_profile(db: Session, user_id: UUID) -> EmployeeProfile | None:
    return db.scalar(select(EmployeeProfile).where(EmployeeProfile.user_id == user_id, EmployeeProfile.deleted_at.is_(None)))


def load_challenge(db: Session, challenge_id: UUID) -> Challenge:
    challenge = db.scalar(select(Challenge).where(Challenge.id == challenge_id, Challenge.deleted_at.is_(None)))
    if challenge is None:
        raise not_found()
    return challenge


def load_solution(db: Session, challenge_id: UUID) -> Solution:
    solution = db.scalar(select(Solution).where(Solution.challenge_id == challenge_id, Solution.deleted_at.is_(None)))
    if solution is None:
        raise not_found()
    return solution


def can_review(db: Session, reviewer: User, challenge: Challenge) -> bool:
    if reviewer.role == AppRole.ADMINISTRATOR:
        return True
    if reviewer.role != AppRole.REVIEWER or reviewer.id == challenge.owner_user_id:
        return False
    reviewer_profile = get_active_profile(db, reviewer.id)
    if reviewer_profile is None:
        return False
    if challenge.team_id is not None:
        return challenge.team_id == reviewer_profile.team_id
    return challenge.department_id == reviewer_profile.department_id


def can_view_challenge(db: Session, viewer: User, challenge: Challenge) -> bool:
    if viewer.role == AppRole.ADMINISTRATOR or viewer.id == challenge.owner_user_id:
        return True
    if challenge.status != ContentStatus.VERIFIED:
        return can_review(db, viewer, challenge)
    if challenge.visibility == VisibilityLevel.COMPANY:
        return True
    if challenge.visibility == VisibilityLevel.ADMINISTRATOR:
        return False
    profile = get_active_profile(db, viewer.id)
    if profile is None:
        return False
    if challenge.visibility == VisibilityLevel.DEPARTMENT:
        return challenge.department_id == profile.department_id
    if challenge.visibility == VisibilityLevel.TEAM:
        return challenge.team_id == profile.team_id
    if challenge.visibility == VisibilityLevel.RESTRICTED:
        return db.scalar(
            select(SolutionContributor.solution_id).where(
                SolutionContributor.solution_id == select(Solution.id).where(Solution.challenge_id == challenge.id).scalar_subquery(),
                SolutionContributor.user_id == viewer.id,
            )
        ) is not None
    return False


def require_view_challenge(db: Session, viewer: User, challenge: Challenge) -> None:
    if not can_view_challenge(db, viewer, challenge):
        raise not_found()


def require_edit_challenge(user: User, challenge: Challenge) -> None:
    if user.role == AppRole.ADMINISTRATOR:
        return
    if user.id != challenge.owner_user_id or challenge.status not in {ContentStatus.DRAFT, ContentStatus.CHANGES_REQUESTED}:
        raise forbidden_error()


def sanitized_filename(filename: str | None) -> str:
    value = Path(filename or "upload").name.strip().replace("\x00", "")
    if not value or value in {".", ".."}:
        return "upload"
    return value[:255]


def set_submitted(challenge: Challenge, solution: Solution, actor_id: UUID) -> None:
    now = datetime.now(UTC)
    challenge.status = ContentStatus.SUBMITTED
    challenge.submitted_at = now
    challenge.updated_by_user_id = actor_id
    solution.status = ContentStatus.SUBMITTED
