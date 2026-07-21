# Product Requirements Document

## 1. Product definition

The Technical Knowledge and Expert Discovery Platform is an internal web application where employees record solved technical roadblocks and other authorized employees retrieve verified historical solutions and the person who solved them. Its primary outcomes are faster problem resolution, reusable institutional knowledge, and trustworthy expert discovery.

It is not a generic chatbot, ticketing system, employee social network, project-management system, or messaging replacement.

## 2. Users and roles

| User | Primary need | Authority |
|---|---|---|
| Employee | Find an authorized solution, record a solved problem, maintain own drafts/profile, give feedback | Read allowed records; create/edit own drafts and submissions |
| Reviewer | Validate technical quality and visibility of submissions | Employee authority plus review/verify/reject assigned submissions |
| Administrator | Administer users, organization metadata, restricted content and audit access | Full platform authority, subject to audit logging |

## 3. Goals and success measures

- Return authorized, relevant historical solutions for technical roadblocks.
- Show verified ownership and only approved company contact details from PostgreSQL.
- Preserve enough technical context to make a solution reproducible.
- Make search useful with keyword search before Bedrock is available; clearly state the dependency state for semantic/RAG features.
- Require a grounded citation for every generated summary.

Initial measures: Recall@5, correct solver retrieval, permission-filter accuracy, no-answer accuracy, citation accuracy, verified-solution percentage, and helpful-feedback rate. Baselines are established after seed-data evaluation; no numerical target is invented in Phase 0.

## 4. MVP scope

### Included

Login/logout; employee profiles; dashboard; draft/save/edit/submit solved problems; symptoms, exact errors, root causes, steps and code snippets; technology tags; reviewer verification; hybrid search; result preview; solution detail; authorized solver contact; helpful/not-helpful feedback; responsive UI; Docker local environment; minimal EC2 deployment; automated tests; and seed data.

### Explicitly excluded

Slack, Teams, Jira and GitHub synchronization; private-email/message ingestion; activity tracking; voice input; native mobile app; advanced analytics; multi-region/DR; RDS/Aurora; ECS/EKS/Kubernetes; ALB; CloudFront; Cognito; NAT gateway; and microservices.

## 5. Core user stories

1. As an employee, I can log in and see only data I may access.
2. As an employee, I can search with a natural-language description and optional filters to find matching past solutions.
3. As an employee, I can see the original solution, root cause, resolution steps, verification state, and allowed solver contact information.
4. As an employee, I can create a draft, recover it, edit it, and submit a complete solved problem for review.
5. As a reviewer, I can approve, reject, request changes to, and set appropriate visibility for a submitted solution.
6. As an employee, I can mark a retrieved solution helpful or not helpful without changing its verification state.
7. As an administrator, I can manage organizational metadata and audit high-risk actions.

## 6. Functional requirements

| ID | Requirement | Acceptance condition |
|---|---|---|
| FR-01 | Authenticate with password and JWT | Protected API/page access rejects missing, invalid, expired tokens. |
| FR-02 | Enforce RBAC and object authorization | Role and visibility tests cover every protected resource action. |
| FR-03 | Manage employee profiles | Structured name, job title, team, department, skills and approved contact fields are rendered only when allowed. |
| FR-04 | Author solutions | Multi-step form validates title, problem, symptoms, root cause, steps, tags, visibility, and attachments; drafts persist. |
| FR-05 | Review solutions | Reviewer decision, rationale, timestamp, and reviewer are retained; only eligible records are marked verified. |
| FR-06 | Search historical knowledge | Hybrid ranking combines vector, PostgreSQL full-text, exact error, filters, verification, feedback, and recency. |
| FR-07 | Generate grounded explanations | Bedrock receives only permitted retrieved context and output includes record citations. |
| FR-08 | Handle uncertainty | A result below confidence threshold returns the approved no-answer response and no invented expert. |
| FR-09 | Gather retrieval feedback | One feedback record per user/solution/query context is stored and auditable. |
| FR-10 | Audit sensitive actions | Authentication, content lifecycle, review, visibility, contact reveal/action, and admin activity are logged. |

## 7. Non-functional requirements

- Accessibility: keyboard-operable controls, visible focus, semantic structure, accessible names and status announcements.
- Security: controls in `SECURITY.md`; never embed personal contact data in vectors or pass disallowed content to Bedrock.
- Reliability: explicit loading, empty, error, success, disabled, and permission-denied states; retryable network failures.
- Performance: page size and query budgets are set in Phase 1 baselines; pagination defaults are in API contract.
- Observability: structured API errors, audit records, non-secret operational logs, and correlation IDs.
- Maintainability: one monorepo, single frontend, single backend, documented contracts, Alembic migrations, and ADR-gated change.

## 8. Data and AI boundaries

PostgreSQL is authoritative for employee identity, contact data, ownership, roles, team/department, verification, and authorization. Bedrock creates embeddings and grounded summaries only. It must not generate or infer structured employee/permission facts.

## 9. Delivery phases and acceptance criteria

| Phase | Outcome | Exit criteria |
|---|---|---|
| 0 | Requirements/design lock | Required documents, diagrams, contracts and skeleton exist; stakeholders approve unresolved decisions. |
| 1 | Foundation | `docker compose up --build` starts web, API and pgvector; migrations, health check, env validation, seed skeleton and CI exist. |
| 2 | Authentication | Login/logout/current user, protected routes/endpoints and role tests work. |
| 3 | Knowledge repository | Authorized authoring, drafts, details, profile and reviewer verification work with tests/states. |
| 4 | UI foundation | Approved tokens/app shell/components/states implemented and accessibility checks pass. |
| 5 | Keyword search | FTS, exact error match, filters, sort, pagination, drawer and tests work without Bedrock. |
| 6 | Bedrock embeddings | Configured Bedrock embedding adapter, hashes, re-embedding and failure states work without fake output. |
| 7 | Hybrid retrieval | Merged/reranked/filter-authorized results pass evaluation cases. |
| 8 | Grounded answers | Citation-bearing, permission-safe summaries and no-answer path pass adapter/evaluation tests. |
| 9 | Interactive UI | Command palette, autosave, responsive/mobile, feedback and all states meet UI specification. |
| 10 | Quality/deployment | Full test suite, EC2/Docker/Nginx/EBS runbook, IAM, backup and deployment validation pass. |

## 10. Assumptions

- Initial people and solutions are fictional seed data; production data requires policy approval.
- Company email and an approved contact action are the default contact fields, pending final policy.
- Both light and dark themes are supported because the user-facing theme choice is unresolved; semantic tokens make either removable by approval.
- Attachments are supplementary evidence, never a substitute for the structured solution record.
