from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.database.session import SessionLocal
from app.main import create_app
from app.models.auth import AppRole, AuditLog, RevokedToken, User
from app.models.repository import (
    Attachment,
    Challenge,
    ChallengeTechnology,
    ContentStatus,
    Department,
    EmployeeProfile,
    Feedback,
    SearchQuery,
    Solution,
    SolutionEmbedding,
    Team,
    Technology,
    VerificationReview,
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
    secondary_technology = Technology(id=uuid4(), name=f"Docker {suffix}", slug=f"docker-{suffix}", category="platform")
    users = {
        "author": User(id=uuid4(), email=f"author-{suffix}@example.test", password_hash=hash_password("correct-password"), role=AppRole.EMPLOYEE, is_active=True),
        "reviewer": User(id=uuid4(), email=f"reviewer-{suffix}@example.test", password_hash=hash_password("correct-password"), role=AppRole.REVIEWER, is_active=True),
        "outsider": User(id=uuid4(), email=f"outsider-{suffix}@example.test", password_hash=hash_password("correct-password"), role=AppRole.EMPLOYEE, is_active=True),
    }
    with SessionLocal() as db:
        db.add_all([department, team, technology, secondary_technology, *users.values()])
        db.flush()
        db.add_all([
            EmployeeProfile(user_id=user.id, display_name=key.title(), job_title="Engineer", department_id=department.id, team_id=team.id, contact_email=user.email)
            for key, user in users.items()
        ])
        db.commit()
    yield {
        "department": department,
        "team": team,
        "technology": technology,
        "secondary_technology": secondary_technology,
        "users": users,
    }
    ids = [user.id for user in users.values()]
    with SessionLocal() as db:
        attachment_keys = list(
            db.scalars(select(Attachment.storage_key).where(Attachment.uploaded_by_user_id.in_(ids)))
        )
        db.execute(delete(SearchQuery).where(SearchQuery.requested_by_user_id.in_(ids)))
        db.execute(delete(Feedback).where(Feedback.submitted_by_user_id.in_(ids)))
        db.execute(delete(VerificationReview).where(VerificationReview.reviewer_user_id.in_(ids)))
        db.execute(delete(Attachment).where(Attachment.uploaded_by_user_id.in_(ids)))
        db.execute(delete(ChallengeTechnology).where(ChallengeTechnology.challenge_id.in_(db.query(Challenge.id).filter(Challenge.owner_user_id.in_(ids)))))
        db.execute(delete(SolutionEmbedding).where(SolutionEmbedding.solution_id.in_(db.query(Solution.id).filter(Solution.primary_owner_user_id.in_(ids)))))
        db.execute(delete(Solution).where(Solution.primary_owner_user_id.in_(ids)))
        db.execute(delete(Challenge).where(Challenge.owner_user_id.in_(ids)))
        db.execute(delete(AuditLog).where(AuditLog.actor_user_id.in_(ids)))
        db.execute(delete(RevokedToken).where(RevokedToken.user_id.in_(ids)))
        db.execute(delete(EmployeeProfile).where(EmployeeProfile.user_id.in_(ids)))
        db.execute(delete(User).where(User.id.in_(ids)))
        db.execute(delete(Technology).where(Technology.id.in_([technology.id, secondary_technology.id])))
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

    @property
    def model_id(self):
        return self.settings.bedrock_embedding_model_id

    def embed(self, document: str, *, input_type: str = "passage") -> list[float]:
        return [0.0] * 1024


class _FakeGroundedGenerationAdapter:
    calls = 0

    def __init__(self, settings):
        self.settings = settings

    def generate(self, *, query, sources):
        type(self).calls += 1
        source_id = sources[0].solution_id
        return GroundedAnswer(summary=f"Use the verified technical resolution. [{source_id}]", citations=[source_id])


def _create_verified_search_record(repository_fixture, *, title: str, exact_error: str, technology_ids: list):
    """Insert an authorized verified record for endpoint-search regression tests."""
    challenge_id, solution_id = uuid4(), uuid4()
    owner = repository_fixture["users"]["author"]
    with SessionLocal() as db:
        db.add_all(
            [
                Challenge(
                    id=challenge_id,
                    title=title,
                    problem_description=f"Controlled endpoint-search problem: {exact_error}",
                    symptoms="A deterministic test symptom.",
                    exact_error_message=exact_error,
                    environment="Test environment",
                    status=ContentStatus.VERIFIED,
                    visibility=VisibilityLevel.COMPANY,
                    department_id=repository_fixture["department"].id,
                    team_id=repository_fixture["team"].id,
                    owner_user_id=owner.id,
                    created_by_user_id=owner.id,
                    updated_by_user_id=owner.id,
                ),
                Solution(
                    id=solution_id,
                    challenge_id=challenge_id,
                    root_cause="Controlled endpoint-search root cause.",
                    resolution_steps=["Apply the controlled resolution."],
                    code_snippets=[],
                    prevention_notes=None,
                    status=ContentStatus.VERIFIED,
                    primary_owner_user_id=owner.id,
                ),
                *[
                    ChallengeTechnology(challenge_id=challenge_id, technology_id=technology_id)
                    for technology_id in technology_ids
                ],
            ]
        )
        db.commit()
    return SimpleNamespace(challenge_id=challenge_id, solution_id=solution_id)


def _keyword_candidate(record, *, score: float) -> SearchResult:
    return SearchResult(
        challenge_id=record.challenge_id,
        solution_id=record.solution_id,
        title="Controlled candidate",
        problem_excerpt="Controlled problem",
        root_cause_excerpt="Controlled cause",
        resolution_steps=["Controlled resolution"],
        exact_error_message=None,
        status=ContentStatus.VERIFIED,
        visibility=VisibilityLevel.COMPANY,
        solved_at=None,
        updated_at=datetime.now(UTC),
        technologies=[],
        solver={"user_id": uuid4(), "display_name": "Controlled", "job_title": "Engineer"},
        match_reasons=["Keyword match"],
        score=score,
    )


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


def test_incomplete_draft_can_be_saved_but_not_submitted(repository_fixture):
    client = TestClient(create_app())
    author_headers = _headers(client, repository_fixture["users"]["author"].email)

    created = client.post(
        "/api/v1/challenges",
        headers=author_headers,
        json={
            "title": "Draft saved before the full solution is known",
            "technology_ids": [str(repository_fixture["technology"].id)],
            "solution": {},
        },
    )
    assert created.status_code == 201
    draft = created.json()["data"]
    assert draft["status"] == "draft"
    assert draft["problem_description"] == ""
    assert draft["solution"]["root_cause"] == ""
    assert draft["solution"]["resolution_steps"] == []

    updated = client.patch(
        f"/api/v1/challenges/{draft['id']}",
        headers=author_headers,
        json={
            "expected_updated_at": draft["updated_at"],
            "problem_description": "",
            "symptoms": "",
            "environment": "Development workspace",
            "solution": {"root_cause": "Still under investigation."},
        },
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["environment"] == "Development workspace"
    assert updated.json()["data"]["problem_description"] == ""

    submitted = client.post(f"/api/v1/challenges/{draft['id']}/submit", headers=author_headers)
    assert submitted.status_code == 422
    assert submitted.json()["error"]["code"] == "validation_error"


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


def test_employee_profile_returns_contact_stats_and_authorized_verified_solutions(repository_fixture, monkeypatch):
    monkeypatch.setattr("app.api.search.BedrockEmbeddingAdapter", _FakeEmbeddingAdapter)
    client = TestClient(create_app())
    author = repository_fixture["users"]["author"]
    author_headers = _headers(client, author.email)
    reviewer_headers = _headers(client, repository_fixture["users"]["reviewer"].email)
    outsider_headers = _headers(client, repository_fixture["users"]["outsider"].email)

    profile_update = client.patch(
        "/api/v1/profiles/me",
        headers=author_headers,
        json={
            "contact_handle": "@author",
            "skills": ["Docker troubleshooting", "Incident review"],
        },
    )
    assert profile_update.status_code == 200

    visible = client.post("/api/v1/challenges", headers=author_headers, json=_draft_payload(repository_fixture))
    visible_id = visible.json()["data"]["id"]
    assert client.post(f"/api/v1/challenges/{visible_id}/submit", headers=author_headers).status_code == 200
    visible_solution_id = SessionLocal().query(Solution.id).filter(Solution.challenge_id == visible_id).scalar()
    assert client.post(
        "/api/v1/reviews",
        headers=reviewer_headers,
        json={"solution_id": str(visible_solution_id), "decision": "verified"},
    ).status_code == 201

    restricted = client.post(
        "/api/v1/challenges",
        headers=author_headers,
        json=_draft_payload(repository_fixture, "restricted"),
    )
    restricted_id = restricted.json()["data"]["id"]
    assert client.post(f"/api/v1/challenges/{restricted_id}/submit", headers=author_headers).status_code == 200
    restricted_solution_id = SessionLocal().query(Solution.id).filter(Solution.challenge_id == restricted_id).scalar()
    assert client.post(
        "/api/v1/reviews",
        headers=reviewer_headers,
        json={"solution_id": str(restricted_solution_id), "decision": "verified"},
    ).status_code == 201

    profile = client.get(f"/api/v1/profiles/{author.id}", headers=outsider_headers)
    assert profile.status_code == 200
    body = profile.json()["data"]
    assert body["user_id"] == str(author.id)
    assert body["display_name"] == "Author"
    assert body["job_title"] == "Engineer"
    assert body["department"] == repository_fixture["department"].name
    assert body["team"] == repository_fixture["team"].name
    assert body["contact_email"] == author.email
    assert body["contact_handle"] == "@author"
    assert body["skills"] == ["Docker troubleshooting", "Incident review"]
    assert body["initials"] == "A"
    assert body["helpful_contribution_count"] == 0
    assert str(visible_id) in {item["challenge_id"] for item in body["verified_solutions"]}
    assert str(restricted_id) not in {item["challenge_id"] for item in body["verified_solutions"]}
    assert repository_fixture["technology"].name in body["technologies"]

    searched = client.post(
        "/api/v1/search",
        headers=outsider_headers,
        json={
            "query": "ModuleNotFoundError: No module named 'service'",
            "filters": {
                "verified_only": True,
                "technology_ids": [str(repository_fixture["technology"].id)],
            },
            "include_summary": False,
        },
    )
    assert searched.status_code == 200
    solver = next(
        result["solver"]
        for result in searched.json()["data"]["results"]
        if result["challenge_id"] == str(visible_id)
    )
    assert solver["team"] == repository_fixture["team"].name
    assert solver["department"] == repository_fixture["department"].name
    assert solver["contact_email"] == author.email
    assert solver["contact_handle"] == "@author"
    assert solver["initials"] == "A"


def test_solution_feedback_can_be_created_and_changed(repository_fixture):
    client = TestClient(create_app())
    author_headers = _headers(client, repository_fixture["users"]["author"].email)
    reviewer_headers = _headers(client, repository_fixture["users"]["reviewer"].email)
    outsider_headers = _headers(client, repository_fixture["users"]["outsider"].email)

    created = client.post("/api/v1/challenges", headers=author_headers, json=_draft_payload(repository_fixture))
    challenge_id = created.json()["data"]["id"]
    assert client.post(f"/api/v1/challenges/{challenge_id}/submit", headers=author_headers).status_code == 200
    solution_id = SessionLocal().query(Solution.id).filter(Solution.challenge_id == challenge_id).scalar()
    assert client.post(
        "/api/v1/reviews",
        headers=reviewer_headers,
        json={"solution_id": str(solution_id), "decision": "verified"},
    ).status_code == 201

    resolved = client.post(
        "/api/v1/feedback",
        headers=outsider_headers,
        json={"solution_id": str(solution_id), "value": "resolved_my_issue", "comment": "This fixed the issue."},
    )
    assert resolved.status_code == 201
    assert resolved.json()["data"]["value"] == "resolved_my_issue"

    detail = client.get(f"/api/v1/challenges/{challenge_id}", headers=outsider_headers)
    assert detail.status_code == 200
    assert detail.json()["data"]["feedback"]["resolved_my_issue"] == 1
    assert detail.json()["data"]["feedback"]["current_user_feedback"]["comment"] == "This fixed the issue."

    changed = client.post(
        "/api/v1/feedback",
        headers=outsider_headers,
        json={"solution_id": str(solution_id), "value": "not_helpful", "comment": "Needs more detail."},
    )
    assert changed.status_code == 201
    assert changed.json()["data"]["id"] == resolved.json()["data"]["id"]

    updated_detail = client.get(f"/api/v1/challenges/{challenge_id}", headers=outsider_headers)
    assert updated_detail.json()["data"]["feedback"]["resolved_my_issue"] == 0
    assert updated_detail.json()["data"]["feedback"]["not_helpful"] == 1


def test_verified_technical_edit_returns_solution_to_review_and_clears_stale_embedding(repository_fixture):
    client = TestClient(create_app())
    author_headers = _headers(client, repository_fixture["users"]["author"].email)
    reviewer_headers = _headers(client, repository_fixture["users"]["reviewer"].email)

    created = client.post("/api/v1/challenges", headers=author_headers, json=_draft_payload(repository_fixture))
    challenge_id = created.json()["data"]["id"]
    assert client.post(f"/api/v1/challenges/{challenge_id}/submit", headers=author_headers).status_code == 200
    solution_id = SessionLocal().query(Solution.id).filter(Solution.challenge_id == challenge_id).scalar()
    assert client.post("/api/v1/reviews", headers=reviewer_headers, json={"solution_id": str(solution_id), "decision": "verified"}).status_code == 201

    with SessionLocal() as db:
        db.add(
            SolutionEmbedding(
                solution_id=solution_id,
                searchable_text="stale verified text",
                embedding=[0.0] * 1024,
                embedding_model="test-model",
                content_hash="stale-hash",
            )
        )
        db.commit()

    detail = client.get(f"/api/v1/challenges/{challenge_id}", headers=author_headers).json()["data"]
    changed = client.patch(
        f"/api/v1/challenges/{challenge_id}",
        headers=author_headers,
        json={
            "expected_updated_at": detail["updated_at"],
            "problem_description": "The verified problem statement was materially corrected.",
        },
    )

    assert changed.status_code == 200
    assert changed.json()["data"]["status"] == "submitted"
    assert changed.json()["data"]["verified_by_user_id"] is None
    assert changed.json()["data"]["verified_by_name"] is None
    assert changed.json()["data"]["last_verified_at"] is None
    assert any(review["decision"] == "verified" for review in changed.json()["data"]["review_history"])
    assert client.get("/api/v1/reviews/queue", headers=reviewer_headers).json()["data"][0]["id"] == challenge_id
    with SessionLocal() as db:
        assert db.scalar(select(SolutionEmbedding.id).where(SolutionEmbedding.solution_id == solution_id)) is None


def test_request_changes_edit_resubmit_approve_search_profile_and_feedback(repository_fixture, monkeypatch):
    monkeypatch.setattr("app.api.search.BedrockEmbeddingAdapter", _FakeEmbeddingAdapter)
    client = TestClient(create_app())
    author = repository_fixture["users"]["author"]
    author_headers = _headers(client, author.email)
    reviewer_headers = _headers(client, repository_fixture["users"]["reviewer"].email)
    outsider_headers = _headers(client, repository_fixture["users"]["outsider"].email)

    created = client.post("/api/v1/challenges", headers=author_headers, json=_draft_payload(repository_fixture))
    challenge_id = created.json()["data"]["id"]
    assert client.post(f"/api/v1/challenges/{challenge_id}/submit", headers=author_headers).status_code == 200
    solution_id = SessionLocal().query(Solution.id).filter(Solution.challenge_id == challenge_id).scalar()

    changes = client.post(
        "/api/v1/reviews",
        headers=reviewer_headers,
        json={"solution_id": str(solution_id), "decision": "changes_requested", "notes": "Add the exact verification step."},
    )
    assert changes.status_code == 201
    returned = client.get(f"/api/v1/challenges/{challenge_id}", headers=author_headers).json()["data"]
    assert returned["status"] == "changes_requested"
    assert returned["review_history"][0]["notes"] == "Add the exact verification step."

    edited = client.patch(
        f"/api/v1/challenges/{challenge_id}",
        headers=author_headers,
        json={
            "expected_updated_at": returned["updated_at"],
            "solution": {
                "root_cause": "The Docker image copied the package into an unexpected path.",
                "resolution_steps": ["Correct the Docker COPY path.", "Rebuild the image.", "Confirm the service imports on startup."],
                "code_snippets": ["python -c \"import service\""],
            },
        },
    )
    assert edited.status_code == 200
    assert client.post(f"/api/v1/challenges/{challenge_id}/submit", headers=author_headers).status_code == 200
    approved = client.post("/api/v1/reviews", headers=reviewer_headers, json={"solution_id": str(solution_id), "decision": "verified"})
    assert approved.status_code == 201

    searched = client.post(
        "/api/v1/search",
        headers=outsider_headers,
        json={"query": "ModuleNotFoundError: No module named 'service'", "include_summary": False},
    )
    assert searched.status_code == 200
    assert any(result["challenge_id"] == challenge_id for result in searched.json()["data"]["results"])

    profile = client.get(f"/api/v1/profiles/{author.id}", headers=outsider_headers)
    assert profile.status_code == 200
    assert any(item["challenge_id"] == challenge_id for item in profile.json()["data"]["verified_solutions"])

    feedback = client.post(
        "/api/v1/feedback",
        headers=outsider_headers,
        json={"solution_id": str(solution_id), "value": "helpful", "comment": "The added verification step helped."},
    )
    assert feedback.status_code == 201
    detail = client.get(f"/api/v1/challenges/{challenge_id}", headers=outsider_headers)
    assert detail.json()["data"]["feedback"]["helpful"] == 1


def test_review_approval_attempts_embedding_when_bedrock_is_configured(repository_fixture, monkeypatch):
    client = TestClient(create_app())
    settings = Settings(
        **{
            "APP_ENV": "test",
            "JWT" + "_SECRET": "fictional",
            "BEDROCK_EMBEDDINGS_ENABLED": True,
            "AWS_REGION": "us-east-1",
            "BEDROCK_EMBEDDING_MODEL_ID": "amazon.titan-embed-text-v2:0",
            "BEDROCK_EMBEDDING_DIMENSIONS": 1024,
        }
    )
    app = client.app
    app.dependency_overrides[get_settings] = lambda: settings
    calls: list[str] = []

    class FakeEmbeddingAdapter:
        def __init__(self, configured_settings):
            assert configured_settings.bedrock_embeddings_enabled is True

    def fake_embed(db, *, solution_id, adapter):
        calls.append(str(solution_id))
        return object(), True

    monkeypatch.setattr("app.api.repository.BedrockEmbeddingAdapter", FakeEmbeddingAdapter)
    monkeypatch.setattr("app.api.repository.embed_verified_solution", fake_embed)

    author_headers = _headers(client, repository_fixture["users"]["author"].email)
    reviewer_headers = _headers(client, repository_fixture["users"]["reviewer"].email)
    created = client.post("/api/v1/challenges", headers=author_headers, json=_draft_payload(repository_fixture))
    challenge_id = created.json()["data"]["id"]
    assert client.post(f"/api/v1/challenges/{challenge_id}/submit", headers=author_headers).status_code == 200
    solution_id = SessionLocal().query(Solution.id).filter(Solution.challenge_id == challenge_id).scalar()

    reviewed = client.post("/api/v1/reviews", headers=reviewer_headers, json={"solution_id": str(solution_id), "decision": "verified"})

    assert reviewed.status_code == 201
    assert reviewed.json()["data"]["embedding_status"] == "generated"
    assert calls == [str(solution_id)]
    app.dependency_overrides.clear()


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

    searched = client.post(
        "/api/v1/search",
        headers=outsider_headers,
        json={
            "query": "ModuleNotFoundError: No module named 'service'",
            "filters": {
                "verified_only": True,
                "technology_ids": [str(repository_fixture["technology"].id)],
            },
            "page": 1,
            "page_size": 10,
            "sort": "relevance",
            "include_summary": False,
        },
    )
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


def test_search_api_serializes_one_and_multiple_complete_technology_names(repository_fixture, monkeypatch):
    """The endpoint must never leak PostgreSQL array literals or character arrays."""
    monkeypatch.setattr("app.api.search.BedrockEmbeddingAdapter", _FakeEmbeddingAdapter)
    client = TestClient(create_app())
    headers = _headers(client, repository_fixture["users"]["outsider"].email)
    one_technology = _create_verified_search_record(
        repository_fixture,
        title="One complete technology API result",
        exact_error="endpoint-one-technology-marker",
        technology_ids=[repository_fixture["technology"].id],
    )
    multiple_technologies = _create_verified_search_record(
        repository_fixture,
        title="Multiple complete technologies API result",
        exact_error="endpoint-multiple-technologies-marker",
        technology_ids=[repository_fixture["technology"].id, repository_fixture["secondary_technology"].id],
    )

    one_response = client.post(
        "/api/v1/search",
        headers=headers,
        json={"query": "endpoint-one-technology-marker", "include_summary": False},
    )
    assert one_response.status_code == 200
    one_result = next(
        result for result in one_response.json()["data"]["results"] if result["solution_id"] == str(one_technology.solution_id)
    )
    assert one_result["technologies"] == [repository_fixture["technology"].name]

    multiple_response = client.post(
        "/api/v1/search",
        headers=headers,
        json={"query": "endpoint-multiple-technologies-marker", "include_summary": False},
    )
    assert multiple_response.status_code == 200
    multiple_result = next(
        result
        for result in multiple_response.json()["data"]["results"]
        if result["solution_id"] == str(multiple_technologies.solution_id)
    )
    assert set(multiple_result["technologies"]) == {
        repository_fixture["technology"].name,
        repository_fixture["secondary_technology"].name,
    }
    assert all(len(name) > 1 for name in multiple_result["technologies"])


def test_search_api_applies_eligibility_before_pagination_and_reports_no_answer(repository_fixture, monkeypatch):
    """Endpoint metadata must derive from the eligible, deduplicated result set."""
    monkeypatch.setattr("app.api.search.BedrockEmbeddingAdapter", _FakeEmbeddingAdapter)
    client = TestClient(create_app())
    headers = _headers(client, repository_fixture["users"]["outsider"].email)
    eligible_first = _create_verified_search_record(
        repository_fixture,
        title="First eligible endpoint result",
        exact_error="endpoint-eligibility-marker-one",
        technology_ids=[repository_fixture["technology"].id],
    )
    eligible_second = _create_verified_search_record(
        repository_fixture,
        title="Second eligible endpoint result",
        exact_error="endpoint-eligibility-marker-two",
        technology_ids=[repository_fixture["technology"].id],
    )
    ineligible = _create_verified_search_record(
        repository_fixture,
        title="Ineligible endpoint result",
        exact_error="endpoint-eligibility-marker-three",
        technology_ids=[repository_fixture["technology"].id],
    )

    candidates = [
        _keyword_candidate(eligible_first, score=0.2),
        _keyword_candidate(eligible_first, score=1.0),
        _keyword_candidate(eligible_second, score=0.8),
        _keyword_candidate(ineligible, score=0.0),
    ]
    monkeypatch.setattr(
        "app.services.search.execute_keyword_search",
        lambda *args, **kwargs: (candidates, len(candidates), 0),
    )

    first_page = client.post(
        "/api/v1/search",
        headers=headers,
        json={"query": "eligible endpoint records", "page": 1, "page_size": 1, "include_summary": False},
    )
    assert first_page.status_code == 200
    first_payload = first_page.json()
    assert first_payload["meta"] == {"page": 1, "page_size": 1, "total": 2, "has_next": True}
    assert first_payload["data"]["no_answer"] is False
    assert first_payload["data"]["results"][0]["solution_id"] == str(eligible_first.solution_id)

    second_page = client.post(
        "/api/v1/search",
        headers=headers,
        json={"query": "eligible endpoint records", "page": 2, "page_size": 1, "include_summary": False},
    )
    assert second_page.status_code == 200
    second_payload = second_page.json()
    assert second_payload["meta"] == {"page": 2, "page_size": 1, "total": 2, "has_next": False}
    assert second_payload["data"]["results"][0]["solution_id"] == str(eligible_second.solution_id)
    returned_ids = {
        first_payload["data"]["results"][0]["solution_id"],
        second_payload["data"]["results"][0]["solution_id"],
    }
    assert returned_ids == {str(eligible_first.solution_id), str(eligible_second.solution_id)}
    assert str(ineligible.solution_id) not in returned_ids

    monkeypatch.setattr(
        "app.services.search.execute_keyword_search",
        lambda *args, **kwargs: ([_keyword_candidate(ineligible, score=0.0)], 1, 0),
    )
    no_answer = client.post(
        "/api/v1/search",
        headers=headers,
        json={"query": "ineligible endpoint record", "page": 1, "page_size": 1, "include_summary": False},
    )
    assert no_answer.status_code == 200
    no_answer_payload = no_answer.json()
    assert no_answer_payload["data"]["no_answer"] is True
    assert no_answer_payload["data"]["results"] == []
    assert no_answer_payload["meta"] == {"page": 1, "page_size": 1, "total": 0, "has_next": False}
