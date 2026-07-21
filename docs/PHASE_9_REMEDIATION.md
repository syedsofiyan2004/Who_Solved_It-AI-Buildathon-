# Phase 9 Remediation Audit

## Audit scope and constraints

The remediation brief, approved design/architecture documents, existing source, migrations, seed data, and tests were reviewed. The 36-page [Internal Technical Knowledge Platform.pdf](D:\Expert Discovery Platform\docs\Internal%20Technical%20Knowledge%20Platform.pdf) is the master plan and was re-read in full on 2026-07-21. `docs/decisions/` has no approved ADR files. The repository has no usable Git metadata, so tracked-file history cannot be verified locally.

## Confirmed defects

| Priority | Defect | Likely files | Root cause | Correction | Required proof |
|---|---|---|---|---|---|
| 0 | Local `.env` contains AWS credential keys | `.env`, `.gitignore`, Compose/config | Local development credentials were supplied directly rather than through a profile/role | Keep `.env` ignored, remove credential forwarding where possible, add safe scanner/startup reporting, document account-owner rotation | Scanner reports no credentials outside ignored local env; no values printed |
| 1 | Technology chips render `{ O I D C }` | `services/search.py` | PostgreSQL array aggregate is coerced with `list()` when driver returns a string | Normalize aggregate values to `list[str]` in both search paths | One/multiple-tech API and UI regression tests |
| 1 | Typed input can differ from applied result query | `SearchPage.tsx` | URL state is used as both editable draft and submitted query context without an explicit applied-result label | Keep draft/applied states distinct and display the applied query | Browser/component test |
| 1 | Weak semantic candidates inflate count and appear unrelated | `services/search.py`, `RAG_DESIGN.md` | Threshold is applied only to top confidence after candidate merge | Apply an eligibility floor per result before totals, pagination, and summary context | Ranking/no-answer evaluation tests |
| 1 | Match reason is overly generic | `services/search.py`, `SearchPage.tsx` | Reasons do not reflect all scoring signals | Return deterministic signal-derived reasons | Search contract/unit tests |
| 2 | Evaluation fixture is structural rather than ranking-executable | `tests/test_rag_evaluation_fixture.py` | Fixture validation does not call retrieval | Add deterministic retrieval evaluation tests/metrics | Recall@5, top-1, no-answer, permissions |
| 3-7 | Profile, authoring, reviewer, feedback, detail, command-palette, and overlay requirements are incomplete | web pages/components, repository API/schema | Phase 9 was started as route foundations only | Implement in remediation order; add API/schema changes only where required | Workflow, accessibility, and authorization tests |

## Incomplete Phase 9 features

Employee-profile API/UI, structured authorized solver/contact serialization, authoring with persistence/autosave/edit, duplicate suggestions, reviewer UI, full solution metadata/timeline/feedback, feedback model/API/UI, command-palette search/keyboard selection, accessible Radix overlays, and responsive design remediation remain incomplete.

## Implementation order

1. Security cleanup and scanning.
2. Search serialization/state/ranking fixes and executable retrieval evaluation.
3. Structured solver and profile features.
4. Search/result-card redesign.
5. Authoring, duplicate suggestions, review, detail/edit, and feedback workflows.
6. Command palette/overlay accessibility and responsive verification.
7. Documentation reconciliation and full validation.

## Acceptance gate

Phase 9 remains **In progress** until every remediation requirement is implemented or explicitly blocked with user approval. Phase 10 deployment work is excluded.

## Blockers requiring user action

- The AWS account owner must deactivate/rotate any AWS credentials that may previously have appeared in an archive or local `.env`; this cannot be safely performed from this workspace.
- Git history is unavailable locally, so prior tracking of any credential exposure cannot be verified. Supply repository history if an audit of prior commits is required.
