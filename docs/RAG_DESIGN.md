# RAG and Retrieval Design

## Objective

Return the most relevant authorized historical solutions and the structured profile of the engineer who solved them. AI improves retrieval and summarization; it never invents the solver.

## Retrieval pipeline

1. Authenticate the user.
2. Normalize query and metadata filters.
3. Run PostgreSQL weighted full-text search.
4. Extract and match deterministic technical error fragments.
5. When an embedding provider is configured, embed the query in `query` mode and run pgvector cosine search against embeddings created in `passage` mode.
6. Merge candidates by immutable solution ID.
7. Apply object authorization.
8. Score and threshold each candidate.
9. Sort and paginate eligible results.
10. Load structured solver data from PostgreSQL.
11. Optionally generate a grounded summary from the globally highest-ranked authorized technical records.

## Embedding document

The canonical document includes:

- title
- technology names
- environment
- problem description
- symptoms
- exact error
- root cause
- resolution steps
- code evidence
- prevention notes

It excludes employee identity, contact information, organization metadata, ownership, review status, roles, permissions, credentials, and detected secrets.

The content hash combines the canonical document with the embedding model ID. Unchanged records do not invoke the embedding provider again. A materially edited verified solution returns to review and stale embeddings are removed.

## Default local models

```text
Embedding: nvidia/nemotron-3-embed-1b
Chat: openai/gpt-oss-120b
```

The embedding adapter uses `passage` for stored solution records and `query` for user searches. The current model output is validated against the configured dimension.

## Ranking

Available normalized signals are combined deterministically:

- semantic similarity: 0.40
- PostgreSQL full-text rank: 0.25
- exact-error evidence: 0.20
- selected technology match: 0.05
- verified status: 0.05
- recency: 0.02

Unavailable signals are reweighted over the signals that are present. Full-text rank does not include an exact-error bonus; exact error contributes only once. Scores are bounded to `[0,1]` and deterministic tie-breaking uses score, update time, and stable IDs.

`SEARCH_RESULT_THRESHOLD` is the single eligibility/no-answer threshold. Candidates below it are removed before totals, pagination, audit counts, and summary context selection.

## Match reasons

Reasons are derived from retrieval evidence, not generated prose. Examples:

- Exact error match
- Keyword match
- Same technology
- Similar technical context
- Verified solution

A semantic explanation is emitted only above the documented semantic confidence floor.

## Grounded summary

When `include_summary=true`, the backend reconstructs at most `RAG_MAX_CONTEXT_SOLUTIONS` globally ranked authorized technical records. The chat model must return JSON with:

```json
{"summary":"A cited summary","citations":["solution UUID"]}
```

Every claim requires an inline source UUID. The backend rejects malformed JSON, unknown/duplicate citations, uncited summaries, contact information, and detected secrets. No-answer searches do not invoke generation. Provider failure returns the source results with a safe unavailable status and never fabricates prose.

## Modes

- AI disabled or unavailable: keyword and exact-error retrieval remains active.
- Embeddings configured: hybrid retrieval is active.
- Chat configured and requested: grounded summary is added after retrieval.

A separate reranker is optional and not required for the final review build.
