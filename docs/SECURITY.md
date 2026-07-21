# Security Design

## 1. Security principles

Authenticate every protected request, authorize every object access server-side, minimize data sent to clients/models, validate untrusted input, log sensitive actions safely, and fail closed when a dependency or policy is unavailable. Privacy/permission correctness outweighs retrieval recall.

## 2. Control matrix

| Area | Required control | Phase implementation checkpoint |
|---|---|---|
| Passwords | Argon2id or bcrypt using vetted library; no plaintext/reversible storage; generic login failures | Phase 2 |
| JWT | Signed short-lived access tokens; issuer/audience/algorithm validation; rotation/revocation design documented before implementation | Phase 2 |
| RBAC | Employee/reviewer/admin dependency checks | Phase 2 |
| Object authorization | Visibility and ownership checks on detail, download, review, feedback, contact and Bedrock context | Phases 2–8 |
| Input | Pydantic/Zod schemas, length/enums/UUID checks, normalized errors, safe pagination | all features |
| Database | SQLAlchemy parameterization; least-privileged application DB user; migrations reviewed | Phase 1 |
| CORS | Exact allowed origins from config; no wildcard with credentials | Phase 1 |
| Rate limiting | Login and search limits from config; 429 with retry guidance | Phases 2/5 |
| Uploads | MIME/signature allow-list, size limit, name sanitization, stored outside public path, scan/status gate | Phase 3 |
| Content safety | Render Markdown/plain text using sanitization; no unsanitized HTML; CSP in Nginx | Phases 3/4/10 |
| Secrets | `.env` ignored in Phase 1; pre-commit/CI secret detection; redact logs | Phase 1 |
| Bedrock | Instance role/profile only; model/region least privilege; no credentials in source | Phases 6/10 |
| Audit | Append-only high-risk events, request IDs, redacted metadata, retention approval | Phases 2–3 |
| Deployment | TLS, security groups, non-root containers, patched base images, EBS backup runbook | Phase 10 |

## 3. Roles and object policy

Employees can access company-visible records and records matching their team/department; they can edit only their own eligible content. Reviewers gain review capability in their explicitly assigned or allowed organization scope and cannot approve their own solution. Administrators access all content for legitimate administration and produce an audit event. `restricted` is limited to owner/contributor/assigned reviewer/administrator; `administrator` to administrators.

Contact details receive the same record visibility check and an additional approved-contact-field policy. API serialization omits fields rather than sending them disabled/hidden to the browser. Admin actions, contact reveal/action, review decisions, visibility changes, and attachment downloads are audited.

## 4. Data classification and model boundary

Credentials, JWTs, password hashes, AWS credentials, raw IP addresses, and detected secrets are never embedded, returned, or logged. Employee details (names, emails, titles, teams, departments, contacts), ownership, verification, roles, and permissions remain structured in PostgreSQL. No personal contact detail appears in embedding documents. Permission filtering happens before candidate context goes to Bedrock.

## 5. Secure error and incident protocol

For an error: reproduce exact command/output, identify failing layer, compare with approved architecture, identify root cause, apply the smallest valid correction, add regression coverage when code exists, re-run related checks, update implementation status, and continue the same phase. Do not replace Bedrock, remove auth, bypass authorization, or fabricate a successful result. Security incidents additionally require credential rotation/containment and stakeholder escalation before resuming affected deployment work.

## 6. Open security decisions

Stakeholder approval is required for JWT storage/refresh strategy, password policy/SSO future path, contact-field policy, retention periods (uploads, audit, query logs), reviewer organization assignment, attachment malware scanning service/process, backup frequency/retention, and production TLS/DNS ownership. These are intentionally not invented in Phase 0.

## 7. Phase 2 MVP decisions

Phase 2 uses Argon2id through `pwdlib` for password hashes. Access tokens are signed HS256 JWTs with a 60-minute default lifetime and validated issuer, audience, algorithm, issue time, not-before time, expiry, subject, and token ID. The browser keeps the token in memory only; there is no refresh token or persistent browser storage. This conservative temporary MVP choice requires a new sign-in after a browser refresh and avoids placing a bearer token in local storage.

`POST /auth/logout` stores only a token ID and expiry in PostgreSQL so an access token is rejected immediately after logout. The authenticated user is loaded from PostgreSQL on every protected request, so disabled or soft-deleted accounts fail closed. Authentication events are audit logged without passwords or tokens. Login throttling is per-process for the single-instance MVP; it must be reviewed if the approved topology changes.

## 8. Phase 3 repository controls

Challenge edits require the owner (or an administrator) and an editable state; updates include an optimistic `updated_at` value. A non-owner receives a safe authorization response, while a record that is not visible returns `404` to reduce enumeration. Verified records apply company, department, team, restricted, or administrator visibility before serialization. Until a reviewer-assignment policy is approved, a reviewer can review only another employee's submitted record in the reviewer's own team or department; administrators retain audited override authority.

Attachments accept only configured MIME types, enforce the configured size ceiling, sanitize the filename, validate PDF magic bytes or UTF-8 text content, and store evidence outside the public web path. Every accepted upload is `pending_scan`, so it cannot be downloaded until a future approved scanner marks it available. Uploads and allowed downloads are audit events. This fail-closed scan gate is intentional; no attachment is treated as clean merely because it was uploaded.

## 9. Phase 8 grounded-generation controls

Generation is available only after authenticated retrieval has applied object authorization and the confidence gate. The adapter receives a reconstructed technical document for at most three permitted records, never API result solver fields or employee/contact/permission metadata. Query and context content are secret-scanned before invocation. The Bedrock response must be JSON with only a summary and allow-listed source UUID citations; malformed, duplicate, unknown, non-inline, or contact-data output is suppressed. Bedrock dependency/output failures return source records and a safe status without synthetic prose. Search audit metadata records whether a summary was requested and safely used, never the prompt, completion, credentials, or contact data.

## 10. Local AWS credential handling (Phase 9 remediation)

`.env` is ignored and is never committed. `.env.example` contains names and placeholders only. In local development, the API service alone may receive `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and optional `AWS_SESSION_TOKEN` from the ignored local `.env`, so Boto3 can invoke Bedrock. Those values are neither stored in Compose nor passed to the browser service. Boto3 can alternatively use a local CLI profile when the optional `docker-compose.aws-profile.example.yml` override is selected. Deployment uses the EC2 instance role; the profile override must never be used in EC2 deployment.

Run the repository scanner from the repository root with `python apps/api/scripts/scan_secrets.py`; CI runs the same scanner before migrations and tests. It detects AKIA/ASIA access keys, private keys, GitHub tokens, non-placeholder AWS key assignments, token/API-key/JWT-secret assignments, and database URLs with embedded non-placeholder passwords. It checks tracked project content while excluding `.env`, virtual environments, build output, dependency folders, caches, uploads, and Git metadata. Findings report paths only, never matched values. Use `python apps/api/scripts/package_source.py` for any shared source export; it applies the same local/generated-file exclusions. Missing Bedrock configuration is reported by setting name only. Credential rotation/revocation remains the AWS account owner's responsibility and must occur outside source control.
