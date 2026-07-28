import json
import os
import re
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Protocol
from uuid import UUID

import boto3
import httpx
from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.repository import (
    Challenge,
    ChallengeTechnology,
    ContentStatus,
    Solution,
    SolutionEmbedding,
    Technology,
)


class EmbeddingUnavailable(RuntimeError):
    pass


class EmbeddingContentRejected(ValueError):
    pass


SECRET_PATTERNS = (
    re.compile(r"(?:AKIA|ASIA)[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)\b(?:password|secret|api[_-]?key|access[_-]?token)\s*[:=]\s*\S+"),
)


def _assert_safe_embedding_content(value: str) -> None:
    if any(pattern.search(value) for pattern in SECRET_PATTERNS):
        raise EmbeddingContentRejected("Embedding content contains a detected secret and was not sent to the configured AI provider.")


def build_embedding_document(db: Session, solution: Solution) -> str:
    challenge = db.scalar(select(Challenge).where(Challenge.id == solution.challenge_id, Challenge.deleted_at.is_(None)))
    if challenge is None:
        raise ValueError("The solution does not have an active challenge.")
    technologies = list(
        db.scalars(
            select(Technology.name)
            .join(ChallengeTechnology, ChallengeTechnology.technology_id == Technology.id)
            .where(ChallengeTechnology.challenge_id == challenge.id, Technology.deleted_at.is_(None))
            .order_by(Technology.name)
        )
    )
    document = "\n".join(
        [
            f"Title: {challenge.title}",
            f"Technologies: {', '.join(technologies)}",
            f"Environment: {challenge.environment or ''}",
            f"Problem: {challenge.problem_description}",
            f"Symptoms: {challenge.symptoms}",
            f"Exact error: {challenge.exact_error_message or ''}",
            f"Root cause: {solution.root_cause}",
            f"Resolution: {' | '.join(solution.resolution_steps)}",
            f"Code evidence: {' | '.join(solution.code_snippets)}",
            f"Prevention: {solution.prevention_notes or ''}",
        ]
    )
    _assert_safe_embedding_content(document)
    return document


def content_hash(document: str, model_id: str) -> str:
    return sha256(f"{model_id}\n{document}".encode()).hexdigest()


class EmbeddingAdapter(Protocol):
    settings: Settings
    model_id: str

    def embed(self, document: str, *, input_type: str = "passage") -> list[float]: ...


@dataclass
class BedrockEmbeddingAdapter:
    settings: Settings
    client: Any | None = None

    def __post_init__(self) -> None:
        if self.settings.ai_provider not in {"bedrock", "disabled"} and not self.settings.bedrock_embeddings_enabled:
            raise EmbeddingUnavailable("Bedrock embeddings are not the configured provider.")
        if not self.settings.bedrock_embeddings_enabled:
            raise EmbeddingUnavailable("Bedrock embeddings are disabled until configuration is approved.")
        if self.client is None:
            if not os.environ.get("AWS_PROFILE", "").strip():
                os.environ.pop("AWS_PROFILE", None)
            self.client = boto3.client("bedrock-runtime", region_name=self.settings.aws_region)

    @property
    def model_id(self) -> str:
        return self.settings.bedrock_embedding_model_id

    def _provider(self) -> str:
        if self.settings.bedrock_embedding_provider != "auto":
            return self.settings.bedrock_embedding_provider
        model = self.model_id.lower()
        if model.startswith("amazon.titan"):
            return "amazon_titan"
        if model.startswith("cohere."):
            return "cohere"
        raise EmbeddingUnavailable("The configured Bedrock embedding model needs an explicit supported provider.")

    def embed(self, document: str, *, input_type: str = "passage") -> list[float]:
        _assert_safe_embedding_content(document)
        provider = self._provider()
        cohere_type = "search_query" if input_type == "query" else "search_document"
        body = (
            {"inputText": document, "dimensions": self.settings.bedrock_embedding_dimensions, "normalize": True}
            if provider == "amazon_titan"
            else {"texts": [document], "input_type": cohere_type}
        )
        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            payload = json.loads(response["body"].read())
        except (BotoCoreError, ClientError, KeyError, json.JSONDecodeError) as exc:
            raise EmbeddingUnavailable("Bedrock embedding invocation failed.") from exc
        values = payload.get("embedding") if provider == "amazon_titan" else (payload.get("embeddings") or [None])[0]
        if not isinstance(values, list) or not values or not all(isinstance(value, (int, float)) for value in values):
            raise EmbeddingUnavailable("Bedrock returned an invalid embedding response.")
        vector = [float(value) for value in values]
        expected = self.settings.bedrock_embedding_dimensions
        if expected is not None and len(vector) != expected:
            raise EmbeddingUnavailable("Bedrock returned an embedding with an unexpected dimension.")
        return vector


@dataclass
class NvidiaEmbeddingAdapter:
    settings: Settings
    client: httpx.Client | None = None

    def __post_init__(self) -> None:
        if self.settings.ai_provider != "nvidia" or not self.settings.nvidia_api_key:
            raise EmbeddingUnavailable("NVIDIA embeddings are disabled until NVIDIA_API_KEY is configured.")
        if self.client is None:
            self.client = httpx.Client(timeout=self.settings.nvidia_timeout_seconds)

    @property
    def model_id(self) -> str:
        return self.settings.nvidia_embedding_model

    def embed(self, document: str, *, input_type: str = "passage") -> list[float]:
        _assert_safe_embedding_content(document)
        payload = {
            "input": [document],
            "model": self.model_id,
            "input_type": "query" if input_type == "query" else "passage",
            "encoding_format": "float",
            "truncate": "END",
        }
        try:
            response = self.client.post(
                self.settings.nvidia_embedding_url,
                headers={
                    "Authorization": f"Bearer {self.settings.nvidia_api_key}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            body = response.json()
            values = body["data"][0]["embedding"]
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise EmbeddingUnavailable("NVIDIA embedding invocation failed.") from exc
        if not isinstance(values, list) or not values or not all(isinstance(value, (int, float)) for value in values):
            raise EmbeddingUnavailable("NVIDIA returned an invalid embedding response.")
        vector = [float(value) for value in values]
        expected = self.settings.nvidia_embedding_dimensions
        if expected is not None and len(vector) != expected:
            raise EmbeddingUnavailable("NVIDIA returned an embedding with an unexpected dimension.")
        return vector


def create_embedding_adapter(settings: Settings) -> EmbeddingAdapter:
    if settings.effective_ai_provider == "nvidia":
        return NvidiaEmbeddingAdapter(settings)
    if settings.effective_ai_provider == "bedrock":
        return BedrockEmbeddingAdapter(settings)
    raise EmbeddingUnavailable("Semantic search is disabled until an embedding provider is configured.")


def embed_verified_solution(db: Session, *, solution_id: UUID, adapter: EmbeddingAdapter) -> tuple[SolutionEmbedding, bool]:
    solution = db.scalar(select(Solution).where(Solution.id == solution_id, Solution.deleted_at.is_(None)))
    if solution is None or solution.status != ContentStatus.VERIFIED:
        raise ValueError("Only active verified solutions can be embedded.")
    document = build_embedding_document(db, solution)
    digest = content_hash(document, adapter.model_id)
    existing = db.scalar(
        select(SolutionEmbedding).where(
            SolutionEmbedding.solution_id == solution.id,
            SolutionEmbedding.embedding_model == adapter.model_id,
            SolutionEmbedding.content_hash == digest,
        )
    )
    if existing is not None:
        return existing, False
    vector = adapter.embed(document, input_type="passage")
    db.execute(
        delete(SolutionEmbedding).where(
            SolutionEmbedding.solution_id == solution.id,
            SolutionEmbedding.embedding_model == adapter.model_id,
        )
    )
    embedding = SolutionEmbedding(
        solution_id=solution.id,
        searchable_text=document,
        embedding=vector,
        embedding_model=adapter.model_id,
        content_hash=digest,
    )
    db.add(embedding)
    db.flush()
    return embedding, True


def reembed_verified_solutions(db: Session, *, adapter: EmbeddingAdapter) -> tuple[int, int, int]:
    created = skipped = failed = 0
    solution_ids = list(db.scalars(select(Solution.id).where(Solution.status == ContentStatus.VERIFIED, Solution.deleted_at.is_(None))))
    for solution_id in solution_ids:
        try:
            _, did_create = embed_verified_solution(db, solution_id=solution_id, adapter=adapter)
            created += int(did_create)
            skipped += int(not did_create)
        except (EmbeddingContentRejected, EmbeddingUnavailable, ValueError):
            failed += 1
    return created, skipped, failed
