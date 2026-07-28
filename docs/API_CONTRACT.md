# API Contract

Base path: `/api/v1`. JSON is UTF-8. All non-auth endpoints require `Authorization: Bearer <JWT>` unless specified. APIs return only permitted fields. Datetimes are ISO 8601 UTC strings; IDs are UUIDs. Application API routes are registered only under `/api/v1`; unprefixed application routes such as `/search` and `/auth/login` are not supported.

## 1. Shared response rules

Success: `{ "data": <resource>, "meta": { ...optional } }`.

Paginated success: `{ "data": [...], "meta": { "page": 1, "page_size": 20, "total": 53, "has_next": true } }`. Default page is 1; default/max page size is 20/100 unless search contract says otherwise.

All errors: `{ "error": { "code": "validation_error", "message": "Human-readable safe message.", "details": [{ "field": "query", "message": "Required." }], "request_id": "uuid" } }`.

Codes: 400 malformed request, 401 unauthenticated, 403 unauthorized, 404 authorized resource absent/not visible, 409 state conflict, 413 attachment too large, 415 unsupported file type, 422 validation, 429 rate limited, 500 internal, 502/503 upstream dependency unavailable. Never reveal authorization scope or stack traces in error text.

## 2. Resource shapes

- `User`: `id,email,role,is_active,profile` (profile includes approved display name/title/team/department/contact fields only when viewer is allowed).
- `EmployeeProfile`: `user_id,display_name,job_title,team,department,contact_email,contact_handle,skills,technologies,avatar_key,initials,bio,verified_solutions,contribution_count,helpful_contribution_count`; solution lists are filtered to records visible to the viewer.
- `ChallengeSummary`: `id,title,status,visibility,owner_user_id,updated_at`.
- `ChallengeDetail`: summary plus `solution_id`, problem description, symptoms, exact error, environment, `technology_ids`, complete `technologies`, solution body, attachment summaries, review history, verifier/last-verified metadata, related visible verified solutions, `can_edit`, and feedback aggregate.
- `SearchResult`: `challenge_id,solution_id,title,score,match_reasons,status,visibility,solver,technologies,technical excerpts`; `technologies` is always an array of complete strings, solver/contact fields come only from PostgreSQL, and `match_reasons` contains at most three deterministic signal explanations. Generated text is separate.

## 3. Endpoint catalogue

| Method/path | Purpose | Auth/roles | Request and validation | Response/status/authorization |
|---|---|---|---|---|
| `GET /health/live` | Liveness check under `/api/v1` | Public (no sensitive detail) | none | `200` service status; configured AI provider readiness does not expose credentials. |
| `GET /health/ready` | Readiness check under `/api/v1` | Public (no sensitive detail) | none | `200` service/database status or `503 database_unavailable`. |
| `POST /auth/login` | Password login | Public, rate-limited | `{email,password}`; valid email; password 8–128 chars | `200` token/current user, `401` generic invalid credentials, `429`. |
| `POST /auth/logout` | Revoke/session logout mechanism | Any authenticated | optional refresh/session identifier | `204`; always audit. |
| `GET /auth/me` | Current user/profile | Any authenticated | none | `200 User`, `401`. |
| `GET /profiles/me` | Own full editable profile | Any authenticated | none | `200`; owner only. |
| `PATCH /profiles/me` | Edit allowed self fields | Any authenticated | display name/title/skills/contact action, strict lengths | `200`, `422`; cannot alter role/org scope. |
| `GET /profiles/{user_id}` | Discover allowed employee profile | Any authenticated | UUID | `200 allowed User`, `404` if not visible, `403` never exposes prohibited contact. |
| `GET /technologies` | List/search tag vocabulary | Any authenticated | `q`, page controls | paginated `200`; active tags only. |
| `GET /challenges` | Browse authorized records | Any authenticated | status, technology, team, department, visibility filters; paging | `200`; server intersects filters with caller scope. |
| `POST /challenges` | Create draft challenge | Employee+ | title, problem, symptoms, error, env, visibility, metadata; no publish status | `201`; caller is owner, audit. |
| `GET /challenges/{id}` | Full authorized detail | Any authenticated | UUID | `200 ChallengeDetail`, `404` when not visible. |
| `PATCH /challenges/{id}` | Edit allowed lifecycle content | Owner/admin | partial validated fields + optimistic `updated_at` | `200`, `403`, `409`; draft/changes/submitted edits persist; verified technical edits return to review and clear stale embeddings. |
| `POST /challenges/{id}/submit` | Submit draft for review | Owner | no body or confirmation token | `200`; validates complete solution, moves to `submitted`. |
| `POST /challenges/{id}/archive` | Archive allowed record | Owner/admin by state policy | reason required | `200`; no hard delete. |
| `POST /challenges/{id}/attachments` | Upload evidence | Owner/reviewer/admin per access | multipart allowed MIME, <= configured max, sanitized filename | `201`, `413`, `415`, scan pending; object authorization. |
| `GET /challenges/{id}/attachments/{attachment_id}` | Download permitted attachment | Authorized viewer | UUIDs | `200` stream or `404`; re-check visibility and scan status. |
| `POST /reviews` | Review submission | Reviewer/admin, not owner | `{solution_id,decision,notes,visibility_after}`; decision enum; notes on reject/change request | `201`, `403`, `409`; append-only review/audit; response includes safe `embedding_status`. |
| `GET /reviews/queue` | Reviewer work queue | Reviewer/admin | status/page filters | `200` only assignments/eligible organization scope. |
| `POST /search` | Hybrid solution discovery | Any authenticated, rate-limited | `{query,filters:{technology_ids,department_id,team_id,verified_only,visibility},page,page_size,include_summary}`; 3–1000 chars; page size max 20 | `200` results/citations/no-answer or `503 bedrock_unavailable` for requested semantic/RAG functionality; server filters before generation. |
| `GET /search/{query_id}` | Retrieve own logged search summary | Searcher/admin audit scope | UUID | `200`; owner or administrator only. |
| `POST /feedback` | Record solution usefulness | Employee+ | `{solution_id,search_query_id?,value,comment?}`; comment max 1000 | `201`/`200` idempotent update; caller must see solution. |
| `GET /admin/users` | Administer users | Administrator | paging/filter | `200`; audit. |
| `PATCH /admin/users/{id}` | Set active/role/org assignment | Administrator | constrained role/status fields, reason | `200`, `409`; cannot self-demote without second admin policy. |
| `GET /admin/audit-logs` | Audit investigation | Administrator | date/action/actor/page filters | paginated `200`; sensitive metadata redacted. |

## 4. Phase 2 authentication implementation notes

`POST /auth/login` accepts a JSON body with a normalized work email and an 8-128 character password. It returns `{data:{access_token,token_type,expires_in,user},meta:{}}`. The browser keeps the access token only in memory during Phase 2; no refresh token, cookie session, or persistent browser token is introduced. Login failures remain generic and rate limiting returns `429` in the shared API error format.

`GET /auth/me` and `POST /auth/logout` require `Authorization: Bearer <JWT>`. Tokens validate algorithm, issuer, audience, expiry, not-before, subject UUID, and token-ID UUID. Logout records the token ID and expiry in PostgreSQL; a revoked, inactive, deleted, malformed, expired, or absent identity returns `401` through the shared error format. RBAC is supplied through server-side dependencies and remains the authorization boundary for later endpoints.

## 5. Phase 3 repository implementation notes

`POST /challenges` creates a structured draft and creates its paired solution in the same PostgreSQL transaction. `PATCH /challenges/{id}` requires an `expected_updated_at` value for optimistic concurrency. Owners can edit drafts, returned-for-changes records, submitted records, and verified records; administrators can edit permitted records. A verified record remains verified for metadata-only edits, but searchable technical-content changes move the challenge and solution back to `submitted` and delete stale embeddings so the change must be reviewed again. `POST /challenges/{id}/submit` moves editable records to `submitted`; `POST /challenges/{id}/archive` requires a reason and records an audit event. `GET /challenges` and detail responses apply the server-side visibility policy before serialization.

Profile endpoints return approved company contact email and optional internal contact handle from PostgreSQL. The reviewer queue and review endpoint enforce reviewer role, in-scope organization, submitted state, and a prohibition on reviewing one's own solution. Review decisions are append-only and update the current challenge/solution lifecycle state. When a submitted solution is verified, the API attempts to generate or refresh its configured AI provider embedding only if embeddings are configured; otherwise it records a safe disabled/unavailable status without fabricating vectors.

Attachment upload accepts only configured MIME types, a maximum configured size, PDF magic bytes or UTF-8 text content, and a sanitized filename. Accepted uploads return `pending_scan`; download returns no resource until a scanner marks the attachment `available`. The local attachment volume is not publicly served.

## 6. Search-specific response

`POST /search` returns `{data:{query_id,results,summary,summary_citations,summary_error,confidence,no_answer,service_status},meta:{page,page_size,total,has_next}}`. In Phase 8, `include_summary=true` embeds the authenticated query, merges already-authorized pgvector/FTS/exact-error candidates, and—only when the confidence gate passes—sends the first three permitted technical records to configured AI provider. `summary_citations` is an allow-listed array of immutable solution UUIDs; solver fields remain PostgreSQL serialization and no contact field is returned.

An embedding dependency failure returns `503 semantic_search_unavailable`; unsafe query content returns `422 unsafe_search_content`. A generation dependency or output-validation failure returns the source results with `summary:null`, empty citations, a safe `summary_error`, and `service_status.grounded_summary` of `unavailable` or `invalid_response`. No-answer results return `grounded_summary:not_run_no_answer` and do not invoke generation.

Current implementation note: grounded-summary context is selected from the globally highest-ranked authorized eligible solutions, capped by `RAG_MAX_CONTEXT_SOLUTIONS`, not only from the visible page. Solver profile and approved contact fields remain PostgreSQL serialization and are never generated by configured AI provider.

Candidates below the single `SEARCH_RESULT_THRESHOLD` are removed before `meta.total`, pagination, search logging, and grounding context. When none remain, the response is `no_answer=true`. Grounding always uses the highest-ranked authorized eligible results globally, capped by `RAG_MAX_CONTEXT_SOLUTIONS`, rather than the current page only. `technologies` is always a JSON array of complete strings rather than a PostgreSQL array literal. `match_reasons` contains no more than three deterministic signal explanations.

## 5. Authorization behaviour

Endpoints authenticate first, validate input second, load candidates with visibility policy third, then act. A record that exists but is not visible returns 404 in normal user routes to reduce enumeration. Reviewer authority is constrained to assigned/allowed organization scope; administrator action is audit logged. Client-side hiding is never authorization.
