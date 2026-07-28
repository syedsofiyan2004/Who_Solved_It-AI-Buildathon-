# UI Specification

## 1. Design intent and guardrails

The interface is a compact internal SaaS application: Linear informs shell/navigation density, Glean informs search/results/expert discovery, and Notion informs authoring/reading/code. These are interaction references, not templates. The UI avoids decorative gradients, glass, marketing copy, default shadcn pages, arbitrary charts/metrics, and repeated generic cards. Search is the dominant global action. All static text is referenced by ID from `UI_COPY.md`.

## 2. Design tokens and layout rules

| Token area | Rule |
|---|---|
| Typography | Inter/system sans UI: 12, 13, 14, 16, 20, 24, 30px; 14px default body; 20px page title; 24px solution title; code uses 13px monospace/1.55 line height. |
| Spacing | 4px base: 4, 8, 12, 16, 20, 24, 32, 40, 48, 64. Prefer 16/24 between related groups and 32 between sections. |
| Radius | 4px controls, 6px cards/drawers, 8px dialogs only; no pill containers except chips/badges. |
| Borders/shadows | `border-subtle` 1px for surfaces; `border-strong` for focus/active; one `shadow-overlay` for drawers/dialogs, otherwise no decorative shadows. |
| Colour tokens | Use semantic Tailwind tokens only: `background`, `foreground`, `surface`, `surface-foreground`, `card`, `card-foreground`, `muted`, `muted-foreground`, `border`, `border-strong`, `input`, `primary`, `primary-foreground`, `accent`, `accent-foreground`, `success`, `warning`, `destructive`/`danger`, `info`, `code`, and `code-foreground`. No hardcoded white/black/gray scale classes in ordinary UI components. |
| Themes | Light: canvas/surface contrast and dark text. Dark: lifted surfaces, muted borders, WCAG AA contrast. Semantic tokens—not component-specific colours—switch themes. |
| Shell | Desktop sidebar 240px expanded / 64px collapsed; header 56px; main padding 24px; mobile top bar 56px and sheet navigation. |
| Content widths | Search results 1120px max; solution reading 860px; authoring 760px; dashboard 1120px. Use responsive gutters 16px mobile/24px desktop. |
| Controls | Inputs/buttons 36px compact or 40px default; touch targets at least 44px on mobile. Tables use 40px rows, 12px headers, fixed action column. |
| Icons/motion | Lucide 16px inline, 18px controls, 20px nav; 120ms hover, 160ms dropdown/tooltip, 200ms drawer/dialog, ease-out; respect reduced motion. |
| Code | `code-bg`, 1px border, 8px padding mobile/12px desktop, horizontal scroll, line wrapping toggle, Copy action. |

## 3. Route map

| Route | Page | Access |
|---|---|---|
| `/login` | Login | Public; redirects authenticated user to dashboard |
| `/` | Dashboard | Authenticated |
| `/search` | Search results and master-detail preview workspace | Authenticated; `q`, `technology`, `team`, `verification`, `sort`, `page`, `solution`, and `solver` are URL-driven where supported |
| `/drafts` | Draft list | Authenticated; shows accessible draft records through the existing challenge listing contract |
| `/solutions/:challengeId` | Complete solution details | Authorized viewer |
| `/solutions/:challengeId/preview` | Deep-linkable drawer state | Authorized viewer; normal UX opens drawer over search |
| `/solutions/new` | Multi-step submission | Employee+ |
| `/solutions/:challengeId/edit` | Edit owned draft/allowed revision | Owner/reviewer/admin policy |
| `/people/:userId` | Employee profile | Authorized viewer |
| `/reviews` | Reviewer panel | Reviewer/admin |
| `/admin/users` | User administration | Administrator |
| `/forbidden` | Permission denied | Authenticated |
| `*` | Not found | Public/authenticated as appropriate |

## 4. Component inventory

**Shell:** `AppShell`, `ProductSidebar`, `MobileNavigation`, `TopBar`, `CommandPalette`, `ThemeToggle`, `UserMenu`.

**Search:** `GlobalSearch`, `SearchFilters`, `AppliedFilterChip`, `SearchSummary`, `ResultList`, `SearchResultCard`, `MatchStrength`, `MatchReasonList`, `SolutionPreviewPanel`, `SolverProfilePanel`, `DetailSheet`, `CitationList`, `NoAnswerPanel`.

**Knowledge:** `SolutionReader`, `SolutionMetadata`, `VerificationBadge`, `VisibilityBadge`, `CodeBlock`, `ResolutionStepList`, `AttachmentList`, `SolverMiniProfile`, `FeedbackControl`, `ReviewTimeline`.

**Authoring/review:** `SubmissionStepper`, `ProblemStep`, `CauseStep`, `ResolutionStep`, `SubmissionReview`, `TechnologyCombobox`, `VisibilitySelect`, `AttachmentUpload`, `AutosaveIndicator`, `DuplicateSuggestion`, `ReviewQueue`, `ReviewDecisionDialog`.

**System:** `PageHeader`, `EmptyState`, `ErrorState`, `PermissionDeniedState`, `LoadingSkeleton`, `InlineValidation`, `ConfirmDialog`, `Toast`, `Pagination`, `StatusBadge`.

Use customized shadcn/Radix primitives (Button, Input, Textarea, Select, Dialog, Drawer, DropdownMenu, Tabs, Tooltip, Sheet, Toast, Table) under shared wrappers. Pages do not style primitive instances ad hoc.

## 5. Common interaction/state standard

Every screen uses: skeletons preserving final geometry while loading; a purposeful empty state; retryable network-error state; success toast/inline confirmation; visible hover/active states only for interactive elements; 2px semantic focus ring; disabled controls with reason/tooltip where useful; server validation next to field plus summary; and a `PermissionDeniedState` on 403/authorized-route policy failure. Keyboard focus follows visual order; dialogs/drawers trap focus, restore trigger focus, close on Escape unless destructive confirmation is active, and announce outcome with live regions. Motion is opacity/short translation only and disabled for reduced motion.

## 6. Screen specifications

| Screen | Purpose and desktop/mobile structure | Actions and state behaviour | Reused components / copy |
|---|---|---|---|
| Login | Centered 360–400px form on calm canvas; brand/product name, email/password fields. Mobile uses 16px gutters, no side content. | Submit on Enter; focus email first; invalid credentials are generic. Loading disables submit; success redirects; error is inline; authenticated users never see form. | `Input`, `Button`, `InlineValidation`; `login.*`, `state.session_expired`. |
| Dashboard | Desktop shell with page title, prominent search input, lightweight recent verified list and authoring prompt. Mobile stacks search then list. No metric-card grid. | Search Enter opens `/search`; command palette shortcut opens global search. Empty recent state, list skeleton, retry state, authoring success toast. | `AppShell`, `SearchInput`, `SolutionResultCard`, `EmptyState`; `dashboard.*`, `action.open_search`. |
| Global search/command palette | Centered dialog 680px wide; query first, shortcuts/results below. Mobile full-height drawer. | `Ctrl/Cmd+K`, slash when not typing, arrow navigation, Enter select, Escape close. Loading row/skeleton; no-result guidance; unavailable service status. | `CommandPalette`, `SearchInput`; `search.*`, `action.close`. |
| Search results and filters | Master-detail desktop: 248px sticky filter rail, results list, and optional 420px right detail rail. Mobile keeps the result list primary and opens details in a near-full-screen sheet. Query, verification, technology, sort, page, selected solution, and selected solver are URL synchronized. | Filter chips update URL and query; clear/filter keyboard accessible. Skeleton cards; blank query state; no-answer panel; network retry; result cards expose preview/full-solution/contact actions. Opening a solution sets `solution`, opening its solver sets `solver`, browser Back returns through those states without losing the query/filter/page context. | `SearchFilters`, `SearchResultCard`, `SolutionPreviewPanel`, `SolverProfilePanel`, `DetailSheet`, `SearchSummary`, `NoAnswerPanel`; `search.*`. |
| Result preview drawer | Desktop right rail within search workspace; mobile accessible sheet; summary, match reasons, root cause/steps excerpts, solver and source link. | Click Preview/Enter opens; Escape/Close removes the URL detail param. Loading skeleton; missing/denied becomes state panel; contact only when API supplies it. Solver preview opens inside the same workspace rather than forcing a full-page route change. | `SolutionPreviewPanel`, `SolverProfilePanel`, `SolverMiniProfile`, `CitationList`; `search.preview`, `action.open_full_solution`, `action.contact_solver`. |
| Complete solution detail | 860px reading column with sticky compact metadata/solver aside desktop; mobile shows metadata above sections. Structured sections make scanning clear. | Copy code; feedback control; attachment download gated by scan/auth. Detail loading skeleton, unavailable/permission state, feedback success. Long errors/code scroll rather than break layout. | `SolutionReader`, `CodeBlock`, `FeedbackControl`; `detail.*`, `state.*`. |
| Multi-step submission | 760px form with 4-step top indicator; mobile step label/progress only. Steps are Problem, Root cause, Resolution, Review. | Validate only current step plus final submit; Enter does not prematurely submit textareas; autosave after idle and on step navigation; draft recovery prompt; duplicate suggestions are non-blocking; review confirmation. Loading/save/submission states; file type/size inline errors; success redirects to detail/status. | `SubmissionStepper`, form controls, `AttachmentUpload`, `DuplicateSuggestion`; `submit.*`, actions. |
| Employee profile | Header with approved identity/contact fields, skills, and authorized verified solutions. Desktop two columns; mobile stacks. | Profile links use standard cards; contact action is absent if unavailable. Loading skeleton, no-solutions state, error retry, permission state. | `SolverPanel`, `ResultList`, `StatusBadge`; `profile.*`, actions. |
| Reviewer panel | Dense table/list with status, owner, technology, submitted time and row actions; 70/30 detail/review split desktop, detail then sticky action footer mobile. | Keyboard table navigation; decision dialog requires notes for reject/change request. Queue empty, loading table, error retry, success optimistic refresh. Own submissions cannot render decision controls. | `ReviewQueue`, `ReviewDecisionDialog`, `SolutionReader`; `review.*`. |
| Loading, empty, error, denied | Shared patterns replace the main content region without changing shell. Mobile uses same hierarchy with full width. | Skeletons never show fabricated content. Empty state has one relevant action; error has retry if safe; 403/404 avoids claiming whether protected data exists. | `LoadingSkeleton`, `EmptyState`, `ErrorState`, `PermissionDeniedState`; `state.*`. |
| Mobile navigation | Top bar: menu, current page title, search trigger; sheet contains navigation, user menu and sign out. | Menu button labels state, closes Escape/overlay, locks background scroll, preserves focus. Active route distinct in text/icon; disabled admin/review links omitted rather than merely disabled. | `MobileNavSheet`, `TopBar`; `mobile.*`, `nav.*`. |

## 7. Accessibility and responsive acceptance

Meet WCAG 2.1 AA contrast/keyboard requirements; use landmarks, headings in order, labels/errors associated with controls, aria-live for save/search/result feedback, and no colour-only status. Validate at 320px, 768px, 1024px, 1440px. Desktop sidebar collapses before content becomes cramped; filter rail becomes sheet below 1024px; reading and authoring columns become full width below 768px. Touch targets remain 44px minimum.

## 8. UI implementation acceptance

Every listed route renders with appropriate role protection; every important screen implements desktop/mobile/loading/empty/error/success/hover/focus/disabled/permission-denied behavior; no static text bypasses `UI_COPY.md`; no console warnings; keyboard and screen-reader smoke tests pass; and components reuse the inventory before a new primitive/pattern is introduced.
