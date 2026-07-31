import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { AuthProvider, useAuth } from "./auth/AuthProvider";
import { setAccessToken } from "./auth/token";
import { createChallenge, updateMyProfile } from "./services/api";

vi.mock("./services/api", () => ({
  login: vi.fn(async (payload: { email: string }) => {
    const role = payload.email.startsWith("reviewer") || payload.email.startsWith("srikar")
      ? "reviewer"
      : "employee";
    return { access_token: "test-token", user: { id: role === "reviewer" ? "2" : "1", email: payload.email, role, is_active: true, profile: null } };
  }),
  logout: vi.fn(async () => undefined),
  fetchCurrentUser: vi.fn(async () => ({ id: "1", email: "updated.avery@example.test", role: "employee", is_active: true, profile: null })),
  fetchApiHealth: vi.fn(async () => ({ data: { service: "api", status: "ok", environment: "test", version: "0.1.0", rag_enabled: false }, meta: {} })),
  listChallenges: vi.fn(async () => ({ data: [], meta: { total: 0 } })),
  reviewQueue: vi.fn(async () => [{ id: "challenge-1", title: "Container startup failure", status: "submitted", visibility: "company", owner_user_id: "1", updated_at: "2026-07-22T00:00:00Z" }]),
  reviewSolution: vi.fn(async () => ({ data: { id: "review-1", embedding_status: "disabled_until_configured" }, meta: {} })),
  recordFeedback: vi.fn(async () => ({ id: "feedback-1", solution_id: "solution-1", value: "resolved_my_issue", comment: null, updated_at: "2026-07-22T00:00:00Z" })),
  listTechnologies: vi.fn(async () => [{ id: "technology-1", name: "Docker", slug: "docker", category: "containers" }]),
  listEmployeeProfiles: vi.fn(async () => ({ data: [{ user_id: "solver-1", display_name: "Avery Engineer", job_title: "Platform Engineer", team: "Runtime", department: "Platform Engineering", contact_email: "avery@example.test", contact_handle: "@avery", skills: ["Docker troubleshooting"], avatar_key: null, initials: "AE" }], meta: { total: 1 } })),
  getChallenge: vi.fn(async () => ({
    id: "draft-1",
    solution_id: "solution-1",
    title: "Docker import failure",
    status: "submitted",
    visibility: "company",
    owner_user_id: "1",
    updated_at: "2026-07-22T00:00:00Z",
    problem_description: "",
    symptoms: "",
    exact_error_message: null,
    environment: null,
    department_id: null,
    team_id: null,
    technology_ids: ["technology-1"],
    technologies: ["Docker"],
    attachment_count: 0,
    attachments: [],
    solution: { root_cause: "COPY path was wrong.", resolution_steps: ["Fix the Docker COPY path."], code_snippets: [], prevention_notes: null, solved_at: null },
    review_history: [],
    verified_by_user_id: null,
    verified_by_name: null,
    last_verified_at: null,
    related_solutions: [],
    can_edit: true,
    feedback: { helpful: 1, not_helpful: 0, resolved_my_issue: 0, current_user_feedback: null }
  })),
  createChallenge: vi.fn(async () => ({
    id: "draft-1",
    solution_id: "solution-1",
    title: "Docker import failure",
    status: "draft",
    visibility: "company",
    owner_user_id: "1",
    updated_at: "2026-07-22T00:00:00Z",
    problem_description: "",
    symptoms: "",
    exact_error_message: null,
    environment: null,
    department_id: null,
    team_id: null,
    technology_ids: ["technology-1"],
    technologies: ["Docker"],
    attachment_count: 0,
    attachments: [],
    solution: { root_cause: "", resolution_steps: [], code_snippets: [], prevention_notes: null, solved_at: null },
    review_history: [],
    verified_by_user_id: null,
    verified_by_name: null,
    last_verified_at: null,
    related_solutions: [],
    can_edit: true,
    feedback: { helpful: 0, not_helpful: 0, resolved_my_issue: 0, current_user_feedback: null }
  })),
  updateChallenge: vi.fn(async () => ({
    id: "draft-1",
    solution_id: "solution-1",
    title: "Docker import failure",
    status: "draft",
    visibility: "company",
    owner_user_id: "1",
    updated_at: "2026-07-22T00:00:01Z",
    problem_description: "Container cannot import the service package.",
    symptoms: "",
    exact_error_message: null,
    environment: null,
    department_id: null,
    team_id: null,
    technology_ids: ["technology-1"],
    technologies: ["Docker"],
    attachment_count: 0,
    attachments: [],
    solution: { root_cause: "", resolution_steps: [], code_snippets: [], prevention_notes: null, solved_at: null },
    review_history: [],
    verified_by_user_id: null,
    verified_by_name: null,
    last_verified_at: null,
    related_solutions: [],
    can_edit: true,
    feedback: { helpful: 0, not_helpful: 0, resolved_my_issue: 0, current_user_feedback: null }
  })),
  submitChallenge: vi.fn(async () => ({
    id: "draft-1",
    solution_id: "solution-1",
    title: "Docker import failure",
    status: "submitted",
    visibility: "company",
    owner_user_id: "1",
    updated_at: "2026-07-22T00:00:02Z",
    problem_description: "Container cannot import the service package.",
    symptoms: "ModuleNotFoundError",
    exact_error_message: "ModuleNotFoundError",
    environment: "Docker",
    department_id: null,
    team_id: null,
    technology_ids: ["technology-1"],
    technologies: ["Docker"],
    attachment_count: 0,
    attachments: [],
    solution: { root_cause: "COPY path was wrong.", resolution_steps: ["Fix the Docker COPY path."], code_snippets: [], prevention_notes: null, solved_at: null },
    review_history: [],
    verified_by_user_id: null,
    verified_by_name: null,
    last_verified_at: null,
    related_solutions: [],
    can_edit: true,
    feedback: { helpful: 0, not_helpful: 0, resolved_my_issue: 0, current_user_feedback: null }
  })),
  uploadChallengeAttachment: vi.fn(async () => ({ id: "attachment-1", original_filename: "evidence.txt", content_type: "text/plain", size_bytes: 8, status: "pending_scan" })),
  searchSolutions: vi.fn(async () => ({ data: { query_id: "search-1", results: [{ challenge_id: "challenge-1", solution_id: "solution-1", title: "Container startup failure", problem_excerpt: "Container did not start.", root_cause_excerpt: "The image copied files to the wrong path.", resolution_steps: ["Correct the Docker COPY path."], exact_error_message: "ModuleNotFoundError", updated_at: "2026-07-21T00:00:00Z", technologies: ["Docker"], solver: { user_id: "solver-1", display_name: "Avery Engineer", job_title: "Platform Engineer", team: "Runtime", department: "Platform Engineering", initials: "AE", contact_email: "avery@example.test", contact_handle: "@avery" }, match_reasons: ["Semantic match", "Keyword match"], score: 0.82 }], summary: null, summary_citations: [], confidence: 0.72, no_answer: false, service_status: { keyword_search: "available", semantic_search: "available", grounded_summary: "not_requested" } }, meta: { page: 1, page_size: 10, total: 1, has_next: false } })),
  getEmployeeProfile: vi.fn(async () => ({
    user_id: "solver-1",
    display_name: "Avery Engineer",
    job_title: "Platform Engineer",
    team: "Runtime",
    department: "Platform Engineering",
    department_id: "department-1",
    team_id: "team-1",
    contact_email: "avery@example.test",
    contact_handle: "@avery",
    skills: ["Docker troubleshooting", "Incident review"],
    technologies: ["Docker"],
    avatar_key: null,
    initials: "AE",
    bio: "Maintains runtime services.",
    contribution_count: 3,
    helpful_contribution_count: null,
    verified_solutions: [{ challenge_id: "challenge-1", solution_id: "solution-1", title: "Container startup failure", status: "verified", visibility: "company", solved_at: "2026-07-21", updated_at: "2026-07-21T00:00:00Z", technologies: ["Docker"] }]
  })),
  updateMyProfile: vi.fn(async (payload: { contact_email?: string }) => ({
    user_id: "solver-1",
    display_name: "Avery Engineer",
    job_title: "Platform Engineer",
    team: "Runtime",
    department: "Platform Engineering",
    department_id: "department-1",
    team_id: "team-1",
    contact_email: payload.contact_email ?? "avery@example.test",
    contact_handle: "@avery",
    skills: ["Docker troubleshooting", "Incident review"],
    technologies: ["Docker"],
    avatar_key: null,
    initials: "AE",
    bio: "Maintains runtime services.",
    contribution_count: 3,
    helpful_contribution_count: null,
    verified_solutions: [{ challenge_id: "challenge-1", solution_id: "solution-1", title: "Container startup failure", status: "verified", visibility: "company", solved_at: "2026-07-21", updated_at: "2026-07-21T00:00:00Z", technologies: ["Docker"] }]
  }))
}));

function createTestQueryClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } });
}

function renderApp(path = "/dashboard", queryClient = createTestQueryClient()) {
  render(<QueryClientProvider client={queryClient}><AuthProvider><MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }} initialEntries={[path]}><App /></MemoryRouter></AuthProvider></QueryClientProvider>);
}

async function signIn(user: ReturnType<typeof userEvent.setup>, role: "employee" | "reviewer" = "employee") {
  const email = role === "reviewer" ? "srikar.deshmukh@minfytech.com" : "syed.sofiyan@minfytech.com";
  await user.type(screen.getByLabelText("Work email"), email);
  await user.type(screen.getByLabelText("Password"), "development-only-password");
  await user.click(screen.getByRole("button", { name: "Sign in" }));
}

describe("App", () => {
  beforeEach(() => {
    setAccessToken(null);
    window.sessionStorage.clear();
    vi.clearAllMocks();
  });

  it("redirects unauthenticated users to login", () => {
    renderApp();
    expect(screen.getByRole("heading", { name: "Sign in to the knowledge platform" })).toBeInTheDocument();
  });

  it("signs in and reaches the protected foundation route", async () => {
    const user = userEvent.setup();
    renderApp("/login");
    await signIn(user);
    expect(await screen.findByRole("heading", { name: "What are you blocked on?" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Search solutions, people, or paste an error/ }));
    expect(screen.getByRole("dialog", { name: "Search and commands" })).toBeInTheDocument();
  });

  it("sends an employee to the permission state for reviewer routes", async () => {
    const user = userEvent.setup();
    renderApp("/reviews");
    await signIn(user);
    expect(await screen.findByRole("heading", { level: 2, name: "You do not have access to this content" })).toBeInTheDocument();
  });

  it("runs keyword search and opens the full solution", async () => {
    const user = userEvent.setup();
    renderApp("/search");
    await signIn(user);
    await user.type(await screen.findByPlaceholderText("Paste an error message or describe the roadblock"), "Docker startup failure");
    await user.click(screen.getByRole("button", { name: "Search" }));
    expect(await screen.findByRole("heading", { name: "Container startup failure" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Container startup failure/ }));
    expect(await screen.findByRole("heading", { name: "Docker import failure" })).toBeInTheDocument();
    expect(screen.queryByRole("dialog", { name: "Preview solution" })).not.toBeInTheDocument();
  });

  it("keeps a typed draft separate from the applied search query", async () => {
    const user = userEvent.setup();
    renderApp("/search");
    await signIn(user);

    const input = await screen.findByPlaceholderText("Paste an error message or describe the roadblock");
    await user.type(input, "Terraform");
    await user.click(screen.getByRole("button", { name: "Search" }));
    expect(await screen.findByTestId("applied-search-query")).toHaveTextContent("Terraform");

    await user.clear(input);
    await user.type(input, "Docker");
    expect(screen.getByTestId("applied-search-query")).toHaveTextContent("Terraform");

    await user.click(screen.getByRole("button", { name: "Search" }));
    expect(await screen.findByTestId("applied-search-query")).toHaveTextContent("Docker");
  });

  it("renders the employee profile with approved contact and verified solutions", async () => {
    const user = userEvent.setup();
    renderApp("/people/solver-1");
    await signIn(user);

    expect(await screen.findByRole("heading", { name: "Avery Engineer" })).toBeInTheDocument();
    expect(screen.getAllByText("Employee profile").length).toBeGreaterThan(0);
    expect(screen.getByText("Runtime")).toBeInTheDocument();
    expect(screen.getByText("Docker troubleshooting")).toBeInTheDocument();
    expect(await screen.findByRole("link", { name: "Contact the solver" })).toHaveAttribute("href", "mailto:avery@example.test");
    expect(screen.getByRole("link", { name: /Container startup failure/ })).toHaveAttribute("href", "/solutions/challenge-1");
  });

  it("updates work email from the editable profile form", async () => {
    const user = userEvent.setup();
    renderApp("/people/me");
    await signIn(user);

    expect(await screen.findByRole("heading", { name: "Avery Engineer" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Edit profile" }));
    const email = screen.getByLabelText("Work email");
    await user.clear(email);
    await user.type(email, "updated.avery@example.test");
    await user.click(screen.getByRole("button", { name: "Save profile" }));

    await waitFor(() => expect(updateMyProfile).toHaveBeenCalledWith(expect.objectContaining({ contact_email: "updated.avery@example.test" }), expect.anything()));
    expect(await screen.findByText("Profile updated.")).toBeInTheDocument();
  });

  it("saves a solved-problem draft through the authoring workflow", async () => {
    const user = userEvent.setup();
    renderApp("/solutions/new");
    await signIn(user);

    expect(await screen.findByRole("heading", { name: "Log a solved problem" })).toBeInTheDocument();
    await user.type(screen.getByLabelText("Problem title"), "Docker import failure");
    await user.click(screen.getByRole("button", { name: "Save as draft" }));

    await waitFor(() => expect(createChallenge).toHaveBeenCalledWith(expect.objectContaining({ title: "Docker import failure" })));
  });

  it("lets reviewers open the queue and approve a submitted solution", async () => {
    const user = userEvent.setup();
    renderApp("/reviews");
    await signIn(user, "reviewer");

    expect(await screen.findByRole("heading", { name: "Review submitted solutions" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Container startup failure/ })).toBeInTheDocument();
    await user.click(await screen.findByRole("button", { name: /Approve/ }));
    expect(await screen.findByText("Publishes this solution as verified knowledge.")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Record review decision" }));
    expect(await screen.findByText("Approved. The solution is now verified and available to authorized search users.")).toBeInTheDocument();
  });

  it("does not reuse a stale empty review queue after signing in as a reviewer", async () => {
    const user = userEvent.setup();
    const queryClient = createTestQueryClient();
    queryClient.setQueryData(["review-queue", "2"], []);
    renderApp("/reviews", queryClient);
    await signIn(user, "reviewer");

    expect(await screen.findByRole("button", { name: /Container startup failure/ })).toBeInTheDocument();
  });

  it("clears private query data on login and logout", async () => {
    const user = userEvent.setup();
    const queryClient = createTestQueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <AuthCacheProbe cacheKey={["employee-profile", "me"]} />
        </AuthProvider>
      </QueryClientProvider>
    );

    queryClient.setQueryData(["employee-profile", "me"], { display_name: "Previous user" });
    await user.click(screen.getByRole("button", { name: "Probe login" }));
    await waitFor(() => expect(queryClient.getQueryData(["employee-profile", "me"])).toBeUndefined());

    queryClient.setQueryData(["employee-profile", "me"], { display_name: "Signed-in user" });
    await user.click(screen.getByRole("button", { name: "Probe logout" }));
    await waitFor(() => expect(queryClient.getQueryData(["employee-profile", "me"])).toBeUndefined());
  });

  it("renders solution detail with solver contact and feedback controls", async () => {
    const user = userEvent.setup();
    renderApp("/solutions/challenge-1");
    await signIn(user);

    expect(await screen.findByRole("heading", { name: "Docker import failure" })).toBeInTheDocument();
    expect(screen.getByText("Solver profile")).toBeInTheDocument();
    expect(await screen.findByRole("link", { name: "Contact the solver" })).toHaveAttribute("href", "mailto:avery@example.test");
    await user.click(screen.getByRole("button", { name: /Resolved my issue/ }));
  });
});

function AuthCacheProbe({ cacheKey }: { cacheKey: string[] }) {
  const auth = useAuth();
  return (
    <div>
      <button onClick={() => void auth.login({ email: "srikar.deshmukh@minfytech.com", password: "development-only-password" })}>Probe login</button>
      <button onClick={() => void auth.logout()}>Probe logout</button>
      <span>{cacheKey.join("/")}</span>
    </div>
  );
}
