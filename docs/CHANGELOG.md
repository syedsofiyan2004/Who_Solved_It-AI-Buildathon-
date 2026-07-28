# Changelog

All notable project changes are documented here. The format is intentionally lightweight during the MVP.

## [Unreleased]

### Changed - Phase 9 remediation in progress

- Began the approved Priority 0 security cleanup and Priority 1 search-correctness remediation only; Phase 10 and the remaining Phase 9 workflows were not started.
- Removed AWS static credential forwarding from the base Compose configuration, added a path-only repository secret scanner in CI, and documented local AWS CLI-profile versus EC2-instance-role authentication.
- Normalized PostgreSQL technology aggregates to complete string arrays, introduced a per-result retrieval eligibility floor, and made search explanations signal-derived and capped at three.
- Clarified the search interface's applied query and rendered the returned explanations rather than a generic match label.
- Corrected the remaining psycopg untyped-array shape, which can arrive as a list of individual PostgreSQL literal characters, so live result tags render as complete technology names.
- Completed the approved Priority 0-1 correction slice: safe source packaging, expanded path-only secret detection and tests, `main` branch alignment, one retrieval/no-answer threshold, minimum semantic-reason confidence, globally ranked grounding context, and expanded backend/frontend regressions.
- Restored local semantic search configuration while keeping provider credentials server-side only. A live authenticated `Terraform` search now returns verified results.
- Closed the remaining reviewed Priority 0–1 validation gaps: CI-safe test settings, endpoint-level search metadata coverage, CI-equivalent migration/seed validation under `APP_ENV=test`, and a retained verified source archive with no local environment file or credential-like content.

### Added - Phase 8 grounded RAG answers

- Strict grounded-generation adapter with a JSON-only prompt, permitted technical context reconstruction, source UUID citation validation, secret/contact output checks, and no synthetic fallback.
- Optional `POST /search` summaries that run only for confidence-passing authorized results, with source-preserving unavailable/invalid-response states and safe generation audit metadata.
- Controlled adapter regression coverage plus successful grounded-summary validation using fictional records only.

### Fixed - Phase 8 validation

- Isolated the RAG configuration-negative test from local generation environment settings.

### Added - Phase 7 hybrid retrieval

- Authenticated hybrid solution search using configured query embeddings, bounded pgvector cosine candidates, PostgreSQL FTS/exact-error candidates, object-level visibility filtering, deterministic merge/rerank, confidence logging, and no-answer gating.
- A verified keyword/exact-result fallback for records awaiting re-embedding, without fabricating a semantic score.
- Versioned fictional retrieval evaluation fixture covering the 36 seeded solutions through expected top-five groups plus no-answer and permission cases.

### Fixed - Phase 7 retrieval configuration

- Set the Docker Compose development default for `SEARCH_SIMILARITY_THRESHOLD` to `0.35` rather than passing a blank value into the API container.
- Deferred a dimension-specific HNSW index after PostgreSQL correctly rejected indexing the deliberately dimension-flexible pgvector column; the bounded scan is appropriate for the fictional corpus and preserves the approved model-change boundary.

### Added - Phase 6 semantic embeddings

- Idempotent, fictional-only development corpus with 24 `example.test` employees, 12 technologies, and 36 technical solution records.
- pgvector `solution_embeddings` storage, canonical permitted technical embedding documents, secret detection, content hashes, and verified-only re-embedding command.
- Strict embedding adapter contracts with configuration, dimension, malformed-response, and dependency failure handling that never fabricates a vector.
- Adapter and pgvector persistence tests using controlled in-process responses rather than AWS calls.

### Fixed - Phase 6 live validation

- Treat a blank `AWS_PROFILE` supplied by Docker Compose as absent so boto3 uses the approved credential chain.
- Made embedding configuration tests independent from locally configured provider environment values.

### Added - Phase 5 keyword search

- PostgreSQL weighted full-text search documents refreshed from challenge, solution, and technology content, with existing FTS/trigram indexes used for keyword and exact-error retrieval.
- Authenticated, rate-limited keyword-search and search-log endpoints with bounded filters, deterministic relevance/newest ordering, pagination, visibility filtering, audit events, and owner/admin log access.
- Search interface with URL-synchronized query/filter/sort/page state, loading/error/no-answer results, structured solver/result cards, and a responsive result preview drawer.
- API and web regression coverage for exact-error matching, restricted-content exclusion, search-log authorization, result rendering, and preview interaction.

### Fixed - Phase 5 validation

- Replaced an invalid correlated FTS trigger update with a CTE-based function and applied a corrective Alembic revision for databases that had already received the first Phase 5 migration.
- Made keyword-search UI tests select the intended control where the accessible label is intentionally shared with a compact header action.

### Added - Phase 4 UI foundation

- Semantic design tokens with light/dark behaviour, responsive layout rules, focus styles, reduced-motion support, and approved density/radius/shadow treatment.
- Reusable button, page-header, loading, and shared state components.
- Responsive app shell with collapsible desktop sidebar, mobile navigation sheet, theme control, command surface, and role-aware navigation.
- Route foundations for dashboard, search, authoring, solution detail, profile, reviews, administration, forbidden, and not-found states.
- UI tests for command navigation and role-denied routing, plus browser verification at desktop and 320px mobile sizes.

### Fixed - Phase 4 validation

- Replaced a compact JSX shell implementation that failed TypeScript parsing with maintainable structured JSX.
- Restarted the local Vite container after Windows-mounted file watching served a stale transformed module.
- Enabled React Router future flags to remove known test-console warnings.
- Made the role-denial regression assertion target the permission state rather than the intentionally duplicated page and state headings.

### Added - Phase 3 knowledge repository

- Structured challenge and solution models, drafts, ownership-safe edits, submission, archival, details, and authorized browsing.
- Profile read/update endpoints, technology vocabulary listing, scoped reviewer queue, and immutable verification decisions.
- Object-level company, department, team, restricted, administrator, owner, and reviewer visibility enforcement.
- Private local attachment intake with MIME, size, content, filename, audit, and scan-pending safeguards.
- Repository integration tests using temporary fictional users, profiles, technology, drafts, reviews, visibility cases, uploads, and archive actions.

### Fixed - Phase 3 validation

- SQLAlchemy post-commit session expiry in integration tests, a missing browse authorization import, and upload cleanup for failed persistence/test artifacts.

### Added - Phase 2 authentication

- Argon2id password hashing through the documented `pwdlib` dependency.
- Password login, protected current-user API, and JWT logout revocation endpoints.
- Short-lived JWTs with issuer, audience, algorithm, expiry, not-before, subject, and token-ID validation.
- PostgreSQL `revoked_tokens` migration and safe authentication audit events.
- Role dependency helpers and regression coverage for protected access, role denial, invalid login, and revocation.
- Login form with React Hook Form/Zod validation, memory-only access-token storage, protected client route, and sign-out action.

### Fixed - Phase 2 validation

- Explicit JSONB mapping for audit metadata, lowercase PostgreSQL role-enum mapping, and ORM UUID server defaults.
- Vitest authentication mock hoisting.

### Added - Phase 1 foundation

- FastAPI application skeleton with public liveness and readiness health endpoints.
- Pydantic settings validation for environment, JWT, upload, CORS, search and RAG configuration.
- SQLAlchemy database session setup.
- Alembic migration environment and first foundation migration for PostgreSQL extensions, enums, core relational tables, audit fields, FTS column, and indexes.
- Development seed skeleton that runs without inserting unapproved sample data.
- Vite React TypeScript frontend skeleton with Tailwind, React Router, TanStack Query, Motion for React, Lucide, Radix/shadcn foundation dependencies, React Hook Form and Zod dependencies.
- Minimal Phase 1 web shell that verifies frontend startup and API health connectivity.
- Docker Compose stack for PostgreSQL with pgvector, API, and web services.
- API and web Dockerfiles.
- GitHub Actions CI workflow for linting, tests, migrations, seed skeleton, typecheck, and build.
- `.gitignore` for local secrets, dependency folders, build output and caches.

### Fixed - Phase 1 foundation validation

- Corrected Pydantic Settings parsing for comma-separated environment list values.
- Prevented duplicate PostgreSQL enum creation in the initial Alembic migration.
- Mounted/copied API tests into the containerized development/test path.
- Added Vitest and Vite client typings for web typecheck.
- Fixed the seed skeleton import path when executed as a script.

### Added - Phase 0 requirements and design lock

- Approved monorepo directory skeleton with no application implementation.
- Product requirements, architecture, UI specification and approved static copy.
- Database, API, RAG, security, and test design contracts.
- Phase acceptance criteria, migration plan, sample-data plan, and blocker register.
- ADR governance and environment-variable template.

### Not added

- No authentication implementation, knowledge repository workflows, retrieval, AI integration, RAG summaries, reviewer workflows, Nginx configuration, or deployment scripts were started in Phase 1.

## Final local product build - 2026-07-26

- Rebranded the showcase product as **Minfy Resolve** and retained a local-only Docker architecture with no AWS deployment requirement.
- Added NVIDIA-hosted AI adapters for semantic embeddings and grounded summaries while preserving keyword/exact-error search when AI is unavailable.
- Configured `nvidia/nemotron-3-embed-1b` for query/passage embeddings and `moonshotai/kimi-k2.6` for grounded summaries.
- Replaced the small fictional seed with an idempotent original synthetic corpus containing 43 supplied employee profiles, 49 technologies, 53 incident blueprints, seven environments, and 371 solution records.
- Added Cloud/DevOps, SREaaS, Intelligent Data Applications, AI/Data Science, leadership, management, and People Operations profiles with temporary showcase email conventions.
- Redesigned the authenticated UI into a premium connected product shell with responsive navigation, semantic light/dark themes, a product home, expert directory, and technical reading views.
- Converted search into a URL-preserved master-detail workspace so opening a solution or solver does not discard query, filters, page, cached results, or scroll context.
- Added rich solution/solver panels, upgraded result cards, improved authoring and review workspaces, and fixed light-theme contrast defects caused by dark-only text assumptions.
- Made authoring submission use the persisted draft ID, permitted incomplete draft updates, protected autosave against stale responses, and corrected active verification metadata after material edits.
- Added final local setup, data-provenance, AI configuration, and safe source-package documentation.
