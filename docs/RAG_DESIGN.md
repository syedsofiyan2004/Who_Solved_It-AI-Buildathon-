# RAG and Retrieval Design

## 1. Non-negotiable retrieval sequence

1. Authenticate the employee.
2. Accept and validate the search query.
3. Extract optional metadata filters.
4. Create the query embedding through Amazon Bedrock.
5. Run pgvector similarity search.
6. Run PostgreSQL full-text search.
7. Match normalized exact error-message fragments.
8. Apply visibility and authorization filters.
9. Merge candidate results.
10. Rerank candidates.
11. Apply a confidence threshold.
12. Retrieve structured employee information from PostgreSQL.
13. Send only permitted retrieved solution context to Bedrock.
14. Generate a grounded summary.
15. Return citations to original solution records.

Phases 7 and 8 implement the full sequence. Phase 8 runs only after Phase 7 has returned authorized, confidence-passing results. It never creates a synthetic vector or generated prose. `semantic_search` is `available` only after the embedding call succeeds; `grounded_summary` is `available` only after a validated generation response is returned.

## 2. Embedding document contract

One current embedding document is created per verified/retrievable solution. It contains title, technical problem description, symptoms, sanitized exact error message, environment, technology names, root cause, resolution steps, prevention notes, and non-sensitive code snippet text. It excludes employee names, email addresses, job titles, teams/departments, contact details, role, raw permissions, reviewer names, and any secret detected in user content.

The `content_hash` is SHA-256 of the canonical permitted technical document plus embedding model ID. A changed hash triggers re-embedding; unchanged records do not invoke Bedrock. A dimension/model change requires an ADR and controlled re-embedding migration.

## 3. Candidate retrieval

- Vector: cosine similarity through pgvector, up to 100 candidates for the configured embedding model.
- Full text and exact error: PostgreSQL weighted `tsvector`, normalized exact-error comparison, and trigram support, up to 20 candidates.
- Metadata: technology, verified-only, department, team, and visibility are narrowing filters, never client-authorized overrides.
- Authorization: `can_view_challenge` is applied before a candidate enters the merge set.

A verified FTS/exact-error candidate remains eligible if it is awaiting its embedding. This preserves useful search after review or content updates without pretending it has a semantic score.

## 4. Merge, rerank, and threshold

The approved initial score is:

`score = 0.40*semantic + 0.25*fts + 0.20*exact_error + 0.05*technology + 0.05*verification + 0.03*helpful_feedback + 0.02*recency`

Each input is normalized to `[0,1]`. Unavailable signals are reweighted over available signals. Phase 7 does not yet collect helpful-feedback signals, so the active score uses semantic (0.40), FTS (0.25), exact error (0.20), optional technology (0.05), verification (0.05), and recency (0.02). The initial candidate limits are 100 vector and 20 FTS/exact candidates. `SEARCH_RESULT_THRESHOLD` defaults to `0.45` and is the sole eligibility and no-answer threshold: every candidate below it is excluded before sorting, totals, pagination, audit result counts, and Bedrock context selection; when no eligible candidate remains, the response is `no_answer=true`.

Results sort by score, solved date descending, then UUID for a stable final tie break. The Phase 7 confidence gate uses the top eligible reranked score. Below threshold, return `no_answer=true` with the approved no-answer UI copy; never select or suggest a probable expert. Match explanations are deterministic and limited to three: exact error text, keyword/FTS evidence, selected technology, and semantic context in that priority order. `Similar technical context` appears only for a semantic score of at least `0.60`; lower semantic scores may contribute to rank but do not receive that explanation. Grounded summaries use the globally highest-ranked authorized eligible solutions, capped at `RAG_MAX_CONTEXT_SOLUTIONS`, even when the request displays a later pagination page. Score separation and weight changes require evaluation evidence and, where architectural, an ADR.

## 5. Grounded generation

Phase 8 sends only the first three authorized, confidence-passing technical records to Bedrock. The record body is reconstructed from the same permitted technical document contract used for embeddings; it excludes employees, contact data, ownership, verification, roles, permissions, and organization metadata. The system prompt requires JSON only, an inline immutable `solution_id` citation for every claim, and an allow-listed citations array.

The adapter rejects malformed JSON, citations outside the supplied source set, duplicate citations, uncited non-empty summaries, citations not present inline with claims, detected email/contact data, and detected secrets. It returns source records with `summary=null` and a safe summary-status/error when Bedrock is unavailable or invalid; it never replaces that state with fabricated prose. A no-answer result never invokes the generation model.

## 6. Security and failure handling

Bedrock IAM permits only selected model invocation actions in the selected region. Timeouts and response failures produce a dependency-unavailable response without synthetic vectors. Query text is secret-scanned before Bedrock invocation. Retrieval logs must not store prohibited contact data, and no denied content may reach a Bedrock request.

## 7. Evaluation and observability

The deterministic fictional seed is the Phase 7 evaluation corpus: 36 solution records, with repeated scenario variants, plus no-answer and permission cases in `tests/fixtures/rag_evaluation.jsonl`. Each row has `query`, `expected_solution_id`, `expected_solver_id`, `expected_technology_ids`, `expected_top_five_ids`, `expected_no_answer`, `caller_scope`, expected permission behavior, and expected citation behavior. Measure Recall@5, MRR, solver accuracy, permission-filter accuracy, no-answer accuracy, citation validity, and latency by channel before changing scoring or threshold values.
