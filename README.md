# Technical Knowledge and Expert Discovery Platform

Internal MVP for recording solved technical problems, discovering verified prior solutions, and contacting approved internal experts.

## Phase status

Phase 0 is approved. Phase 1 adds the runnable local foundation only: web, API, PostgreSQL with pgvector, migrations, health checks, seed skeleton, and CI. Product features begin in later phases. Read `docs/IMPLEMENTATION_STATUS.md` before beginning work.

## Locked architecture

- React + TypeScript + Vite frontend
- FastAPI + SQLAlchemy backend
- PostgreSQL with pgvector in Docker
- Amazon Bedrock for embeddings and grounded summaries
- Docker Compose locally and on one EC2 instance, with Nginx

No architecture change is permitted without an approved ADR in `docs/decisions/`.

## Structure

```text
apps/web/                 React application
apps/api/                 FastAPI application
infrastructure/docker/    Docker assets
infrastructure/nginx/     Reverse proxy assets (Phase 10)
infrastructure/deployment/ EC2 deployment assets (Phase 10)
docs/                     Approved design and delivery records
```

## Local foundation

Copy `.env.example` to `.env` when local overrides are needed. The default Compose values are development-only and do not enable RAG.

```bash
docker compose up --build
```

Then check:

- Web: `http://localhost:5173`
- API liveness: `http://localhost:8000/api/v1/health/live`
- API readiness: `http://localhost:8000/api/v1/health/ready`
