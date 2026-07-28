# Test Plan

## 1. Test strategy

Run fast unit/component tests on change, API/database integration tests against ephemeral PostgreSQL+pgvector in CI, contract tests at service boundaries, and end-to-end/responsive/accessibility suites before phase completion. AI-provider calls are never required for normal unit tests: adapter contract tests use recorded valid/invalid responses; a separately gated integration suite uses approved provider credentials and explicitly records dependency-unavailable outcomes.

## 2. Coverage matrix

| Level | Scope | Examples |
|---|---|---|
| Backend unit | Services, policies, serializers, hashing, ranker | visibility matrix, owner/edit rule, content hash changes, score normalization, no-answer threshold |
| Frontend component | Isolated accessible UI | login form, filter chips, result card/drawer, all submission steps, skeleton/empty/error/disabled states, mobile nav |
| API integration | FastAPI + PostgreSQL migrations | login, protected endpoint, challenge lifecycle, review, feedback idempotency, pagination/error envelope |
| Database | Constraints, indexes, migrations | uniqueness, visibility checks, cascade/restrict behavior, FTS/exact-error/vector query plan and migration upgrade |
| Authorization | Role/object matrix | forbidden detail/download/contact/review/admin access; AI-provider context excludes denied record |
| Retrieval | Keyword/exact/vector/merge/rerank | expected top-five, confidence gate, protected record exclusion, deterministic tie break |
| AI-provider adapter | Request/response/failures | model config, dimensions, timeout, throttling, malformed/citation-invalid output, no fake fallback |
| RAG evaluation | Fixed labeled corpus | Recall@5, solver accuracy, permission/no-answer/citation accuracy |
| E2E | Browser workflow | login → submit → review → search → details/contact → feedback; error/retry path |
| Responsive/accessibility | Desktop/mobile and assistive tech | 320px mobile navigation, keyboard command palette, focus trap, contrast, screen-reader status/live updates |
| Regression/security | Previously fixed defects and controls | rate limits, XSS/Markdown sanitization, upload rejects, secret redaction, CORS, JWT expiry |

## 3. Required sample and evaluation data

Create 10–20 fictional employees across at least 3 departments and 5 teams, including 1 administrator, 1 reviewer, and varied employee visibility scopes. Create 30–50 fictional verified/submitted/draft solutions spanning AWS, Terraform, Docker, Kubernetes, Python, React, PostgreSQL, networking, Linux, authentication, CI/CD, and security. Include duplicate-like incidents, distinct similar wording, long exact errors, zero-match queries, restricted/admin records, helpful and not-helpful feedback, and valid/invalid attachments.

Evaluation row schema: `query`, `expected_solution_id`, `expected_solver_id`, `expected_technology_ids`, `expected_top_five_ids`, `expected_no_answer`, `caller_scope`, `expected_permission_behavior`, `expected_citation_ids`. Maintain this corpus under version control once sample data is approved; it must contain no real employee data or secrets.

## 4. Phase gates

| Phase | Required evidence before complete |
|---|---|
| 0 | Documentation links/diagrams render; required file/section checklist passes; no app feature created. |
| 1 | Clean build/start, health checks, migration upgrade/downgrade policy test, env validation, seed idempotency. |
| 2 | Auth/expiry/role/object API and protected-route tests; audit test. |
| 3 | CRUD lifecycle, review/visibility, upload validation, profile/feedback tests and UI states. |
| 4 | Component snapshots where useful, keyboard/a11y assertions, desktop/mobile visual checks. |
| 5 | FTS/error/filter/sort/pagination integration and evaluation baseline. |
| 6 | Hash/dimension/re-embed and AI-provider failure adapter tests. |
| 7 | Hybrid ranking and permission-filter evaluation gates. |
| 8 | Grounding/citation/no-answer/AI-provider-unavailable integration and evaluation gates. |
| 9 | E2E interaction, responsive, accessibility, no-console-warning checks. |
| 10 | Full regression/security suite, production image/config smoke test, local Docker end-to-end validation. |

## 5. Test execution policy

Exact commands are introduced with Phase 1 tooling and recorded in `IMPLEMENTATION_STATUS.md`. Every bug follows the error protocol in `SECURITY.md`; a regression test accompanies a code fix when feasible. Failing tests block phase completion and cannot be worked around by changing the architecture or skipping the feature.

## 6. Phase 9 Priority 0-1 regression additions

- Repository secret scanner: fail only with affected paths when an AKIA/ASIA key, private key, GitHub token, non-placeholder AWS/token/API-key/JWT-secret assignment, or password-bearing database URL occurs outside ignored local `.env`; exercise it from the repository root and in CI. Package-export tests verify that local env, dependencies, builds, uploads, virtual environments, caches, and generated artifacts are absent.
- Configuration: reject an eligibility floor below the no-answer threshold and report missing AI-provider configuration by variable name only.
- Search serialization: assert PostgreSQL aggregate strings and native arrays both become complete `list[str]` technology values.
- Search ranking: assert one/multiple technology serialization, ineligible-result exclusion, accurate totals, pagination after filtering, deduplication, one-threshold no-answer behavior, and stable explanations; integration coverage confirms summary context uses the global ranked source cap.
- Search UI: assert complete technology chips, URL-refresh restoration, browser back/forward restoration, immediate loading, no-answer, error/retry, and draft-versus-applied-query behavior.
