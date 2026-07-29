import { getAccessToken } from "../auth/token";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type AuthenticatedUser = { id: string; email: string; role: "employee" | "reviewer" | "administrator"; is_active: boolean; profile: null };
export type LoginPayload = { email: string; password: string };
type ApiEnvelope<T> = { data: T; meta: Record<string, unknown> };
type ApiErrorEnvelope = { error?: { code?: string; message?: string } };

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_URL}/api/v1${path}`, { ...init, headers });
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ApiErrorEnvelope;
    throw new Error(body.error?.message ?? "The request could not be completed.");
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function login(payload: LoginPayload) {
  const response = await request<ApiEnvelope<{ access_token: string; token_type: "bearer"; expires_in: number; user: AuthenticatedUser }>>("/auth/login", { method: "POST", body: JSON.stringify(payload) });
  return response.data;
}
export async function logout() { await request<void>("/auth/logout", { method: "POST" }); }
export async function fetchCurrentUser() { return (await request<ApiEnvelope<AuthenticatedUser>>("/auth/me")).data; }
export async function fetchApiHealth() { return request<ApiEnvelope<{ service: string; status: string; environment: string; version: string; rag_enabled: boolean }>>("/health/live"); }

export type SearchPayload = {
  query: string;
  filters: { verified_only: boolean; technology_ids?: string[]; department_id?: string | null; team_id?: string | null; visibility?: string | null };
  page: number;
  page_size: number;
  sort: "relevance" | "newest";
  include_summary: boolean;
};

export type SearchResult = {
  challenge_id: string;
  solution_id: string;
  title: string;
  problem_excerpt: string;
  root_cause_excerpt: string;
  resolution_steps: string[];
  exact_error_message: string | null;
  status?: string;
  visibility?: string;
  solved_at?: string | null;
  updated_at: string;
  technologies: string[];
  solver: {
    user_id: string;
    display_name: string;
    job_title: string;
    team?: string | null;
    department?: string | null;
    avatar_key?: string | null;
    initials?: string | null;
    contact_email?: string | null;
    contact_handle?: string | null;
  };
  match_reasons: string[];
  score: number;
};

export type SearchResponse = {
  query_id: string;
  results: SearchResult[];
  summary: string | null;
  summary_citations: string[];
  summary_error?: string | null;
  confidence: number | null;
  no_answer: boolean;
  service_status: {
    keyword_search: "available";
    semantic_search: "available" | "not_available";
    grounded_summary: "not_requested" | "available" | "not_generated" | "not_run_no_answer" | "unavailable" | "invalid_response";
  };
};

export async function searchSolutions(payload: SearchPayload) {
  return request<ApiEnvelope<SearchResponse> & { meta: { page: number; page_size: number; total: number; has_next: boolean } }>("/search", { method: "POST", body: JSON.stringify(payload) });
}

export type EmployeeProfile = {
  user_id: string;
  display_name: string;
  job_title: string;
  team: string;
  department: string;
  department_id: string;
  team_id: string;
  contact_email: string;
  contact_handle: string | null;
  skills: string[];
  technologies: string[];
  avatar_key: string | null;
  initials: string;
  bio: string | null;
  verified_solutions: {
    challenge_id: string;
    solution_id: string;
    title: string;
    status: string;
    visibility: string;
    solved_at: string | null;
    updated_at: string;
    technologies: string[];
  }[];
  contribution_count: number;
  helpful_contribution_count: number | null;
};
export async function getEmployeeProfile(userId: string) {
  return (await request<ApiEnvelope<EmployeeProfile>>(userId === "me" ? "/profiles/me" : `/profiles/${userId}`)).data;
}
export type EmployeeProfileUpdate = {
  display_name?: string;
  job_title?: string;
  contact_email?: string;
  bio?: string | null;
  contact_handle?: string | null;
  skills?: string[];
};
export async function updateMyProfile(payload: EmployeeProfileUpdate) {
  return (await request<ApiEnvelope<EmployeeProfile>>("/profiles/me", { method: "PATCH", body: JSON.stringify(payload) })).data;
}

export type EmployeeDirectoryItem = Pick<EmployeeProfile, "user_id" | "display_name" | "job_title" | "team" | "department" | "contact_email" | "contact_handle" | "skills" | "avatar_key" | "initials">;
export async function listEmployeeProfiles(query = "") {
  const suffix = query.trim() ? `?query=${encodeURIComponent(query.trim())}` : "";
  return request<ApiEnvelope<EmployeeDirectoryItem[]> & { meta: { total: number } }>(`/profiles${suffix}`);
}

export type ChallengeSummary = { id: string; title: string; status: string; visibility: string; owner_user_id: string; updated_at: string };
export type ChallengeDetail = ChallengeSummary & {
  solution_id: string;
  problem_description: string;
  symptoms: string;
  exact_error_message: string | null;
  environment: string | null;
  technology_ids: string[];
  technologies: string[];
  attachment_count: number;
  attachments: { id: string; original_filename: string; content_type: string; size_bytes: number; status: string }[];
  solution: { root_cause: string; resolution_steps: string[]; code_snippets: string[]; prevention_notes: string | null; solved_at: string | null };
  review_history: { id: string; reviewer_user_id: string; reviewer_name: string; decision: string; notes: string | null; visibility_after: string | null; created_at: string }[];
  verified_by_user_id: string | null;
  verified_by_name: string | null;
  last_verified_at: string | null;
  related_solutions: { challenge_id: string; title: string; updated_at: string; technologies: string[] }[];
  can_edit: boolean;
  feedback: {
    helpful: number;
    not_helpful: number;
    resolved_my_issue: number;
    current_user_feedback: { id: string; solution_id: string; value: "helpful" | "not_helpful" | "resolved_my_issue"; comment: string | null; updated_at: string } | null;
  };
};
export type Technology = { id: string; name: string; slug: string; category: string | null };
export async function listChallenges(status = "verified") { return request<ApiEnvelope<ChallengeSummary[]> & { meta: { total: number } }>(`/challenges?status=${status}&page_size=10`); }
export async function getChallenge(id: string) { return (await request<ApiEnvelope<ChallengeDetail>>(`/challenges/${id}`)).data; }
export async function listTechnologies() { return (await request<ApiEnvelope<Technology[]>>("/technologies")).data; }
export async function createChallenge(payload: Record<string, unknown>) { return (await request<ApiEnvelope<ChallengeDetail>>("/challenges", { method: "POST", body: JSON.stringify(payload) })).data; }
export async function updateChallenge(id: string, payload: Record<string, unknown>) { return (await request<ApiEnvelope<ChallengeDetail>>(`/challenges/${id}`, { method: "PATCH", body: JSON.stringify(payload) })).data; }
export async function submitChallenge(id: string) { return (await request<ApiEnvelope<ChallengeDetail>>(`/challenges/${id}/submit`, { method: "POST" })).data; }
export async function uploadChallengeAttachment(id: string, file: File) {
  const body = new FormData();
  body.append("file", file);
  return (await request<ApiEnvelope<{ id: string; original_filename: string; content_type: string; size_bytes: number; status: string }>>(`/challenges/${id}/attachments`, { method: "POST", body })).data;
}
export async function reviewQueue() { return (await request<ApiEnvelope<ChallengeSummary[]>>("/reviews/queue")).data; }
export async function reviewSolution(payload: { solution_id: string; decision: string; notes?: string }) { return request<ApiEnvelope<{ id: string; embedding_status?: string }>>("/reviews", { method: "POST", body: JSON.stringify(payload) }); }
export async function recordFeedback(payload: { solution_id: string; value: "helpful" | "not_helpful" | "resolved_my_issue"; comment?: string }) {
  return (await request<ApiEnvelope<{ id: string; solution_id: string; value: string; comment: string | null; updated_at: string }>>("/feedback", { method: "POST", body: JSON.stringify(payload) })).data;
}
