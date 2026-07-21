from datetime import UTC, datetime
from uuid import uuid4
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.security import hash_password
from app.core.config import get_settings
from app.database.session import SessionLocal
from app.main import create_app
from app.models.auth import AppRole, AuditLog, RevokedToken, User
from app.models.repository import (
    Attachment,
    Challenge,
    ChallengeTechnology,
    Department,
    EmployeeProfile,
    SearchQuery,
    Solution,
    Team,
    Technology,
    VerificationReview,
    ContentStatus,
    VisibilityLevel,
)
from app.schemas.repository import SearchResult
from app.services.grounded_generation import GroundedAnswer


@pytest.fixture
def repository_fixture():
    suffix = str(uuid4())[:8]
    department = Department(id=uuid4(), name=f"Engineering {suffix}", slug=f"engineering-{suffix}")
    team = Team(id=uuid4(), department_id=department.id, name=f"Platform {suffix}", slug=f"platform-{suffix}")
    technology = Technology(id=uuid4(), name=f"Python {suffix}", slug=f"python-{suffix}", category="language")
    users = {
        "author": User(id=uuid4(), email=f"author-{suffix}@example.test", password_hash=hash_password("correct-password"), role=AppRole.EMPLOYEE, is_active=True),
        "reviewer": User(id=uuid4(), email=f"reviewer-{suffix}@example.test", password_hash=hash_password("correct-password"), role=AppRole.REVIEWER, is_active=True),
        "outsider": User(id=uuid4(), email=f"outsider-{suffix}@example.test", password_hash=hash_password("correct-password"), role=AppRole.EMPLOYEE, is_active=True),
    }
    with SessionLocal() as db:
        db.add_all([department, team, technology, *users.values()])
        db.flush()
        db.add_all([
            EmployeeProfile(user_id=user.id, display_name=key.title(), job_title="Engineer", department_id=department.id, team_id=team.id, contact_email=user.email)
            for key, user in users.items()
        ])
        db.commit()
    yield {"department": department, "team": team, "technology": technology, "users": users}
    ids = [user.id for user in users.values()]
    with SessionLocal() as db:
        attachment_keys = list(
            db.scalars(select(Attachment.storage_key).where(Attachment.uploaded_by_user_id.in_(ids)))
        )
        db.execute(delete(SearchQuery).where(SearchQuery.requested_by_user_id.in_(ids)))
        db.execute(delete(VerificationReview).where(VerificationReview.reviewer_user_id.in_(ids)))
        db.execute(delete(Attachment).where(Attachment.uploaded_by_user_id.in_(ids)))
        db.execute(delete(ChallengeTechnology).where(ChallengeTechnology.challenge_id.in_(db.query(Challenge.id).filter(Challenge.owner_user_id.in_(ids)))))
        db.execute(delete(Solution).where(Solution.primary_owner_user_id.in_(ids)))
        db.execute(delete(Challenge).where(Challenge.owner_user_id.in_(ids)))
        db.execute(delete(AuditLog).where(AuditLog.actor_user_id.in_(ids)))
        db.execute(delete(RevokedToken).where(RevokedToken.user_id.in_(ids)))
        db.execute(delete(EmployeeProfile).where(EmployeeProfile.user_id.in_(ids)))
        db.execute(delete(User).where(User.id.in_(ids)))
        db.execute(delete(Technology).where(Technology.id == technology.id))
        db.execute(delete(Team).where(Team.id == team.id))
        db.execute(delete(Department).where(Department.id == department.id))
        db.commit()
    for storage_key in attachment_keys:
        (Path(get_settings().upload_directory) / storage_key).unlink(missing_ok=True)


def _headers(client: TestClient, email: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": "correct-password"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


def _draft_payload(fixture, visibility="company"):
    return {
        "title": "Container startup fails after deployment",
        "problem_description": "The application container did not start after a deployment.",
        "symptoms": "The container exited before the readiness probe completed.",
        "exact_error_message": "ModuleNotFoundError: No module named 'service'",
        "environment": "Docker Compose, Python 3.12",
        "visibility": visibility,
        "technology_ids": [str(fixture["technology"].id)],
        "solution": {
            "root_cause": "The image copied the package into an unexpected path.",
            "resolution_steps": ["Correct the Docker COPY path.", "Rebuild and verify startup."],
            "code_snippets": ["COPY ./service /app/service"],
        },
    }


class _FakeEmbeddingAdapter:
    """Keeps repository tests deterministic and independent from AWS."""

    def __init__(self, settings):
        self.settings = SimpleNamespace(
            bedrock_embedding_model_id=settings.bedrock_embedding_model_id,
        )

    def embed(self, document: str) -> list[float]:
        return [0.0] * 1024


class _FakeGroundedGenerationAdapter:
    calls = 0

    def __init__(self, settings):
        self.settings = settings

    def generate(self, *, query, sources):
        type(self).calls += 1
        source_id = sources[0].solution_id
        return GroundedAnswer(summary=f"Use the verified technical resolution. [{source_id}]", citations=[source_id])


def test_author_draft_submit_review_and_authorized_detail(repository_fixture):
    client = TestClient(create_app())
    author_headers = _headers(client, repository_fixture["users"]["author"].email)
    reviewer_headers = _headers(client, repository_fixture["users"]["reviewer"].email)
    outsider_headers = _headers(client, repository_fixture["users"]["outsider"].email)

    created = client.post("/api/v1/challenges", headers=author_headers, json=_draft_payload(repository_fixture))
    assert created.status_code == 201
    draft = created.json()["data"]
    challenge_id = draft["id"]
    assert draft["status"] == "draft"

    update = client.patch(
        f"/api/v1/challenges/{challenge_id}",
        headers=author_headers,
        json={"expected_updated_at": draft["updated_at"], "title": "Container startup fails after deployment - fixed"},
    )
    assert update.status_code == 200
    submitted = client.post(f"/api/v1/challenges/{challenge_id}/submit", headers=author_headers)
    assert submitted.status_code == 200
    assert submitted.json()["data"]["status"] == "submitted"

    queue = client.get("/api/v1/reviews/queue", headers=reviewer_headers)
    assert queue.status_code == 200
    assert queue.json()["data"][0]["id"] == challenge_id
    solution_id = SessionLocal().query(Solution.id).filter(Solution.challenge_id == challenge_id).scalar()
    reviewed = client.post("/api/v1/reviews", headers=reviewer_headers, json={"solution_id": str(solution_id), "decision": "verified"})
    assert reviewed.status_code == 201

    visible = client.get(f"/api/v1/challenges/{challenge_id}", headers=outsider_headers)
    assert visible.status_code == 200
    assert visible.json()["data"]["solution"]["root_cause"].startswith("The image")
    browse = client.get("/api/v1/challenges", headers=outsider_headers)
    assert browse.status_code == 200
    assert browse.json()["data"][0]["id"] == challenge_id


def test_owner_and_attachment_authorization(repository_fixture):
    client = TestClient(create_app())
    author_headers = _headers(client, repository_fixture["users"]["author"].email)
    outsider_headers = _headers(client, repository_fixture["users"]["outsider"].email)
    created = client.post("/api/v1/challenges", headers=author_headers, json=_draft_payload(repository_fixture, "restricted"))
    challenge_id = created.json()["data"]["id"]

    denied = client.get(f"/api/v1/challenges/{challenge_id}", headers=outsider_headers)
    assert denied.status_code == 404
    invalid_upload = client.post(
        f"/api/v1/challenges/{challenge_id}/attachments", headers=author_headers,
        files={"file": ("evidence.exe", b"not an allowed file", "application/octet-stream")},
    )
    assert invalid_upload.status_code == 415
    accepted_upload = client.post(
        f"/api/v1/challenges/{challenge_id}/attachments", headers=author_headers,
        files={"file": ("evidence.txt", b"safe technical evidence", "text/plain")},
    )
    assert accepted_upload.status_code == 201
    assert accepted_upload.json()["data"]["status"] == "pending_scan"
    archived = client.post(f"/api/v1/challenges/{challenge_id}/archive", headers=author_headers, json={"reason": "Duplicate draft created during testing."})
    assert archived.status_code == 200
    assert archived.json()["data"]["status"] == "archived"


def test_profile_update_and_reviewer_cannot_review_own_submission(repository_fixture):
    client = TestClient(create_app())
    reviewer = repository_fixture["users"]["reviewer"]
    reviewer_headers = _headers(client, reviewer.email)
    profile = client.get("/api/v1/profiles/me", headers=reviewer_headers)
    assert profile.status_code == 200
    updated = client.patch("/api/v1/profiles/me", headers=reviewer_headers, json={"bio": "Maintains platform services."})
    assert updated.status_code == 200
    assert updated.json()["data"]["bio"] == "Maintains platform services."

    created = client.post("/api/v1/challenges", headers=reviewer_headers, json=_draft_payload(repository_fixture))
    challenge_id = created.json()["data"]["id"]
    assert client.post(f"/api/v1/challenges/{challenge_id}/submit", headers=reviewer_headers).status_code == 200
    solution_id = SessionLocal().query(Solution.id).filter(Solution.challenge_id == challenge_id).scalar()
    own_review = client.post("/api/v1/reviews", headers=reviewer_headers, json={"solution_id": str(solution_id), "decision": "verified"})
    assert own_review.status_code == 403


def test_hybrid_search_exact_match_filters_authorization_and_logs(repository_fixture, monkeypatch):
    monkeypatch.setattr("app.api.search.BedrockEmbeddingAdapter", _FakeEmbeddingAdapter)
    monkeypatch.setattr("app.api.search.BedrockGroundedGenerationAdapter", _FakeGroundedGenerationAdapter)
    client = TestClient(create_app())
    author_headers = _headers(client, repository_fixture["users"]["author"].email)
    reviewer_headers = _headers(client, repository_fixture["users"]["reviewer"].email)
    outsider_headers = _headers(client, repository_fixture["users"]["outsider"].email)

    created = client.post("/api/v1/challenges", headers=author_headers, json=_draft_payload(repository_fixture))
    challenge_id = created.json()["data"]["id"]
    assert client.post(f"/api/v1/challenges/{challenge_id}/submit", headers=author_headers).status_code == 200
    solution_id = SessionLocal().query(Solution.id).filter(Solution.challenge_id == challenge_id).scalar()
    assert client.post("/api/v1/reviews", headers=reviewer_headers, json={"solution_id": str(solution_id), "decision": "verified"}).status_code == 201

    searched = client.post("/api/v1/search", headers=outsider_headers, json={"query": "ModuleNotFoundError: No module named 'service'", "filters": {"verified_only": True}, "page": 1, "page_size": 10, "sort": "relevance", "include_summary": False})
    assert searched.status_code == 200
    payload = searched.json()
    assert payload["data"]["service_status"]["semantic_search"] == "available"
    assert payload["data"]["summary"] is None
    assert payload["data"]["results"][0]["challenge_id"] == challenge_id
    assert payload["data"]["results"][0]["match_reasons"][:2] == [
        "Exact error message contains the query",
        "Query terms match the documented issue",
    ]
    assert len(payload["data"]["results"][0]["match_reasons"]) <= 3
    assert payload["data"]["results"][0]["solver"]["display_name"] == "Author"

    summary_requested = client.post("/api/v1/search", headers=outsider_headers, json={"query": "Container startup deployment", "filters": {"verified_only": True}, "page": 1, "page_size": 10, "sort": "relevance", "include_summary": True})
    assert summary_requested.status_code == 200
    assert summary_requested.json()["data"]["summary_citations"]
    assert summary_requested.json()["data"]["service_status"]["grounded_summary"] == "available"

    query_log = client.get(f"/api/v1/search/{payload['data']['query_id']}", headers=outsider_headers)
    assert query_log.status_code == 200
    assert client.get(f"/api/v1/search/{payload['data']['query_id']}", headers=author_headers).status_code == 404

    restricted = client.post("/api/v1/challenges", headers=author_headers, json=_draft_payload(repository_fixture, "restricted"))
    restricted_id = restricted.json()["data"]["id"]
    assert client.post(f"/api/v1/challenges/{restricted_id}/submit", headers=author_headers).status_code == 200
    restricted_solution_id = SessionLocal().query(Solution.id).filter(Solution.challenge_id == restricted_id).scalar()
    assert client.post("/api/v1/reviews", headers=reviewer_headers, json={"solution_id": str(restricted_solution_id), "decision": "verified"}).status_code == 201

    _FakeGroundedGenerationAdapter.calls = 0
    denied = client.post("/api/v1/search", headers=outsider_headers, json={"query": "Container startup deployment", "filters": {"verified_only": True, "visibility": "restricted"}, "page": 1, "page_size": 10, "sort": "relevance", "include_summary": True})
    assert denied.status_code == 200
    assert denied.json()["data"]["no_answer"] is True
    assert denied.json()["data"]["service_status"]["grounded_summary"] == "not_run_no_answer"
    assert _FakeGroundedGenerationAdapter.calls == 0


def test_grounded_summary_uses_global_ranked_sources_not_only_current_page(repository_fixture, monkeypatch):
    client = TestClient(create_app())
    headers = _headers(client, repository_fixture["users"]["outsider"].email)
    author_headers = _headers(client, repository_fixture["users"]["author"].email)
    created = client.post("/api/v1/challenges", headers=author_headers, json=_draft_payload(repository_fixture))
    assert created.status_code == 201
    page_challenge_id = created.json()["data"]["id"]
    page_solution_id = SessionLocal().query(Solution.id).filter(Solution.challenge_id == page_challenge_id).scalar()
    globally_ranked_ids = [uuid4(), uuid4(), uuid4(), uuid4()]
    page_result = SearchResult(
        challenge_id=page_challenge_id, solution_id=page_solution_id, title="Visible page-two result",
        problem_excerpt="Problem", root_cause_excerpt="Cause", resolution_steps=["Resolve"],
        exact_error_message=None, status=ContentStatus.VERIFIED, visibility=VisibilityLevel.COMPANY,
        solved_at=None, updated_at=datetime.now(UTC),
        technologies=["Docker"], solver={"user_id": repository_fixture["users"]["author"].id, "display_name": "Author", "job_title": "Engineer"},
        match_reasons=["Query terms match the documented issue"], score=0.9,
    )
    captured: dict[str, list] = {}

    def capture_sources(db, *, solution_ids):
        captured["solution_ids"] = solution_ids
        return [SimpleNamespace(solution_id=solution_ids[0])]

    monkeypatch.setattr("app.api.search.BedrockEmbeddingAdapter", _FakeEmbeddingAdapter)
    monkeypatch.setattr(
        "app.api.search.execute_hybrid_search",
        lambda *args, **kwargs: ([page_result], 4, 1, 0.9, False, globally_ranked_ids),
    )
    monkeypatch.setattr("app.api.search.build_grounding_sources", capture_sources)
    monkeypatch.setattr("app.api.search.BedrockGroundedGenerationAdapter", _FakeGroundedGenerationAdapter)

    searched = client.post(
        "/api/v1/search", headers=headers,
        json={"query": "Docker package import", "filters": {"verified_only": True}, "page": 2, "page_size": 1, "sort": "relevance", "include_summary": True},
    )

    assert searched.status_code == 200
    assert captured["solution_ids"] == globally_ranked_ids[:3]
