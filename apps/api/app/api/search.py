from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.rate_limit import search_rate_limiter
from app.core.security import get_current_user
from app.database.session import get_db
from app.models.auth import User
from app.models.repository import SearchQuery
from app.schemas.repository import SearchLogResponse, SearchRequest
from app.services.audit import audit_event
from app.services.embeddings import (
    BedrockEmbeddingAdapter,
    EmbeddingContentRejected,
    EmbeddingUnavailable,
    NvidiaEmbeddingAdapter,
)
from app.services.grounded_generation import (
    BedrockGroundedGenerationAdapter,
    GroundedGenerationInvalid,
    GroundedGenerationUnavailable,
    NvidiaGroundedGenerationAdapter,
    build_grounding_sources,
)
from app.services.search import (
    can_read_search_log,
    create_search_log,
    execute_hybrid_search,
    execute_keyword_search,
)

router = APIRouter(tags=["hybrid search"])


def _embedding_adapter(settings: Settings):
    if settings.effective_ai_provider == "nvidia":
        return NvidiaEmbeddingAdapter(settings)
    if settings.effective_ai_provider == "bedrock":
        return BedrockEmbeddingAdapter(settings)
    raise EmbeddingUnavailable("Semantic search is disabled until an embedding provider is configured.")


def _generation_adapter(settings: Settings):
    if settings.effective_ai_provider == "nvidia":
        return NvidiaGroundedGenerationAdapter(settings)
    if settings.effective_ai_provider == "bedrock":
        return BedrockGroundedGenerationAdapter(settings)
    raise GroundedGenerationUnavailable("Grounded summaries are disabled until an AI provider is configured.")


@router.post("/search", response_model=dict)
def search_solutions(
    payload: SearchRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    search_rate_limiter.check(f"search:{current_user.id}", limit=settings.rate_limit_search_per_minute)
    semantic_status = "available"
    try:
        results, total, latency_ms, confidence, no_answer, ranked_solution_ids = execute_hybrid_search(
            db,
            user=current_user,
            payload=payload,
            adapter=_embedding_adapter(settings),
            threshold=settings.search_result_threshold,
        )
    except EmbeddingContentRejected as exc:
        raise HTTPException(status_code=422, detail={"code": "unsafe_search_content", "message": str(exc)}) from exc
    except EmbeddingUnavailable:
        # A missing/free-trial AI key must not make the local product unusable.
        # Keyword and exact-error retrieval remain fully authorized and operational.
        results, total, latency_ms = execute_keyword_search(db, user=current_user, payload=payload)
        confidence = results[0].score if results else None
        no_answer = not results
        ranked_solution_ids = [item.solution_id for item in results]
        semantic_status = "not_available"

    summary = None
    citations: list[str] = []
    generation_used = False
    generation_status = "not_requested"
    generation_error = None
    if payload.include_summary and not no_answer and semantic_status == "available":
        try:
            sources = build_grounding_sources(
                db,
                solution_ids=ranked_solution_ids[: settings.rag_max_context_solutions],
            )
            answer = _generation_adapter(settings).generate(query=payload.query, sources=sources)
            summary = answer.summary or None
            citations = [str(citation) for citation in answer.citations]
            generation_used = bool(summary)
            generation_status = "available" if summary else "not_generated"
        except GroundedGenerationUnavailable:
            generation_status = "unavailable"
            generation_error = "Grounded summary is temporarily unavailable."
        except GroundedGenerationInvalid:
            generation_status = "invalid_response"
            generation_error = "Grounded summary could not be safely returned."
    elif payload.include_summary:
        generation_status = "not_run_no_answer" if no_answer else "unavailable"
        if semantic_status != "available" and not no_answer:
            generation_error = "Configure an AI provider to generate a grounded summary."

    outcome = "grounded_summary_generated" if generation_used else ("no_answer" if no_answer else "hybrid_results")
    log = create_search_log(
        db,
        user_id=current_user.id,
        payload=payload,
        results=results,
        total=total,
        latency_ms=latency_ms,
        confidence=confidence,
        no_answer=no_answer,
        bedrock_generation_used=generation_used,
        outcome=outcome,
    )
    audit_event(
        db,
        request,
        action="grounded_search_executed" if payload.include_summary else "hybrid_search_executed",
        outcome=log.outcome,
        actor_user_id=current_user.id,
        entity_type="search_query",
        entity_id=log.id,
        metadata={
            "query_length": len(payload.query),
            "result_count": total,
            "filters_applied": bool(payload.filters.model_dump(exclude_defaults=True)),
            "grounded_summary_requested": payload.include_summary,
            "grounded_summary_used": generation_used,
        },
    )
    db.commit()
    db.refresh(log)
    return {
        "data": {
            "query_id": str(log.id),
            "results": [item.model_dump(mode="json") for item in results],
            "summary": summary,
            "summary_citations": citations,
            "summary_error": generation_error,
            "confidence": confidence,
            "no_answer": no_answer,
            "service_status": {
                "keyword_search": "available",
                "semantic_search": semantic_status,
                "grounded_summary": generation_status,
            },
        },
        "meta": {"page": payload.page, "page_size": payload.page_size, "total": total, "has_next": payload.page * payload.page_size < total},
    }


@router.get("/search/{query_id}", response_model=dict)
def get_search_log(query_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    log = db.get(SearchQuery, query_id)
    if log is None or not can_read_search_log(current_user, log):
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "This resource is not available."})
    return {"data": SearchLogResponse(
        id=log.id,
        query=log.query_text,
        result_count=log.result_count,
        outcome=log.outcome,
        latency_ms=log.latency_ms,
        created_at=log.created_at,
    ).model_dump(mode="json"), "meta": {}}
