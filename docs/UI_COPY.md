# Approved Static UI Copy

All static visible UI strings must use these IDs. Dynamic values, API error details, and AI-generated search summaries are exceptions only where `UI_SPEC.md` permits them. Do not add marketing copy or placeholder prose without updating this file and obtaining normal review.

## Navigation and global actions

| ID | Text |
|---|---|
| `nav.dashboard` | Home |
| `nav.search` | Search solutions |
| `nav.submit` | Log a solved problem |
| `nav.contributions` | My contributions |
| `nav.drafts` | Drafts |
| `nav.reviews` | Reviews |
| `nav.people` | People |
| `nav.profile` | My profile |
| `nav.settings` | Administration |
| `action.search` | Search |
| `action.open_search` | Search past solutions |
| `action.close` | Close |
| `action.cancel` | Cancel |
| `action.back` | Back |
| `action.next` | Continue |
| `action.save_draft` | Save as draft |
| `action.submit_review` | Submit for review |
| `action.retry` | Try again |
| `action.clear_filters` | Clear filters |
| `action.view_solution` | View solution |
| `action.preview_solution` | Preview |
| `action.open_full_solution` | Open full solution |
| `action.view_profile` | View profile |
| `action.view_solver_panel` | View solver |
| `action.open_full_profile` | Open full profile |
| `action.contact_solver` | Contact the solver |
| `action.edit_solution` | Edit solution |
| `action.copy_code` | Copy code |
| `action.copied` | Copied |
| `action.sign_out` | Sign out |
| `action.mark_helpful` | Helpful |
| `action.mark_not_helpful` | Not helpful |
| `action.load_more` | Load more |

## Phase 4 shell and system states

| ID | Text |
|---|---|
| `shell.collapse_navigation` | Collapse navigation |
| `shell.expand_navigation` | Expand navigation |
| `shell.toggle_theme` | Toggle theme |
| `shell.open_user_menu` | Open user menu |
| `shell.primary_navigation` | Primary navigation |
| `shell.mobile_navigation` | Mobile navigation |
| `shell.workspace_group` | Workspace |
| `shell.knowledge_group` | Knowledge |
| `shell.collaboration_group` | Collaboration |
| `shell.admin_group` | Administration |
| `shell.signed_in_as` | Signed in as |
| `command.title` | Search and commands |
| `command.hint` | Type to search pages and actions |
| `command.no_results` | No matching commands |
| `command.shortcut` | Ctrl K |
| `page.not_found_title` | This page is not available |
| `page.not_found_body` | Check the address or return to the dashboard. |
| `page.admin_title` | Administration |
| `page.admin_body` | Administration tools are available to administrators only. |
| `page.solution_title` | Solution details |
| `page.solution_body` | Open a solution from search or an approved link. |
| `page.authoring_body` | Create and edit solution drafts in the authoring workflow. |
| `page.reviews_body` | Review submitted solutions that are available to you. |

## Phase 5 keyword search

| ID | Text |
|---|---|
| `search.sort` | Sort results |
| `search.sort_relevance` | Relevance |
| `search.sort_newest` | Most recently updated |
| `search.keyword_available` | Keyword and exact-error search is active. |
| `search.summary_unavailable` | Grounded summaries will be available after semantic retrieval is configured. |
| `search.summary_available` | Grounded summaries are available for reliable matches. |
| `search.generate_summary` | Generate grounded summary |
| `search.sources` | Sources |
| `search.applied_query` | Results for |
| `search.verified_results` | Showing verified solutions |
| `search.keyword_match` | Keyword match |
| `search.clear` | Clear search |
| `search.previous_page` | Previous page |
| `search.next_page` | Next page |

## Authentication and dashboard

| ID | Text |
|---|---|
| `login.title` | Sign in to the knowledge platform |
| `login.statement` | Find the solution your company already has. |
| `login.email` | Work email |
| `login.password` | Password |
| `login.submit` | Sign in |
| `login.invalid` | We could not sign you in with those details. |
| `login.submitting` | Signing in |
| `login.description` | Search verified technical fixes, understand what worked, and reach the colleague who solved it. |
| `login.internal_only` | Approved internal access only |
| `login.email_invalid` | Enter a valid work email address. |
| `login.password_invalid` | Enter a password between 8 and 128 characters. |
| `dashboard.title` | What are you blocked on? |
| `dashboard.search_hint` | Describe the problem, error message, technology, or environment. |
| `dashboard.log_prompt` | Solved something worth sharing? |
| `dashboard.log_action` | Log a solved problem |
| `dashboard.recent` | Recent verified solutions |
| `dashboard.drafts` | Your drafts |
| `dashboard.reviews` | Awaiting your review |
| `dashboard.continue` | Continue where you left off |
| `dashboard.empty` | No verified solutions are available to you yet. |

## Phase 1 foundation shell

| ID | Text |
|---|---|
| `app.name` | Technical Knowledge Platform |
| `foundation.phase_label` | Phase 1 foundation |
| `foundation.local_stack` | Local stack |
| `foundation.status_eyebrow` | Project foundation |
| `foundation.title` | Search past solutions |
| `foundation.description` | The approved stack is starting here: React, FastAPI, PostgreSQL with pgvector, and explicit service health checks. |
| `foundation.web_label` | Web |
| `foundation.web_ready` | Frontend is running. |
| `foundation.api_label` | API |
| `foundation.checking_api` | Checking API health. |
| `foundation.api_ready` | API health check passed. |
| `foundation.api_unavailable` | API health check failed. |
| `foundation.signed_in` | Signed in |
| `foundation.dashboard_notice` | Authentication is active. Solution discovery begins in a later phase. |

## Search and result content

| ID | Text |
|---|---|
| `search.title` | Search past solutions |
| `search.placeholder` | Paste an error message or describe the roadblock |
| `search.filters` | Filters |
| `search.verified_only` | Verified only |
| `search.technology` | Technology |
| `search.department` | Department |
| `search.team` | Team |
| `search.result_count` | Matching solutions |
| `search.summary` | Summary of matching solutions |
| `search.applied_query` | Results for |
| `search.verified_results` | Showing verified solutions |
| `search.match_reasons` | The server returns up to three signal-derived reasons, such as `Exact error message contains the query`; the interface renders them verbatim. |
| `state.coming_soon` | This area is not available in your current workspace. |
| `search.exact_error` | Exact error match |
| `search.no_answer_title` | No reliable match was found |
| `search.no_answer_body` | Add the exact error message, affected technology or environment to improve your search. |
| `search.empty_title` | Start with the problem you are trying to solve |
| `search.empty_body` | Search uses past solutions that you are allowed to access. |
| `search.error_title` | Search is unavailable |
| `search.error_body` | Check your connection and try again. |
| `search.bedrock_unavailable` | Semantic search and summaries are temporarily unavailable. Keyword matches may still be available. |
| `search.preview` | Preview solution |
| `search.matched_passage` | Matched passage |
| `search.match_reasons` | Match reasons |
| `search.match_strength` | Match strength |
| `search.strength_strong` | Strong |
| `search.strength_medium` | Medium |
| `search.strength_low` | Low |
| `search.sources` | Sources |
| `search.result_unverified` | Not yet verified |
| `search.result_verified` | Verified |

## Submission and review

| ID | Text |
|---|---|
| `submit.title` | Log a solved problem |
| `submit.step_problem` | Problem |
| `submit.step_cause` | Root cause |
| `submit.step_resolution` | Resolution |
| `submit.step_review` | Review |
| `submit.title_label` | Clear problem title |
| `submit.problem_label` | What happened? |
| `submit.symptoms_label` | Symptoms |
| `submit.error_label` | Exact error message |
| `submit.environment_label` | Environment |
| `submit.technology_label` | Technologies |
| `submit.root_cause_label` | Root cause |
| `submit.steps_label` | Resolution steps |
| `submit.code_label` | Code or command evidence |
| `submit.visibility_label` | Who can view this solution? |
| `submit.attachments_label` | Attachments |
| `submit.draft_saved` | Draft saved |
| `submit.submit_success` | Your solution was submitted for review. |
| `submit.validation_required` | Complete the required fields before continuing. |
| `submit.duplicate_title` | Similar past solutions were found |
| `submit.duplicate_body` | Review these records before submitting a duplicate solution. |
| `review.title` | Review submitted solutions |
| `review.filter` | Filter submissions |
| `review.sort` | Sort submissions |
| `review.sort_oldest` | Oldest first |
| `review.sort_newest` | Newest first |
| `review.no_filtered_results` | No submissions match this filter. |
| `review.verify` | Verify solution |
| `review.request_changes` | Request changes |
| `review.reject` | Reject submission |
| `review.notes` | Review notes |
| `review.empty` | There are no solutions waiting for review. |
| `review.success` | Review decision recorded. |

## Details, profile, feedback, and states

| ID | Text |
|---|---|
| `detail.problem` | Problem |
| `detail.symptoms` | Symptoms |
| `detail.environment` | Technical environment |
| `detail.exact_error` | Exact error |
| `detail.root_cause` | Root cause |
| `detail.resolution` | Resolution |
| `detail.code` | Code and commands |
| `detail.copy_code` | Copy code |
| `detail.copied` | Copied |
| `detail.attachments` | Attachments |
| `detail.review_timeline` | Review timeline |
| `detail.related` | Related solutions |
| `detail.technologies` | Technologies |
| `detail.verified` | Verified |
| `detail.unverified` | Unverified |
| `detail.solved_by` | Solved by |
| `detail.verified_by` | Verified by |
| `detail.visibility` | Visibility |
| `detail.feedback_prompt` | Did this solution help? |
| `detail.feedback_comment` | Optional comment |
| `detail.feedback_thanks` | Thanks for the feedback. |
| `profile.title` | Employee profile |
| `profile.contact` | Approved contact |
| `profile.team` | Team |
| `profile.department` | Department |
| `profile.skills` | Skills |
| `profile.technologies` | Technologies |
| `profile.solutions` | Verified solutions |
| `profile.relevant_solutions` | Relevant solutions |
| `profile.contributions` | Contributions |
| `profile.helpful` | Helpful contributions |
| `profile.empty_skills` | No skills are listed yet. |
| `profile.empty_solutions` | No verified solutions are available to you for this employee yet. |
| `profile.empty_tags` | No technologies are associated with visible verified solutions yet. |
| `state.loading` | Loading |
| `state.saving` | Saving |
| `state.submitting` | Submitting |
| `state.retry` | Try again |
| `state.permission_title` | You do not have access to this content |
| `state.permission_body` | If you need access, contact the solution owner or an administrator. |
| `state.not_found_title` | This solution is not available |
| `state.not_found_body` | It may have been removed or you may not have access to it. |
| `state.network_title` | We could not complete that request |
| `state.network_body` | Check your connection and try again. |
| `state.upload_type` | This file type is not allowed. |
| `state.upload_size` | This file is larger than the allowed size. |
| `state.session_expired` | Your session has expired. Sign in again to continue. |
| `mobile.menu` | Open navigation |
| `mobile.close_menu` | Close navigation |

## Labels for visibility and status

| ID | Text |
|---|---|
| `visibility.company` | Company |
| `visibility.department` | Department |
| `visibility.team` | Team |
| `visibility.restricted` | Restricted |
| `visibility.administrator` | Administrators only |
| `status.draft` | Draft |
| `status.submitted` | Submitted for review |
| `status.changes_requested` | Changes requested |
| `status.verified` | Verified |
| `status.rejected` | Rejected |
