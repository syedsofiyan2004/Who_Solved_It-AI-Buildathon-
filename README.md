# Technical Knowledge and Expert Discovery Platform

Internal MVP for recording solved technical problems, discovering verified prior solutions, and contacting approved internal experts.

## Phase status

Phases 0-8 are implemented. Phase 9 remediation is in progress; Phase 10 deployment work has not started. Read `docs/IMPLEMENTATION_STATUS.md` before beginning work.

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

For local Bedrock access, authenticate with the AWS CLI and select the optional read-only profile override. The API-only Compose service can also receive `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and an optional `AWS_SESSION_TOKEN` from an ignored local `.env`; it never forwards them to the frontend and they must never be committed, placed in `.env.example`, or included in an export.

```bash
docker compose -f docker-compose.yml -f docker-compose.aws-profile.example.yml up --build
```

After changing local AWS credentials in `.env`, recreate the API service so it receives the updated values:

```bash
docker compose up -d --force-recreate api
```

Create a shareable source archive only with the safe packaging script. It excludes local `.env`, dependencies, build output, uploads, virtual environments, caches, and generated artifacts.

```bash
python apps/api/scripts/package_source.py --output artifacts/knowledge-platform-source.zip
```

Then check:

- Web: `http://localhost:5173`
- API liveness: `http://localhost:8000/api/v1/health/live`
- API readiness: `http://localhost:8000/api/v1/health/ready`
