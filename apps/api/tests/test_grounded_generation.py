import json
from uuid import uuid4

import httpx
import pytest

from app.core.config import Settings
from app.services.grounded_generation import (
    BedrockGroundedGenerationAdapter,
    GroundedGenerationInvalid,
    GroundingSource,
    NvidiaGroundedGenerationAdapter,
)

SETTINGS_VALUES = {
    "DATABASE_URL": "postgresql+psycopg://app_user:<password>@postgres:5432/knowledge_platform",
    "JWT_SECRET": "<test-only-jwt-secret>",
    "AWS_REGION": "us-east-1",
    "BEDROCK_EMBEDDING_MODEL_ID": "amazon.titan-embed-text-v2:0",
    "BEDROCK_EMBEDDING_DIMENSIONS": 3,
    "BEDROCK_EMBEDDINGS_ENABLED": True,
    "BEDROCK_CHAT_MODEL_ID": "anthropic.claude-3-haiku-20240307-v1:0",
    "RAG_ENABLED": True,
}


class FakeGenerationClient:
    def __init__(self, text: str):
        self.text = text
        self.calls = 0

    def converse(self, **kwargs):
        self.calls += 1
        return {"output": {"message": {"content": [{"text": self.text}]}}}


def test_grounded_generation_accepts_only_authorized_inline_citations():
    solution_id = uuid4()
    response = json.dumps(
        {
            "summary": f"Correct the package path and rebuild. [{solution_id}]",
            "citations": [str(solution_id)],
        }
    )
    client = FakeGenerationClient(response)
    adapter = BedrockGroundedGenerationAdapter(Settings(**SETTINGS_VALUES), client=client)

    answer = adapter.generate(
        query="Container cannot import its package",
        sources=[GroundingSource(solution_id=solution_id, technical_document="Title: Container import failure")],
    )

    assert answer.citations == [solution_id]
    assert client.calls == 1


def test_grounded_generation_accepts_uuid_citation_case_variance():
    solution_id = uuid4()
    response = json.dumps(
        {
            "summary": f"Correct the package path and rebuild. [{str(solution_id).upper()}]",
            "citations": [str(solution_id)],
        }
    )
    adapter = BedrockGroundedGenerationAdapter(Settings(**SETTINGS_VALUES), client=FakeGenerationClient(response))

    answer = adapter.generate(
        query="Container cannot import its package",
        sources=[GroundingSource(solution_id=solution_id, technical_document="Title: Container import failure")],
    )

    assert answer.citations == [solution_id]


@pytest.mark.parametrize(
    "payload",
    [
        {"summary": "Unsupported source [00000000-0000-0000-0000-000000000000]", "citations": ["00000000-0000-0000-0000-000000000000"]},
        {"summary": "Contact engineer@example.test [00000000-0000-0000-0000-000000000000]", "citations": ["00000000-0000-0000-0000-000000000000"]},
    ],
)
def test_grounded_generation_rejects_unsafe_or_ungrounded_output(payload):
    source_id = uuid4()
    adapter = BedrockGroundedGenerationAdapter(Settings(**SETTINGS_VALUES), client=FakeGenerationClient(json.dumps(payload)))

    with pytest.raises(GroundedGenerationInvalid):
        adapter.generate(query="safe query", sources=[GroundingSource(solution_id=source_id, technical_document="Title: Safe")])


def test_nvidia_generation_adapter_returns_only_valid_grounded_json():
    solution_id = uuid4()
    response_payload = {
        "summary": f"Use the verified package path. [{solution_id}]",
        "citations": [str(solution_id)],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        request_payload = json.loads(request.content.decode())
        assert request_payload["model"] == "openai/gpt-oss-120b"
        assert request_payload["max_tokens"] == 1024
        assert request_payload["temperature"] == 0
        assert request_payload["response_format"] == {"type": "json_object"}
        assert request_payload["stream"] is False
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(response_payload)}}]})

    settings = Settings(
        DATABASE_URL="postgresql+psycopg://app_user:<password>@postgres:5432/knowledge_platform",
        JWT_SECRET="<test-only-jwt-secret>",
        AI_PROVIDER="nvidia",
        NVIDIA_API_KEY="fictional-test-key",
        NVIDIA_CHAT_MODEL="openai/gpt-oss-120b",
        NVIDIA_GENERATION_MAX_TOKENS=1024,
        RAG_ENABLED=True,
    )
    adapter = NvidiaGroundedGenerationAdapter(settings, client=httpx.Client(transport=httpx.MockTransport(handler)))
    answer = adapter.generate(
        query="Container package error",
        sources=[GroundingSource(solution_id=solution_id, technical_document="Title: Package path")],
    )

    assert answer.summary.startswith("Use the verified package path")
    assert answer.citations == [solution_id]


def test_nvidia_generation_retries_once_after_invalid_grounded_json():
    solution_id = uuid4()
    responses = [
        {"summary": "Use the verified package path.", "citations": [str(solution_id)]},
        {"summary": f"Use the verified package path. [{solution_id}]", "citations": [str(solution_id)]},
    ]
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        request_payload = json.loads(request.content.decode())
        if calls == 2:
            assert "previous response was rejected" in request_payload["messages"][1]["content"].lower()
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(responses[calls - 1])}}]})

    settings = Settings(
        DATABASE_URL="postgresql+psycopg://app_user:<password>@postgres:5432/knowledge_platform",
        JWT_SECRET="<test-only-jwt-secret>",
        AI_PROVIDER="nvidia",
        NVIDIA_API_KEY="fictional-test-key",
        NVIDIA_CHAT_MODEL="openai/gpt-oss-120b",
        NVIDIA_GENERATION_MAX_TOKENS=1024,
        RAG_ENABLED=True,
    )
    adapter = NvidiaGroundedGenerationAdapter(settings, client=httpx.Client(transport=httpx.MockTransport(handler)))

    answer = adapter.generate(
        query="Container package error",
        sources=[GroundingSource(solution_id=solution_id, technical_document="Title: Package path")],
    )

    assert calls == 2
    assert answer.citations == [solution_id]


def test_nvidia_generation_repairs_missing_inline_citation_markers_when_model_returns_valid_citations():
    solution_id = uuid4()
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({
            "summary": "Use the verified package path.",
            "citations": [str(solution_id)],
        })}}]})

    settings = Settings(
        DATABASE_URL="postgresql+psycopg://app_user:<password>@postgres:5432/knowledge_platform",
        JWT_SECRET="<test-only-jwt-secret>",
        AI_PROVIDER="nvidia",
        NVIDIA_API_KEY="fictional-test-key",
        NVIDIA_CHAT_MODEL="openai/gpt-oss-120b",
        NVIDIA_GENERATION_MAX_TOKENS=1024,
        RAG_ENABLED=True,
    )
    adapter = NvidiaGroundedGenerationAdapter(settings, client=httpx.Client(transport=httpx.MockTransport(handler)))

    answer = adapter.generate(
        query="Container package error",
        sources=[GroundingSource(
            solution_id=solution_id,
            technical_document=(
                "Title: Container cannot import the application package\n"
                "Root cause: The image copied source outside Python's runtime module path.\n"
                "Resolution: Correct COPY and WORKDIR paths. | Rebuild without cache."
            ),
        )],
    )

    assert calls == 2
    assert answer.citations == [solution_id]
    assert f"[{solution_id}]" in answer.summary
    assert answer.summary.startswith("Use the verified package path.")


def test_nvidia_generation_repairs_multiple_valid_citations_without_fallback():
    first_solution_id = uuid4()
    second_solution_id = uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({
            "summary": "Summary without inline citations.",
            "citations": [str(first_solution_id), str(second_solution_id)],
        })}}]})

    settings = Settings(
        DATABASE_URL="postgresql+psycopg://app_user:<password>@postgres:5432/knowledge_platform",
        JWT_SECRET="<test-only-jwt-secret>",
        AI_PROVIDER="nvidia",
        NVIDIA_API_KEY="fictional-test-key",
        NVIDIA_CHAT_MODEL="openai/gpt-oss-120b",
        NVIDIA_GENERATION_MAX_TOKENS=1024,
        RAG_ENABLED=True,
    )
    adapter = NvidiaGroundedGenerationAdapter(settings, client=httpx.Client(transport=httpx.MockTransport(handler)))

    answer = adapter.generate(
        query="Terraform state lock",
        sources=[
            GroundingSource(
                solution_id=first_solution_id,
                technical_document="Title: Terraform lock\nRoot cause: A stale lock remained.\nResolution: Confirm no active apply is running. | Release the stale lock.",
            ),
            GroundingSource(
                solution_id=second_solution_id,
                technical_document="Title: Terraform lock staging\nRoot cause: The previous worker stopped before lock cleanup.\nResolution: Re-run the plan after unlocking.",
            ),
        ],
    )

    assert answer.citations == [first_solution_id, second_solution_id]
    assert f"[{first_solution_id}]" in answer.summary
    assert f"[{second_solution_id}]" in answer.summary


def test_nvidia_generation_falls_back_when_model_returns_no_usable_citations():
    solution_id = uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({
            "summary": "Summary without usable citations.",
            "citations": [],
        })}}]})

    settings = Settings(
        DATABASE_URL="postgresql+psycopg://app_user:<password>@postgres:5432/knowledge_platform",
        JWT_SECRET="<test-only-jwt-secret>",
        AI_PROVIDER="nvidia",
        NVIDIA_API_KEY="fictional-test-key",
        NVIDIA_CHAT_MODEL="openai/gpt-oss-120b",
        NVIDIA_GENERATION_MAX_TOKENS=1024,
        RAG_ENABLED=True,
    )
    adapter = NvidiaGroundedGenerationAdapter(settings, client=httpx.Client(transport=httpx.MockTransport(handler)))

    answer = adapter.generate(
        query="Container package error",
        sources=[GroundingSource(
            solution_id=solution_id,
            technical_document=(
                "Title: Container cannot import the application package\n"
                "Root cause: The image copied source outside Python's runtime module path.\n"
                "Resolution: Correct COPY and WORKDIR paths. | Rebuild without cache."
            ),
        )],
    )

    assert answer.citations == [solution_id]
    assert "verified fixes point to this root cause" in answer.summary
