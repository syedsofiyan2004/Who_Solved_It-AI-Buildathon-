import { getAccessToken } from "../auth/token";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type AuthenticatedUser = { id: string; email: string; role: "employee" | "reviewer" | "administrator"; is_active: boolean; profile: null };
export type LoginPayload = { email: string; password: string };
type ApiEnvelope<T> = { data: T; meta: Record<string, unknown> };
type ApiErrorEnvelope = { error?: { code?: string; message?: string } };

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
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
  filters: { verified_only: boolean };
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
  updated_at: string;
  technologies: string[];
  solver: { user_id: string; display_name: string; job_title: string };
  match_reasons: string[];
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

export type ChallengeSummary = { id: string; title: string; status: string; visibility: string; owner_user_id: string; updated_at: string };
export type ChallengeDetail = ChallengeSummary & { problem_description: string; symptoms: string; exact_error_message: string | null; environment: string | null; technology_ids: string[]; solution: { root_cause: string; resolution_steps: string[]; code_snippets: string[]; prevention_notes: string | null; solved_at: string | null } };
export type Technology = { id: string; name: string; slug: string; category: string | null };
export async function listChallenges(status = "verified") { return request<ApiEnvelope<ChallengeSummary[]> & { meta: { total: number } }>(`/challenges?status=${status}&page_size=10`); }
export async function getChallenge(id: string) { return (await request<ApiEnvelope<ChallengeDetail>>(`/challenges/${id}`)).data; }
export async function listTechnologies() { return (await request<ApiEnvelope<Technology[]>>("/technologies")).data; }
export async function createChallenge(payload: Record<string, unknown>) { return (await request<ApiEnvelope<ChallengeDetail>>("/challenges", { method: "POST", body: JSON.stringify(payload) })).data; }
export async function submitChallenge(id: string) { return (await request<ApiEnvelope<ChallengeDetail>>(`/challenges/${id}/submit`, { method: "POST" })).data; }
export async function reviewQueue() { return (await request<ApiEnvelope<ChallengeSummary[]>>("/reviews/queue")).data; }
export async function reviewSolution(payload: { solution_id: string; decision: string; notes?: string }) { return request<ApiEnvelope<{ id: string }>>("/reviews", { method: "POST", body: JSON.stringify(payload) }); }
