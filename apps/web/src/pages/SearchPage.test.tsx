import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes, useNavigate } from "react-router-dom";

const apiMocks = vi.hoisted(() => ({ getEmployeeProfile: vi.fn(), listTechnologies: vi.fn(), searchSolutions: vi.fn() }));

vi.mock("../services/api", () => ({ getEmployeeProfile: apiMocks.getEmployeeProfile, listTechnologies: apiMocks.listTechnologies, searchSolutions: apiMocks.searchSolutions }));

import { SearchPage } from "./SearchPage";

const response = (overrides = {}) => ({
  data: {
    query_id: "query-1",
    results: [{
      challenge_id: "challenge-1", solution_id: "solution-1", title: "Docker import failure",
      problem_excerpt: "Docker could not import the package.", root_cause_excerpt: "Wrong copy path.",
      resolution_steps: ["Correct COPY path."], exact_error_message: "ModuleNotFoundError",
      updated_at: "2026-07-21T00:00:00Z", technologies: ["Docker", "Python"],
      solver: { user_id: "solver-1", display_name: "Fictional Engineer", job_title: "Engineer" },
      match_reasons: ["Query terms match the documented issue"],
      score: 0.81
    }], summary: null, summary_citations: [], summary_error: null, confidence: 0.8,
    no_answer: false, service_status: { keyword_search: "available", semantic_search: "available", grounded_summary: "not_requested" },
    ...overrides
  },
  meta: { page: 1, page_size: 10, total: 1, has_next: false }
});

function HistoryControls() {
  const navigate = useNavigate();
  return <><button onClick={() => navigate(-1)} type="button">Back</button><button onClick={() => navigate(1)} type="button">Forward</button></>;
}

function renderSearch(entries = ["/search?q=Docker"], initialIndex?: number, historyControls = false) {
  render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }} initialEntries={entries} initialIndex={initialIndex}><Routes><Route path="/search" element={<SearchPage />} /><Route path="*" element={<SearchPage />} /></Routes>{historyControls && <HistoryControls />}</MemoryRouter></QueryClientProvider>);
}

describe("SearchPage", () => {
  beforeEach(() => {
    apiMocks.searchSolutions.mockReset();
    apiMocks.getEmployeeProfile.mockReset();
    apiMocks.listTechnologies.mockReset();
    apiMocks.listTechnologies.mockResolvedValue([{ id: "technology-1", name: "Docker", slug: "docker", category: "containers" }, { id: "technology-2", name: "Python", slug: "python", category: "language" }]);
    apiMocks.getEmployeeProfile.mockResolvedValue({
      user_id: "solver-1",
      display_name: "Fictional Engineer",
      job_title: "Engineer",
      team: "Runtime",
      department: "Platform",
      department_id: "department-1",
      team_id: "team-1",
      contact_email: "fictional@example.test",
      contact_handle: "@fictional",
      skills: ["Debugging"],
      technologies: ["Docker", "Python"],
      avatar_key: null,
      initials: "FE",
      bio: null,
      contribution_count: 2,
      helpful_contribution_count: 1,
      verified_solutions: []
    });
  });

  it("renders complete technology chips", async () => {
    apiMocks.searchSolutions.mockResolvedValue(response());
    renderSearch();
    expect((await screen.findAllByText("Docker", { exact: true })).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Python", { exact: true }).length).toBeGreaterThan(0);
  });

  it("restores the applied query and filters from a refreshed URL", async () => {
    apiMocks.searchSolutions.mockResolvedValue(response());
    renderSearch(["/search?q=Terraform&page=2&verified=false&sort=newest&summary=true"]);
    expect(await screen.findByTestId("applied-search-query")).toHaveTextContent("Terraform");
    expect(screen.getByDisplayValue("Terraform")).toBeInTheDocument();
    expect(screen.getByLabelText(/Verified solutions/)).not.toBeChecked();
    expect(screen.getByLabelText("Sort results")).toHaveValue("newest");
    expect(screen.getByRole("button", { name: "Generate grounded summary" })).toHaveAttribute("aria-pressed", "true");
  });

  it("preserves technology filters from the URL", async () => {
    apiMocks.searchSolutions.mockResolvedValue(response());
    renderSearch(["/search?q=Docker&technology=docker&page=2"]);
    expect(await screen.findByTestId("applied-search-query")).toHaveTextContent("Docker");
    await waitFor(() => expect(apiMocks.searchSolutions).toHaveBeenCalledWith(expect.objectContaining({
      filters: expect.objectContaining({ technology_ids: ["technology-1"] }),
      page: 2
    })));
  });

  it("restores search state with browser back and forward", async () => {
    const user = userEvent.setup();
    apiMocks.searchSolutions.mockResolvedValue(response());
    renderSearch(["/search?q=Docker", "/search?q=Terraform"], 1, true);
    expect(await screen.findByTestId("applied-search-query")).toHaveTextContent("Terraform");
    await user.click(screen.getByRole("button", { name: "Back" }));
    expect(await screen.findByTestId("applied-search-query")).toHaveTextContent("Docker");
    await user.click(screen.getByRole("button", { name: "Forward" }));
    expect(await screen.findByTestId("applied-search-query")).toHaveTextContent("Terraform");
  });

  it("shows loading immediately for an applied query", async () => {
    let resolveSearch: ((value: ReturnType<typeof response>) => void) | undefined;
    apiMocks.searchSolutions.mockReturnValue(new Promise((resolve) => { resolveSearch = resolve; }));
    renderSearch();
    expect(screen.getByRole("status", { name: "Loading" })).toBeInTheDocument();
    resolveSearch?.(response());
    expect((await screen.findAllByText("Docker", { exact: true })).length).toBeGreaterThan(0);
  });

  it("shows the no-answer state", async () => {
    apiMocks.searchSolutions.mockResolvedValue(response({ results: [], confidence: null, no_answer: true }));
    renderSearch();
    expect(await screen.findByRole("heading", { name: "No reliable match was found" })).toBeInTheDocument();
  });

  it("opens solution and solver panels from URL-backed state", async () => {
    const user = userEvent.setup();
    apiMocks.searchSolutions.mockResolvedValue(response());
    renderSearch();
    expect(await screen.findByRole("heading", { name: "Docker import failure" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Preview" }));
    expect(await screen.findByRole("dialog", { name: "Preview solution" })).toBeInTheDocument();
    await user.click(screen.getAllByRole("button", { name: "View solver" })[0]);
    expect(await screen.findByRole("dialog", { name: "Solver profile" })).toBeInTheDocument();
    expect(screen.getAllByRole("heading", { name: "Fictional Engineer" }).length).toBeGreaterThan(0);
  });

  it("shows an error and retries", async () => {
    apiMocks.searchSolutions.mockRejectedValueOnce(new Error("offline")).mockResolvedValueOnce(response());
    renderSearch();
    const retry = await screen.findByRole("button", { name: "Try again" });
    fireEvent.click(retry);
    expect(await screen.findByText("Docker", { exact: true })).toBeInTheDocument();
    expect(apiMocks.searchSolutions).toHaveBeenCalledTimes(2);
  });
});
