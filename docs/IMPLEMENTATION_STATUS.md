# Implementation Status

## Current phase

**Phase 9 - Interactive UI: In progress.** Phases 0 through 8 are complete. Phase 9 now exposes grounded summaries/citations in search, recent verified records on the dashboard, and authorized solution reading. The approved Priority 0 security cleanup and Priority 1 search-correctness remediation are in progress. Authoring, reviewer, and profile workflow interactions remain outside this approved remediation slice and must be completed before this phase can be marked complete.

There are 11 planned phases in total: Phase 0 through Phase 10.

## Status legend

`Not started`, `In progress`, `Blocked`, `Implemented`, `Tested`, and `Complete` are used exactly as defined in the approved plan. A phase is `Complete` only after all of its acceptance criteria pass.

| Area | Status | Tests | UI states | Documentation | Blocker |
|---|---|---:|---:|---:|---|
| Phase 0 requirements/design lock | Complete | Documentation validation only | Specified | Yes | No |
| Phase 1 project foundation | Complete | Passing | Foundation shell only | Yes | No |
| Phase 2 authentication | Complete pending review | Passing | Login, validation, protected-route and sign-out states | Yes | Long-term SSO/password policy remains a pre-real-user decision |
| Phase 3 knowledge repository | Complete pending review | Passing | API lifecycle and safe attachment states | Yes | Attachment scanner and retention policy required before real employee use |
| Phase 4 UI foundation | Complete | Passing | Responsive shell, command, loading/empty/error/denied foundations | Yes | Brand identity and final visual-reference approval remain open |
| Phase 5 keyword search | Complete | Passing | Search, filters, loading/error/no-answer, pagination and preview | Yes | No |
| Phase 6 Bedrock embeddings | Complete | Passing; live Bedrock invocation verified | Dependency-unavailable CLI state | Yes | No |
| Phase 7 hybrid retrieval | Complete | Passing; live Bedrock query verified | Search result, no-answer, and dependency states | Yes | No |
| Phase 8 grounded RAG answers | Complete | Passing; live grounded generation verified | API summary, no-answer, unavailable, and invalid-response states | Yes | No |
| Phase 9 interactive UI | In progress | Search/dashboard/detail UI checks passing | Summary and detail states implemented | Yes | Authoring, reviewer, and profile workflows remain |
| Phase 10 test and AWS deployment | Not started | No | Specified | Yes | EC2, EBS, IAM, DNS/TLS decision required |

## Blockers and required inputs

| Item | Classification | Effect and current treatment |
|---|---|---|
| GitHub remote and CI ownership | Required before hosted CI use and collaboration workflow | The local repository was initialized with an initial commit. No remote was requested or configured; `.github/workflows/ci.yml` will run after the user adds a remote and enables Actions. |
| Product/brand name and primary accent colour | Required before real employee use | Generic working name and semantic colour tokens remain in use; no brand styling selected. |
| AWS account, approved Region, Bedrock embedding/generation model IDs, IAM policy | Required before AWS deployment | Development uses configured Amazon Titan Text Embeddings V2 embeddings and the selected available Claude 3 Haiku generation model in the configured Region. Both adapters completed real fictional-data calls. Production model-cost approval and least-privilege IAM review remain required before deployment. |
| 10-20 fictional employee records and 30-50 solutions | Satisfied for development | `scripts/seed_dev.py` idempotently inserts 24 fictional `example.test` employees, 12 technologies, and 36 fictional challenge/solution records (30 verified, 3 submitted, 3 draft). No real employee data is used. |
| Approved contact fields and data-retention policy | Required before real employee use | Contract exposes approved work email and internal contact action only, pending policy confirmation. |
| Visibility-to-organization mapping and reviewer assignment policy | Required before real employee use | Authorization rules are documented with conservative defaults. |
| Final Figma/reference-board approval | Required before real employee use | `UI_SPEC.md` is the implementation-ready textual source; visual approval remains required. |
| SMTP/contact delivery mechanism | Required before real employee use | MVP uses a protected contact detail/action; no email sending integration is planned. |
| TLS certificate and inbound security-group policy | Required before AWS deployment | Deployment remains Phase 10 work. |
| Attachment malware scanner and retention period | Required before real employee use | Phase 3 stores uploads outside the public path with `pending_scan` status and denies download until an approved scanner integration marks them available. |

## Phase 9 remediation status

| Priority | Scope | Status | Evidence required before closing the slice |
|---|---|---|---|
| 0 | Ignore local env files, isolate local API credentials, scan in CI, document CLI-profile/EC2-role chain | Complete for approved slice | No shared/exported archive was present to remediate; the new tested package script excludes `.env`, dependency/build/upload/cache/virtual-environment/generated paths. The expanded path-only scanner passes locally and is in CI. Local credentials are forwarded only to the API container, never to the web container, and local branch is `main`. |
| 1 | Technology serialization, draft/applied search state, eligibility floor, deterministic explanations | Complete for approved slice | One `SEARCH_RESULT_THRESHOLD` controls eligibility and no-answer. Semantic explanations require >=0.60, summary context is global-ranked, and all requested API/UI regressions pass. |

### Priority 0–1 final closure validation — 2026-07-21

- **CI test configuration:** settings fixtures now use the fictional `<test-only-jwt-secret>` by default. The development-startup test explicitly sets `APP_ENV=development`; only the production-placeholder rejection test supplies `replace-with-a-long-random-secret-before-starting-the-api`.
- **API-level search coverage:** authenticated endpoint tests verify complete one- and multiple-technology strings, post-eligibility totals and pagination, deduplication, correct `has_next`, ineligible-result exclusion, and no-answer behavior when no candidate reaches `SEARCH_RESULT_THRESHOLD`.
- **Exact local CI-equivalent backend run:** with `APP_ENV=test` and `RAG_ENABLED=false`, `ruff check .`, `alembic upgrade head`, and `pytest -q` passed (**30 passed**); `alembic downgrade base`, `alembic upgrade head`, and `python scripts/seed_dev.py` then passed. The final revision is `202607210005 (head)` and the restored fictional corpus contains 24 employees and 36 solutions.
- **Frontend and source safety:** frontend typecheck, 11 frontend tests, and production build passed. The repository secret scan passed. `artifacts/knowledge-platform-source.zip` was created only through `package_source.py`; `verify_source_package.py` programmatically passed, confirming it contains no `.env`, `.git`, dependency/build/upload/virtual-environment/cache paths, or credential-like readable source content.
- **Scope boundary:** this closes the reviewed Priority 0 and Priority 1 issues only. Priority 2 and all other Phase 9 work remain unstarted.

### Local Bedrock search verification — 2026-07-21

- **Observed failure:** browser `POST /api/v1/search` returned HTTP 503 while PostgreSQL and the API health endpoint remained healthy. The UI correctly showed its retryable error state.
- **Root cause:** the base API Compose service had Bedrock enabled but did not receive the operator's ignored local AWS credentials, so Boto3 could not create a usable Bedrock request.
- **Correction:** Compose now forwards `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and optional `AWS_SESSION_TOKEN` to the API service only. `.env` remains ignored, excluded from packages, and unavailable to the web service.
- **Live validation:** after `docker compose up -d --force-recreate api`, a login as the fictional development employee followed by `POST /api/v1/search` for `Terraform` returned `200`, five verified results, `no_answer=false`, and `semantic_search=available`. Automated adapter/UI tests still avoid live AWS calls by design; this manual smoke test covers the local credential wiring.

## Phase 0 acceptance criteria

- [x] Supplied plan PDF read in full; workspace copy was verified byte-identical.
- [x] Locked stack, repository structure, scope boundaries, and ADR process documented.
- [x] Required documentation files, Mermaid architecture/ER diagrams, route map, component inventory, endpoint list, migration plan, and sample-data plan created.
- [x] Every specified UI screen and interaction state has implementation guidance.
- [x] RAG order, grounding boundary, no-answer path, and permission filtering are explicit.
- [x] Security controls, data boundaries, and test strategy are defined.
- [x] No Phase 1 or later application/deployment code was introduced.
- [x] Stakeholder approval received before Phase 1 began.

## Phase 1 acceptance criteria

- [x] `docker compose up --build -d` builds and starts PostgreSQL with pgvector, API, and web services.
- [x] PostgreSQL service uses the `pgvector/pgvector:pg16` image and persistent Docker volume.
- [x] FastAPI application exists with liveness/readiness health endpoints.
- [x] Settings validation blocks invalid production/RAG configuration and permits Phase 1 development startup without Bedrock credentials.
- [x] Alembic exists with an initial foundation migration and verified downgrade/upgrade path.
- [x] Seed skeleton exists and runs idempotently without inserting unapproved sample data.
- [x] Vite React TypeScript application exists with the approved dependency foundation.
- [x] Static visible shell copy is kept in `apps/web/src/content/uiCopy.ts`, derived from approved product language.
- [x] CI workflow exists for API lint/tests/migrations/seed and web typecheck/tests/build.
- [x] No Phase 2 authentication or product feature implementation was started.

## Phase 2 acceptance criteria

- [x] Passwords are verified with Argon2id; plaintext passwords and password hashes are never returned or audit logged.
- [x] `POST /auth/login` normalizes and validates credentials, applies per-process MVP throttling, returns a short-lived signed JWT, and records a safe audit event.
- [x] JWT validation enforces the configured algorithm, issuer, audience, expiry, not-before, subject, and token ID claims.
- [x] `GET /auth/me` rejects missing, invalid, revoked, inactive, and soft-deleted identities and returns only the permitted current-user shape.
- [x] `POST /auth/logout` persists the JWT ID and expiry in PostgreSQL so the current token is immediately rejected.
- [x] Role dependency checks reject unauthorized roles, with direct regression coverage.
- [x] The web client has login validation, an in-memory access-token strategy, protected-route redirect, authenticated shell, and sign-out action.
- [x] API errors use the documented common error envelope for authentication and validation failures.
- [x] Phase 2 migration downgrade and upgrade pass; no Phase 3 repository workflows, uploads, retrieval, or Bedrock features were started.

## Phase 3 acceptance criteria

- [x] Authenticated employees can create structured drafts containing problem, symptoms, exact error, environment, root cause, resolution steps, code evidence, visibility, and technology IDs.
- [x] Draft ownership, editable lifecycle state, optimistic update concurrency, submission, and archival reason requirements are enforced server-side and audited.
- [x] Detail and browse endpoints apply owner, verification status, visibility, organization scope, and administrator policy before returning records.
- [x] Own profile read/update works without exposing pending-policy contact fields; profile updates are audited.
- [x] Reviewer queue and immutable review decisions enforce reviewer role, local organization scope, submitted state, and no self-review. Verification changes the current lifecycle state.
- [x] Attachments enforce configured MIME, size, filename, PDF/text content checks, private storage, audit logging, and an unavailable-until-scanned download gate.
- [x] Temporary fictional database records cover draft/edit/submit/review/visibility/profile/upload/archive behavior and are removed after each integration test.
- [x] No Bedrock request, fake AI output, full UI-foundation implementation, search retrieval, or Phase 4+ feature was introduced.

## Phase 4 acceptance criteria

- [x] Semantic light/dark tokens implement the approved colour, typography, spacing, radius, border, shadow, focus, reduced-motion, control-size, and content-width rules.
- [x] The responsive shell includes desktop sidebar collapse behavior, mobile navigation sheet, compact header, role-aware navigation, theme control, and sign-out action.
- [x] Command navigation opens from the header and `Ctrl/Cmd+K`, closes on Escape, and provides permitted route actions.
- [x] Shared `Button`, `PageHeader`, `StatePanel`, and `LoadingSkeleton` components establish consistent interactive, empty, error, permission-denied, not-found, and loading foundations.
- [x] All planned route paths render through authenticated and role-aware route protection, with intentionally deferred workflows clearly represented by approved state copy rather than fabricated functionality.
- [x] Dashboard, search, authoring, solution, profile, reviewer, administration, forbidden, and not-found route foundations follow the approved hierarchy and mobile behavior.
- [x] Static UI strings added for the Phase 4 shell are documented in `UI_COPY.md` and compiled through `src/content/uiCopy.ts`.
- [x] Browser checks verified the desktop shell, command palette, and 320px navigation. Typecheck, component tests, and production build pass without console warnings.
- [x] No keyword retrieval, Bedrock request, fake AI result, reviewer decision UI, or Phase 5+ interaction was implemented.

## Phase 5 acceptance criteria

- [x] PostgreSQL maintains weighted FTS documents for challenge, solution, and technology content through an Alembic migration and safe trigger functions.
- [x] Authenticated, rate-limited `POST /search` validates a 3–1000-character query and metadata filters, runs FTS plus normalized exact-error matching, then applies existing object-level visibility checks before serializing results.
- [x] Search supports verified-only, technology, department, team, visibility, relevance/newest sort, and bounded pagination parameters; unauthorized records neither appear in results nor contribute to totals.
- [x] Search responses return structured PostgreSQL solver identity, technical excerpts, match reasons, pagination, and a logged query ID; no email/contact field is included pending policy approval.
- [x] Search logs and audit events record the request safely. Search-log retrieval is restricted to its owner or an administrator.
- [x] The UI synchronizes query, verified filter, sort, and pagination through the URL; renders loading, error/retry, no-answer, result-list, and mobile-safe preview-drawer states using approved static copy.
- [x] The API reports keyword search as available and semantic retrieval/grounded summaries as unavailable; a requested summary returns the documented `503 semantic_search_unavailable` response. No Bedrock client, embedding, fake vector, fake summary, or generated ownership/contact data was introduced.
- [x] Repository coverage verifies exact-error results, structured solver data, log authorization, and restricted-result exclusion; UI coverage verifies search and preview interaction.

## Phase 6 acceptance criteria

- [x] The idempotent development seed supplies a persistent, explicitly fictional corpus for future embedding/retrieval evaluation without real identities, contact data, or secrets.
- [x] Alembic migration `202607210005_phase_6_embeddings` adds `solution_embeddings` with a pgvector column, content/model hash uniqueness, and a solution/model index; no vector index is selected before the approved model dimension and corpus benchmark.
- [x] The embedding document contains only permitted technical challenge/solution/technology content and rejects detected secret material before a Bedrock invocation. It excludes names, emails, titles, teams, departments, contact fields, roles, ownership, verification, and permissions.
- [x] The adapter supports the documented Amazon Titan and Cohere Bedrock embedding request/response contracts, validates model/provider configuration and returned dimensions, and surfaces dependency/response failures without synthetic vectors.
- [x] SHA-256 content hashing prevents duplicate invocations for unchanged records. `scripts/embed_verified_solutions.py` re-embeds verified records only when their permitted content or selected model changes.
- [x] Unit and database tests cover adapter contracts, secret rejection, invalid dimension rejection, pgvector persistence, and unchanged-content deduplication without making an AWS call.
- [x] A live, least-privilege Bedrock invocation against the configured Amazon Titan Text Embeddings V2 model succeeds from the configured Region and IAM identity. The fictional corpus holds 30 stored vectors with the configured 1,024 dimensions; an immediate re-run created 0 and skipped 30 unchanged records.
- [x] No vector retrieval/merge/rerank, query embedding endpoint, generated summary, fake vector, or Phase 7+ behavior was introduced.

## Phase 7 acceptance criteria

- [x] Authenticated `POST /search` creates a real query embedding through the configured Bedrock adapter and returns a safe dependency-unavailable error if that invocation fails.
- [x] pgvector cosine candidates, PostgreSQL FTS/exact-error candidates, metadata filters, and existing object-level visibility rules are merged without client-controlled authorization.
- [x] A verified keyword/exact candidate awaiting an embedding remains eligible; unavailable score channels are reweighted rather than fabricated.
- [x] Deterministic reranking returns semantic, keyword, and exact-error reasons, structured PostgreSQL solver fields, bounded pagination, a logged confidence, and a threshold-gated `no_answer` response.
- [x] Grounded summaries and citations remain absent; `include_summary=true` still returns the documented unavailable response until Phase 8.
- [x] The versioned evaluation fixture covers all 36 fictional seeded solutions through expected top-five groups plus no-answer and permission cases, and its structural regression test passes.
- [x] Repository integration coverage uses a deterministic fake adapter; a separate authenticated live search confirmed configured Bedrock query embedding, hybrid result delivery, and a non-no-answer confidence result without exposing secrets.
- [x] No generated summary, inferred expert/contact data, architecture change, fake embedding, or Phase 8 behavior was introduced.

## Phase 8 acceptance criteria

- [x] `POST /search` can request a summary only after authenticated hybrid retrieval has applied metadata and object-level authorization filters and the confidence gate passes.
- [x] Bedrock receives at most three reconstructed permitted technical documents; employee names, emails, titles, teams, departments, contacts, ownership, verification, roles, and permissions remain outside the model boundary.
- [x] The generation adapter uses a strict JSON-only prompt and validates response shape, UUID citations, citation allow-list membership, uniqueness, inline citation placement, non-empty-summary citations, secret safety, and email/contact suppression.
- [x] No-answer searches do not invoke generation. Bedrock dependency and invalid-output conditions preserve source records, return no fabricated summary, and expose safe machine-readable summary status.
- [x] Search logs and audit events record only whether generation was requested and safely used; prompts, completions, credentials, contact data, and employee data are not logged.
- [x] Deterministic adapter tests cover valid citations and unsafe/ungrounded output; repository integration covers the summary route with a controlled adapter.
- [x] A live authenticated request using the configured Bedrock model returned a non-empty grounded summary with three validated citations from authorized fictional records.
- [x] No Phase 9 UI workflow, synthetic answer, model-generated employee/contact/ownership data, or architecture change was introduced.

## Validation commands

Commands run from `D:\Expert Discovery Platform`:

```powershell
docker compose config
docker compose up --build -d
Invoke-WebRequest -Uri 'http://localhost:8000/api/v1/health/live' -UseBasicParsing | Select-Object StatusCode,Content
Invoke-WebRequest -Uri 'http://localhost:8000/api/v1/health/ready' -UseBasicParsing | Select-Object StatusCode,Content
Invoke-WebRequest -Uri 'http://localhost:5173' -UseBasicParsing | Select-Object StatusCode
docker compose ps
docker compose exec -T api pytest
docker compose exec -T api ruff check .
docker compose exec -T api alembic downgrade base
docker compose exec -T api alembic upgrade head
docker compose exec -T api python scripts/seed_dev.py
docker compose exec -T web npm run typecheck
docker compose exec -T web npm test
docker compose exec -T web npm run build
git status --short
```

Phase 2 additions:

```powershell
docker compose up --build -d
docker compose exec -T api pytest
docker compose exec -T api ruff check .
docker compose exec -T web npm test
docker compose exec -T web npm run typecheck
docker compose exec -T web npm run build
docker compose exec -T api alembic downgrade 202607200001
docker compose exec -T api alembic upgrade head
docker compose exec -T api python scripts/seed_dev.py
Invoke-WebRequest -Uri 'http://localhost:8000/api/v1/health/live' -UseBasicParsing | Select-Object StatusCode,Content
Invoke-WebRequest -Uri 'http://localhost:8000/api/v1/health/ready' -UseBasicParsing | Select-Object StatusCode,Content
Invoke-WebRequest -Uri 'http://localhost:5173/login' -UseBasicParsing | Select-Object StatusCode
```

Phase 3 additions:

```powershell
docker compose up --build -d
docker compose exec -T api pytest
docker compose exec -T api ruff check .
docker compose exec -T web npm run typecheck
docker compose exec -T web npm test
docker compose exec -T web npm run build
```

Phase 8 additions:

```powershell
docker compose up -d api
docker compose exec -T api ruff check .
docker compose exec -T api pytest -q
docker compose exec -T web npm run typecheck
docker compose exec -T web npm test
docker compose exec -T web npm run build
```

Phase 4 additions:

```powershell
docker compose exec -T web npm run typecheck
docker compose exec -T web npm test
docker compose exec -T web npm run build
docker compose restart web
```

Phase 5 additions:

```powershell
docker compose exec -T api alembic upgrade head
docker compose exec -T api pytest -q
docker compose exec -T api ruff check .
docker compose exec -T web npm run typecheck
docker compose exec -T web npm test
docker compose exec -T web npm run build
```

Phase 6 additions:

```powershell
docker compose exec -T api alembic upgrade head
docker compose exec -T api python scripts/seed_dev.py
docker compose exec -T api pytest tests/test_embeddings.py tests/test_settings.py -q
docker compose exec -T api python scripts/embed_verified_solutions.py
```

Phase 7 additions:

```powershell
docker compose up -d api
docker compose exec -T api ruff check app/services/search.py app/api/search.py tests/test_repository.py tests/test_rag_evaluation_fixture.py
docker compose exec -T api pytest tests/test_repository.py tests/test_rag_evaluation_fixture.py -q
docker compose exec -T web npm run typecheck
docker compose exec -T web npm test
docker compose exec -T web npm run build
```

## Error record

No Phase 0 application error occurred. The initial PDF extraction attempt failed because the system console used a Windows code page that could not encode a Unicode arrow. The failing layer was local console output, not the project. The smallest correction was to set UTF-8 output for the read-only extraction command; all 36 pages were then read successfully. No project code change was needed.

Repository status inspection returned `fatal: not a git repository (or any of the parent directories): .git`. The failing layer is repository initialization/metadata, not application code. CI files were created locally, but GitHub execution remains blocked until the repository is repaired or initialized with explicit approval.

`docker compose up --build -d` first failed with Docker Desktop pipe access denied from the sandbox. The failing layer was local Docker engine access. The same command was rerun with explicit elevated approval.

The initial Docker build timed out from the tool at 60 seconds while Docker continued in the background and produced the images. The validation command was rerun later with the exact acceptance command and completed successfully.

The timed-out build/start left stale project containers and caused a container-name conflict. The failing layer was Docker Compose local state. The smallest valid correction was `docker compose down --remove-orphans`, without `-v`, preserving persistent volumes.

The API first exited because Pydantic Settings tried to JSON-decode comma-separated environment list values for upload types and CORS origins. The failing layer was configuration parsing. The fix used `NoDecode` with explicit CSV validators and added a regression settings test.

The first Alembic migration failed with `psycopg.errors.DuplicateObject: type "app_role" already exists` because enums were explicitly created and also auto-created during table creation. The failing layer was migration DDL ownership. The fix set PostgreSQL enum objects to `create_type=False`; downgrade/upgrade validation now passes.

The first API test run collected zero tests because the Docker Compose API service did not mount the `tests` directory. The failing layer was container development wiring. The fix mounts tests in Compose and copies tests into the API image.

The web typecheck failed because Vitest config typing was not active and Vite client env types were missing. The failing layer was TypeScript configuration. The fix imports `defineConfig` from `vitest/config` and adds `vite-env.d.ts`; typecheck now passes.

The seed skeleton initially failed with `ModuleNotFoundError: No module named 'app'` when executed as `python scripts/seed_dev.py`. The failing layer was script import path. The fix appends the project root to `sys.path`; the seed skeleton now runs successfully.

Phase 2 startup first failed with `sqlalchemy.orm.exc.MappedAnnotationError` for the `audit_logs.metadata` field. The failing layer was ORM type mapping; the migration itself had succeeded. The smallest valid correction explicitly maps the existing field as PostgreSQL `JSONB`.

The initial authentication tests then found `invalid input value for enum app_role: "EMPLOYEE"` and an audit-log `NULL identity key`. The failing layer was ORM serialization/default metadata. The correction maps role values to the existing lowercase PostgreSQL enum values and declares database-generated UUID defaults for mapped `users` and `audit_logs` records. API tests now pass.

The initial Vitest suite failed because its module mock referenced a top-level variable before Vitest hoisted the mock factory. The failing layer was test mocking, not the application route. The correction keeps the mock function inside the hoisted factory; the web authentication tests now pass.

The Phase 2 `docker compose up --build -d` command exceeded the command tool's 124-second observation limit while Docker continued its build. The failing layer was command observation timing, not the application. Docker status and logs confirmed that the rebuilt API, PostgreSQL, and web services started, and subsequent tests and health checks passed.

Phase 3 repository tests first failed with `sqlalchemy.orm.exc.DetachedInstanceError` because fixture instances expired after their setup transaction committed. The failing layer was SQLAlchemy session test wiring. The smallest correction set `expire_on_commit=False` on the application session factory; the API suite now passes and this also avoids unnecessary reloads of committed objects in normal request services.

Phase 3 lint then found a missing `can_view_challenge` import in the browse endpoint. The failing layer was route module wiring. The correction added the import and added browse coverage to the repository test.

Two failed Phase 3 fixture setups left exactly identified fictional departments, teams, technologies, profiles, and users in the local development database because teardown did not run after the detached-instance error. The failing layer was test cleanup after fixture failure. After read-only identification, only those exact IDs were deleted in a transaction; the seed skeleton then confirmed zero departments. The fixture now uses non-expiring sessions and removes temporary attachment files as well as database records.

Phase 4 initially failed TypeScript parsing in the first compact `AppShell` JSX implementation. The failing layer was frontend source syntax. The smallest valid correction rewrote that component as structured JSX and added a regression test for command navigation and role-denied routes.

The local Vite process continued serving an earlier transformed module after a Windows-mounted source change, even though the current source built successfully. The failing layer was development-server file watching. Restarting only the web container loaded the current shell; browser inspection then verified the expected desktop, command-palette, and mobile-navigation DOM. The temporary browser test account and its exact audit records were removed afterward.

The Phase 4 role-denial regression test initially selected two intentional headings with the same permission text: the page heading and the state-panel heading. The failing layer was test query specificity, not route authorization. The smallest valid correction targets the state-panel level-two heading; the route behavior remains covered without altering the UI.

The initial Phase 5 FTS trigger function referenced the target `UPDATE` alias from a lateral `FROM` clause, which PostgreSQL rejects. The failing layer was the new database trigger function. A CTE-based function now derives the challenge, solution, and technology text before updating the target row; the applied local revision is followed by a corrective Alembic migration so already-migrated databases recover safely. Repository regressions now cover challenge creation and exact-error search.

The first Phase 5 UI regression test used ambiguous accessible text from both the search input label and compact header action. The failing layer was test selector specificity. The correction targets the input placeholder and an exact search button name; the accessible UI remains unchanged.

The Phase 6 embedding persistence test initially mapped pgvector storage as a text column, and PostgreSQL correctly rejected the implicit `varchar` value. The failing layer was SQLAlchemy type mapping, not pgvector. The correction uses a small explicit `PgVector` SQLAlchemy type that binds vectors as pgvector literals; regression coverage now proves persistence through the real `vector` column.

An earlier failed Phase 6 embedding fixture did not reach its cleanup path and left one exactly identifiable `embedding-…@example.test` user plus its related fictional organization, technology, challenge, and solution rows in the local database. The failing layer was failed-test cleanup. After read-only identification, only those test-pattern rows were deleted in dependency order; the idempotent seed then reconfirmed the intended 24 fictional employees, 36 solutions, and 30 verified solutions.

The first real Bedrock adapter run failed before invocation because Docker Compose passed an empty `AWS_PROFILE`, which boto3 interpreted as a requested profile named `""`. The failing layer was blank environment handling. The adapter now removes only a blank profile variable before constructing the client, preserving normal IAM/credential-chain behavior; the retry succeeded and stored a real vector for a fictional record.

After enabling local embedding configuration, a settings test inherited the real Bedrock values from the environment and no longer represented a missing-configuration case. The failing layer was test isolation. The regression test now explicitly supplies blank embedding fields when asserting configuration validation.

Phase 7 index experimentation ran `docker compose exec -T api alembic upgrade head` with an HNSW cosine index over the intentionally dimension-flexible `vector` column. PostgreSQL returned `psycopg.errors.InvalidParameterValue: column does not have dimensions`; the failing layer was index DDL, not retrieval. Hard-coding the current 1,024 dimensions would reduce the approved model-change/ADR boundary, so the smallest architecture-preserving correction removed the unapplied migration and retained the bounded cosine scan for the 30-vector fictional corpus. The dimension-specific index remains a Phase 10 benchmark/deployment decision.

The first Phase 8 settings regression inherited the newly configured local generation values, so its expected missing-configuration validation did not fail. The failing layer was test isolation. The smallest correction explicitly supplied blank Region/model values in that negative test; focused adapter, repository, and settings tests then passed.

Phase 9 browser inspection showed `/search` rendering the older `WorkflowPage` placeholder even though the mounted `App.tsx` correctly routes that path to `SearchPage`. The failing layer was the Windows-mounted Vite transformed-module cache, not routing or search data. The smallest correction was `docker compose restart web`; the current source then typechecked successfully. Refresh the browser after the restart to receive the current module.

During Phase 9 Priority 0 validation, the first liveness request ran immediately after `docker compose ... up -d api` recreated the container and returned `ConnectionRefusedError`. The failing layer was normal API startup timing while Alembic and Uvicorn initialized, not credential configuration or application code. Container status and logs showed successful startup; the configured health check then reported healthy and the repeated liveness request returned `200`. No code correction was required.

Phase 9 Priority 1 live UI verification still rendered technology tags as `{ K u b e r n e t e s }` after the frontend cache was removed. The live PostgreSQL layer returned an untyped `array_agg` value as `list ['{', 'K', 'u', ..., '}']`; the failing layer was backend aggregate serialization, not the browser. `_technology_names` now recognizes and recursively normalizes that driver-specific literal shape, with regression coverage. After restarting the API, an authenticated fictional-data search returned only `"Kubernetes"`; the browser must perform a fresh search to replace its cached pre-fix response.

During the final Priority 0-1 validation, one combined Docker command exceeded the 124-second command-observation limit and Docker Desktop briefly lost its Linux engine pipe. The failing layer was local Docker execution, not the application. The corrective action was to split validation into isolated commands after Docker Desktop recovered. API lint/tests, frontend typecheck/tests/build, clean migration downgrade/upgrade, two idempotent seed runs, packaging, and secret scanning then completed successfully. A first global-grounding regression fixture also used a non-persisted solution UUID and correctly failed its foreign-key check; the test now creates the fixture solution through the repository API before exercising the route.
