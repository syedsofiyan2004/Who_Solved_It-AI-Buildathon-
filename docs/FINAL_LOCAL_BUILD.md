# Final Local Build

## Decision

The buildathon application is intentionally local-only. It uses Docker Compose for the web application, API, PostgreSQL, and pgvector. No AWS deployment resources are required.

## Product workflow

1. Sign in as an employee, reviewer, or administrator.
2. Search verified technical knowledge using a natural-language issue or exact error.
3. Open a solution in the connected preview workspace.
4. Open the solver profile without losing query, filters, pagination, or scroll context.
5. Create and autosave a draft solution.
6. Submit it for review.
7. Approve, request changes, or reject it through the reviewer queue.
8. Search the approved record and contact its solver.
9. Submit usefulness feedback.

## AI configuration

The local product supports three modes:

- `AI_PROVIDER=disabled`: PostgreSQL keyword and exact-error search only.
- `AI_PROVIDER=nvidia`: NVIDIA embeddings plus NVIDIA-hosted grounded chat summaries.
- `AI_PROVIDER=bedrock`: retained compatibility for an approved future environment, but not required for the buildathon.

Default NVIDIA models:

```text
Embedding: nvidia/nemotron-3-embed-1b
Chat: openai/gpt-oss-120b
```

## Finalization boundary

The following are intentionally outside the zero-cost local showcase:

- AWS deployment
- Company SSO
- Slack/Teams/Jira synchronization
- Real customer or employee knowledge ingestion
- Attachment malware-scanning service
- Production email delivery

These exclusions do not prevent the complete local review workflow.
