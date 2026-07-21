import io
from uuid import uuid4

import pytest
from sqlalchemy import delete

from app.core.config import Settings
from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.auth import AppRole, User
from app.models.repository import Challenge, ContentStatus, Department, EmployeeProfile, Solution, SolutionEmbedding, Team, Technology, ChallengeTechnology, VisibilityLevel
from app.services.embeddings import BedrockEmbeddingAdapter, EmbeddingContentRejected, EmbeddingUnavailable, embed_verified_solution


BASE_VALUES = {
    "DATABASE_URL": "postgresql+psycopg://app_user:<password>@postgres:5432/knowledge_platform",
    "JWT_SECRET": "<test-only-jwt-secret>",
    "BEDROCK_EMBEDDINGS_ENABLED": True,
    "AWS_REGION": "us-east-1",
    "BEDROCK_EMBEDDING_MODEL_ID": "amazon.titan-embed-text-v2:0",
    "BEDROCK_EMBEDDING_DIMENSIONS": 3,
}


class FakeBedrockClient:
    def __init__(self, values):
        self.values = values
        self.calls = 0

    def invoke_model(self, **kwargs):
        self.calls += 1
        return {"body": io.BytesIO(("{\"embedding\": " + str(self.values).replace("'", "\"") + "}").encode())}


def test_adapter_validates_provider_dimension_and_secret_content():
    adapter = BedrockEmbeddingAdapter(Settings(**BASE_VALUES), client=FakeBedrockClient([0.1, 0.2, 0.3]))
    assert adapter.embed("technical document") == [0.1, 0.2, 0.3]
    with pytest.raises(EmbeddingContentRejected):
        adapter.embed("password=do-not-embed")
    with pytest.raises(EmbeddingUnavailable):
        BedrockEmbeddingAdapter(Settings(**BASE_VALUES), client=FakeBedrockClient([0.1])).embed("technical document")


def test_verified_solution_embedding_is_hashed_deduplicated_and_stored_in_pgvector():
    suffix = str(uuid4())[:8]
    department_id, team_id, user_id, technology_id, challenge_id, solution_id = [uuid4() for _ in range(6)]
    user = User(id=user_id, email=f"embedding-{suffix}@example.test", password_hash=hash_password("correct-password"), role=AppRole.EMPLOYEE, is_active=True)
    with SessionLocal() as db:
        db.add(Department(id=department_id, name=f"Embedding {suffix}", slug=f"embedding-{suffix}"))
        db.flush()
        db.add_all([
            Team(id=team_id, department_id=department_id, name=f"Embedding Team {suffix}", slug=f"embedding-team-{suffix}"),
            user,
            Technology(id=technology_id, name=f"Python {suffix}", slug=f"python-embedding-{suffix}", category="language"),
        ])
        db.flush()
        db.add(EmployeeProfile(user_id=user_id, display_name="Embedding Engineer", job_title="Engineer", department_id=department_id, team_id=team_id, contact_email=user.email))
        db.flush()
        db.add_all([
            Challenge(id=challenge_id, title="Embedding test incident", problem_description="A fictional Python service failed to start.", symptoms="The process exited.", exact_error_message="Import error", environment="Python", status=ContentStatus.VERIFIED, visibility=VisibilityLevel.COMPANY, department_id=department_id, team_id=team_id, owner_user_id=user_id, created_by_user_id=user_id, updated_by_user_id=user_id),
            Solution(id=solution_id, challenge_id=challenge_id, root_cause="A package was absent.", resolution_steps=["Install the package."], code_snippets=[], prevention_notes=None, status=ContentStatus.VERIFIED, primary_owner_user_id=user_id),
            ChallengeTechnology(challenge_id=challenge_id, technology_id=technology_id),
        ])
        db.commit()
        adapter = BedrockEmbeddingAdapter(Settings(**BASE_VALUES), client=FakeBedrockClient([0.1, 0.2, 0.3]))
        embedding, created = embed_verified_solution(db, solution_id=solution_id, adapter=adapter)
        db.commit()
        assert created is True
        assert embedding.searchable_text.startswith("Title: Embedding test incident")
        _, created_again = embed_verified_solution(db, solution_id=solution_id, adapter=adapter)
        assert created_again is False
        db.execute(delete(SolutionEmbedding).where(SolutionEmbedding.solution_id == solution_id))
        db.execute(delete(ChallengeTechnology).where(ChallengeTechnology.challenge_id == challenge_id))
        db.execute(delete(Solution).where(Solution.id == solution_id))
        db.execute(delete(Challenge).where(Challenge.id == challenge_id))
        db.execute(delete(EmployeeProfile).where(EmployeeProfile.user_id == user_id))
        db.execute(delete(User).where(User.id == user_id))
        db.execute(delete(Technology).where(Technology.id == technology_id))
        db.execute(delete(Team).where(Team.id == team_id))
        db.execute(delete(Department).where(Department.id == department_id))
        db.commit()
