import pytest
from pydantic import ValidationError

from app.core.config import Settings

BASE_VALUES = {
    "DATABASE_URL": "postgresql+psycopg://app_user:<password>@postgres:5432/knowledge_platform",
    "JWT_SECRET": "<test-only-jwt-secret>",
}


def test_development_can_start_before_bedrock_is_configured():
    settings = Settings(**BASE_VALUES, APP_ENV="development", RAG_ENABLED=False)

    assert settings.rag_enabled is False
    assert settings.bedrock_status == "disabled_until_configured"


def test_rag_enabled_requires_bedrock_model_configuration():
    with pytest.raises(ValidationError):
        Settings(
            **BASE_VALUES,
            RAG_ENABLED=True,
            AWS_REGION="",
            BEDROCK_EMBEDDING_MODEL_ID="",
            BEDROCK_CHAT_MODEL_ID="",
        )

    settings = Settings(
        **BASE_VALUES,
        RAG_ENABLED=True,
        AWS_REGION="us-east-1",
        BEDROCK_EMBEDDING_MODEL_ID="amazon.titan-embed-text-v2:0",
        BEDROCK_CHAT_MODEL_ID="anthropic.claude-3-haiku-20240307-v1:0",
    )
    assert settings.bedrock_status == "configured"


def test_embeddings_enabled_requires_its_own_model_configuration():
    with pytest.raises(ValidationError):
        Settings(
            **BASE_VALUES,
            BEDROCK_EMBEDDINGS_ENABLED=True,
            AWS_REGION="",
            BEDROCK_EMBEDDING_MODEL_ID="",
            BEDROCK_EMBEDDING_DIMENSIONS=None,
        )

    settings = Settings(**BASE_VALUES, BEDROCK_EMBEDDINGS_ENABLED=True, AWS_REGION="us-east-1", BEDROCK_EMBEDDING_MODEL_ID="amazon.titan-embed-text-v2:0", BEDROCK_EMBEDDING_DIMENSIONS=3)
    assert settings.embedding_status == "configured"


def test_production_rejects_placeholder_jwt_secret():
    with pytest.raises(ValidationError):
        Settings(
            **{**BASE_VALUES, "JWT_SECRET": "replace-with-a-long-random-secret-before-starting-the-api"},
            APP_ENV="production",
            RAG_ENABLED=False,
        )


def test_one_search_threshold_is_configured_for_eligibility_and_no_answer():
    settings = Settings(**BASE_VALUES, SEARCH_RESULT_THRESHOLD=0.52)

    assert settings.search_result_threshold == 0.52


def test_nvidia_provider_requires_key_only_when_rag_is_enabled():
    keyword_only = Settings(**BASE_VALUES, AI_PROVIDER="nvidia", RAG_ENABLED=False)
    assert keyword_only.rag_enabled is False

    with pytest.raises(ValidationError):
        Settings(**BASE_VALUES, AI_PROVIDER="nvidia", NVIDIA_API_KEY="", RAG_ENABLED=True)

    configured = Settings(
        **BASE_VALUES,
        AI_PROVIDER="nvidia",
        NVIDIA_API_KEY="fictional-test-key",
        RAG_ENABLED=True,
    )
    assert configured.embedding_status == "configured"
    assert configured.chat_model_id == "moonshotai/kimi-k2.6"
