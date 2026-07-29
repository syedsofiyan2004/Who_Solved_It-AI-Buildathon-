# Showcase Data Provenance

## Purpose

The local buildathon corpus demonstrates search, RAG, permissions, reviewer workflow, and expert discovery without using private company material or copyrighted Q&A content.

## Employee directory

The employee names, high-level departments, and role groupings were supplied for this demonstration. Showcase email addresses are generated deterministically using the temporary convention:

```text
first.last@minfytech.com
```

These addresses and internal handles are demonstration values and must be reviewed before any real organizational use.

## Technical knowledge corpus

The technical incidents and resolutions are original synthetic records based on common engineering failure patterns across:

- Cloud migration and networking
- AWS, Azure, and Google Cloud
- Terraform and configuration automation
- Docker and Kubernetes
- CI/CD and platform engineering
- SRE, monitoring, and incident response
- Software engineering and APIs
- Data engineering and analytics
- AI, MLOps, RAG, and vector search

No record is copied from Stack Overflow, private messages, customer tickets, or internal company systems.

The latest complex-incident expansion was informed by public vendor guidance on failure categories such as Kubernetes pod failure states, AWS IAM/OIDC authorization, Prometheus label cardinality, and NVIDIA GPU memory troubleshooting. The seeded records remain original synthetic examples and do not copy external runbooks.

## Generated scale

`apps/api/scripts/seed_dev.py` currently produces:

- 43 employee profiles
- 54 technology records
- 85 incident blueprints
- 7 deployment environments per blueprint
- 595 challenge/solution records
- deterministic review history and usefulness feedback

The script is idempotent: running it again updates the same stable showcase entities rather than creating uncontrolled duplicates.

## Safety and limitations

- The corpus is suitable for demonstrations and retrieval evaluation, not production operational guidance.
- Commands, regions, and identifiers are intentionally generic.
- No credentials, customer identifiers, private IP addresses, or production secrets are included.
- Human review is required before replacing the synthetic corpus with real organizational knowledge.
