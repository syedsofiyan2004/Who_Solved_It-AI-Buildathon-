import json

import httpx

from app.core.config import Settings
from app.services.embeddings import NvidiaEmbeddingAdapter


def test_nvidia_embedding_adapter_uses_query_passage_modes_and_dimension():
    requests: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode())
        requests.append(payload)
        return httpx.Response(200, json={"data": [{"embedding": [0.1, 0.2, 0.3]}]})

    settings = Settings(
        DATABASE_URL="postgresql+psycopg://app_user:<password>@postgres:5432/knowledge_platform",
        JWT_SECRET="<test-only-jwt-secret>",
        AI_PROVIDER="nvidia",
        NVIDIA_API_KEY="fictional-test-key",
        NVIDIA_EMBEDDING_MODEL="nvidia/test-embed",
        NVIDIA_EMBEDDING_DIMENSIONS=3,
        RAG_ENABLED=True,
    )
    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = NvidiaEmbeddingAdapter(settings, client=client)

    assert adapter.embed("query text", input_type="query") == [0.1, 0.2, 0.3]
    assert adapter.embed("passage text", input_type="passage") == [0.1, 0.2, 0.3]
    assert requests[0]["input_type"] == "query"
    assert requests[1]["input_type"] == "passage"
    assert all(request["model"] == "nvidia/test-embed" for request in requests)
