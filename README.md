# Minfy Resolve

## Internal Technical Knowledge and Expert Discovery Platform

Minfy Resolve is an internal platform for capturing solved technical problems and helping employees find the verified solution and expert behind a similar issue later.

It is not a generic chatbot, ticketing system, social network, or project-management tool. Its core purpose is to turn solved engineering problems into reusable, searchable, permission-aware knowledge.

## What the platform does

Employees document technical problems they have solved. Other employees can search using natural language, exact errors, affected technology, or environment context and retrieve:

- relevant previous solutions;
- root causes;
- resolution steps;
- exact error evidence;
- verified solution ownership;
- the employee who solved the problem;
- approved company contact details;
- grounded summaries generated only from retrieved records.

The platform connects two questions:

1. “Has someone already solved this technical blocker?”
2. “Who owns the verified fix, and can I contact them?”

## Why this is needed

Engineering teams often solve the same class of problems repeatedly across projects, environments, and customers. Those fixes usually live in scattered places: chat messages, ticket comments, deployment notes, personal memory, and one-off runbooks.

That creates repeated waste:

- engineers rediscover known fixes;
- teams depend on knowing the right person informally;
- exact error messages are hard to search reliably;
- unverified AI answers may look plausible but be wrong;
- ownership and contact details must stay controlled by company systems;
- sensitive or restricted records must not be sent blindly to an AI model.

Minfy Resolve solves this by combining structured technical records, review-based verification, authorization-aware retrieval, and grounded AI summaries.

## Core features

### Structured solution capture

Employees can log a solved problem with:

- problem title;
- technical environment;
- symptoms;
- exact error message;
- root cause;
- resolution steps;
- code or command evidence;
- technologies involved;
- visibility level;
- owner metadata.

Drafts can be saved before they are complete. A solution becomes trusted knowledge only after review.

### Reviewer verification

Reviewers validate submitted solutions before they become verified search results.

Reviewer decisions are stored with:

- reviewer identity;
- decision;
- notes;
- timestamp;
- resulting visibility.

This gives each search result a trust trail instead of treating every draft as authoritative.

### Expert discovery

Every verified solution is connected to the employee who solved it.

Search results and profiles expose structured expert data from PostgreSQL:

- display name;
- job title;
- team;
- department;
- approved work contact;
- skills;
- visible verified contributions.

AI never generates employee identity, ownership, or contact data.

### Editable employee profile

Signed-in users can maintain profile information used for expert discovery:

- display name;
- job title;
- contact handle;
- short bio;
- skills.

This helps colleagues decide whether the solver is the right person to contact.

### Hybrid retrieval

Search is not a simple text lookup. The backend combines:

- PostgreSQL full-text search;
- deterministic exact-error matching;
- pgvector semantic similarity when embeddings are configured;
- technology matching;
- verification status;
- object-level authorization;
- deterministic scoring and pagination.

This allows the system to match both copied error strings and natural-language descriptions of the same issue.

## Why RAG is used

RAG means retrieval-augmented generation. It is needed because this platform must answer using internal verified records, not generic model memory.

A plain language model can:

- invent a plausible fix;
- invent a solver;
- invent contact details;
- miss internal environment context;
- ignore visibility rules;
- return an answer with no source record.

Minfy Resolve avoids that by separating responsibilities:

1. PostgreSQL stores trusted facts: records, owners, reviewers, roles, permissions, and contact details.
2. Retrieval finds the highest-ranked authorized solutions.
3. The model receives only permitted technical context.
4. The API validates generated output and citations.
5. The response links back to original solution records.

The model helps summarize; it does not decide ownership, access, or truth.

## Retrieval pipeline

The approved retrieval flow is:

1. Authenticate the employee.
2. Accept the search query.
3. Extract optional metadata filters.
4. Create the query embedding when an embedding provider is configured.
5. Run pgvector similarity search.
6. Run PostgreSQL full-text search.
7. Match exact error-message fragments.
8. Apply visibility and authorization filters.
9. Merge duplicate candidates by solution ID.
10. Rank results using deterministic scoring.
11. Apply the no-answer threshold.
12. Retrieve employee and ownership data from PostgreSQL.
13. Send only permitted technical solution context to the generation model.
14. Generate a grounded summary when requested.
15. Return citations to original solution records.

## What AI is allowed to do

AI may:

- create embeddings for solution documents and search queries;
- help find semantically similar records;
- summarize retrieved technical solution context;
- explain matching results using citations.

AI must not generate:

- employee names;
- employee emails;
- job titles;
- teams;
- departments;
- contact details;
- solution ownership;
- verification status;
- access permissions.

Those fields always come from PostgreSQL.

## Architecture

| Layer | Technology | Purpose |
|---|---|---|
| Web application | React, TypeScript, Vite | Product interface for employees, reviewers, and administrators |
| API | FastAPI, Pydantic | Auth, repository lifecycle, search, review, profile APIs |
| Data access | SQLAlchemy, Alembic | Models, migrations, transactional access |
| Database | PostgreSQL with pgvector | Structured records, full-text search, vector search |
| AI adapters | Amazon Bedrock design with configurable provider adapters | Embeddings and grounded summaries |
| Local runtime | Docker Compose | PostgreSQL, API, and web services |

The frontend is intentionally not the main design focus. The platform value is in structured knowledge capture, verification, authorization-aware retrieval, expert discovery, and grounded summarization.

## Security and governance

The MVP includes:

- JWT authentication;
- password hashing;
- role-based access control;
- object-level authorization;
- restricted CORS;
- parameterized database access;
- upload file-type and size limits;
- secret detection;
- audit logging;
- permission filtering before model calls;
- no personal contact data in embedding documents;
- no AWS credentials in source code;
- safe source packaging.

## Current local MVP status

Implemented locally:

- authentication;
- employee, reviewer, and administrator roles;
- solution drafts, editing, submission, and review;
- verified solution search;
- exact-error and keyword search;
- semantic retrieval when embeddings are configured;
- grounded summaries when a generation provider is configured;
- employee profiles and profile editing;
- expert discovery;
- feedback on solutions;
- safe source packaging and secret scanning;
- expanded synthetic showcase data.

Current showcase seed generates:

- 43 employee profiles;
- 511 generated technical solution records;
- 427 generated verified solution records.

The local database may contain a higher total count if older records were intentionally preserved.

## Local runtime

The application runs locally through Docker Compose:

```bash
docker compose up --build -d
docker compose exec api python scripts/seed_dev.py
```

Open:

- Web: `http://localhost:5173`
- API docs: `http://localhost:8000/docs`
- API health: `http://localhost:8000/api/v1/health/live`

## Safe source package

Create a shareable archive only with:

```bash
python apps/api/scripts/package_source.py --output artifacts/knowledge-platform-source.zip
python apps/api/scripts/verify_source_package.py --archive artifacts/knowledge-platform-source.zip
```

The package excludes local environment files, Git history, dependencies, build output, uploads, caches, virtual environments, and detected credentials.

## Detailed documentation

More detail is available in:

- `docs/PLATFORM_OVERVIEW.md`
- `docs/ARCHITECTURE.md`
- `docs/RAG_DESIGN.md`
- `docs/API_CONTRACT.md`
- `docs/DATABASE_SCHEMA.md`
- `docs/SECURITY.md`
- `docs/IMPLEMENTATION_STATUS.md`
