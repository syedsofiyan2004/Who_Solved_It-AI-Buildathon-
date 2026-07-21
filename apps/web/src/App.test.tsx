import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { AuthProvider } from "./auth/AuthProvider";

vi.mock("./services/api", () => ({
  login: vi.fn(async () => ({ access_token: "test-token", user: { id: "1", email: "employee@example.test", role: "employee", is_active: true, profile: null } })),
  logout: vi.fn(async () => undefined),
  fetchApiHealth: vi.fn(async () => ({ data: { service: "api", status: "ok", environment: "test", version: "0.1.0", rag_enabled: false }, meta: {} })),
  listChallenges: vi.fn(async () => ({ data: [], meta: { total: 0 } })),
  searchSolutions: vi.fn(async () => ({ data: { query_id: "search-1", results: [{ challenge_id: "challenge-1", solution_id: "solution-1", title: "Container startup failure", problem_excerpt: "Container did not start.", root_cause_excerpt: "The image copied files to the wrong path.", resolution_steps: ["Correct the Docker COPY path."], exact_error_message: "ModuleNotFoundError", updated_at: "2026-07-21T00:00:00Z", technologies: ["Docker"], solver: { user_id: "solver-1", display_name: "Avery Engineer", job_title: "Platform Engineer" }, match_reasons: ["Semantic match", "Keyword match"] }], summary: null, summary_citations: [], confidence: 0.72, no_answer: false, service_status: { keyword_search: "available", semantic_search: "available", grounded_summary: "not_requested" } }, meta: { page: 1, page_size: 10, total: 1, has_next: false } }))
}));

function renderApp(path = "/dashboard") {
  render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><AuthProvider><MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }} initialEntries={[path]}><App /></MemoryRouter></AuthProvider></QueryClientProvider>);
}

describe("App", () => {
  it("redirects unauthenticated users to login", () => {
    renderApp();
    expect(screen.getByRole("heading", { name: "Sign in to the knowledge platform" })).toBeInTheDocument();
  });

  it("signs in and reaches the protected foundation route", async () => {
    const user = userEvent.setup();
    renderApp("/login");
    await user.type(screen.getByLabelText("Work email"), "employee@example.test");
    await user.type(screen.getByLabelText("Password"), "correct-password");
    await user.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByRole("heading", { name: "Find a past solution" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Search past solutions Ctrl K" }));
    expect(screen.getByRole("dialog", { name: "Search and commands" })).toBeInTheDocument();
  });

  it("sends an employee to the permission state for reviewer routes", async () => {
    const user = userEvent.setup();
    renderApp("/reviews");
    await user.type(screen.getByLabelText("Work email"), "employee@example.test");
    await user.type(screen.getByLabelText("Password"), "correct-password");
    await user.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByRole("heading", { level: 2, name: "You do not have access to this content" })).toBeInTheDocument();
  });

  it("runs keyword search and opens a result preview", async () => {
    const user = userEvent.setup();
    renderApp("/search");
    await user.type(screen.getByLabelText("Work email"), "employee@example.test");
    await user.type(screen.getByLabelText("Password"), "correct-password");
    await user.click(screen.getByRole("button", { name: "Sign in" }));
    await user.type(await screen.findByPlaceholderText("Paste an error message or describe the roadblock"), "Docker startup failure");
    await user.click(screen.getByRole("button", { name: "Search" }));
    expect(await screen.findByRole("heading", { name: "Container startup failure" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Container startup failure/ }));
    expect(screen.getByRole("dialog", { name: "Preview solution" })).toBeInTheDocument();
  });

  it("keeps a typed draft separate from the applied search query", async () => {
    const user = userEvent.setup();
    renderApp("/search");
    await user.type(screen.getByLabelText("Work email"), "employee@example.test");
    await user.type(screen.getByLabelText("Password"), "correct-password");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

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
});
