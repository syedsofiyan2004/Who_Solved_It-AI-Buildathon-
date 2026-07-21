import json
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.services.grounded_generation import (
    BedrockGroundedGenerationAdapter,
    GroundedGenerationInvalid,
    GroundingSource,
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
