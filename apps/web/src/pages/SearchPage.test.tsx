import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, useNavigate } from "react-router-dom";

const apiMocks = vi.hoisted(() => ({ searchSolutions: vi.fn() }));

vi.mock("../services/api", () => ({ searchSolutions: apiMocks.searchSolutions }));

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
      match_reasons: ["Query terms match the documented issue"]
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
  render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }} initialEntries={entries} initialIndex={initialIndex}><SearchPage />{historyControls && <HistoryControls />}</MemoryRouter></QueryClientProvider>);
}

describe("SearchPage", () => {
  beforeEach(() => apiMocks.searchSolutions.mockReset());

  it("renders complete technology chips", async () => {
    apiMocks.searchSolutions.mockResolvedValue(response());
    renderSearch();
    expect(await screen.findByText("Docker", { exact: true })).toBeInTheDocument();
    expect(screen.getByText("Python", { exact: true })).toBeInTheDocument();
  });

  it("restores the applied query and filters from a refreshed URL", async () => {
    apiMocks.searchSolutions.mockResolvedValue(response());
    renderSearch(["/search?q=Terraform&page=2&verified=false&sort=newest&summary=true"]);
    expect(await screen.findByTestId("applied-search-query")).toHaveTextContent("Terraform");
    expect(screen.getByDisplayValue("Terraform")).toBeInTheDocument();
    expect(screen.getByLabelText("Verified only")).not.toBeChecked();
    expect(screen.getByLabelText("Sort results")).toHaveValue("newest");
    expect(screen.getByRole("button", { name: "Generate grounded summary" })).toHaveAttribute("aria-pressed", "true");
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
    expect(await screen.findByText("Docker", { exact: true })).toBeInTheDocument();
  });

  it("shows the no-answer state", async () => {
    apiMocks.searchSolutions.mockResolvedValue(response({ results: [], confidence: null, no_answer: true }));
    renderSearch();
    expect(await screen.findByRole("heading", { name: "No reliable match was found" })).toBeInTheDocument();
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
