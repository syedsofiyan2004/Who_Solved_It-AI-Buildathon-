import { useQuery } from "@tanstack/react-query";
import type { UseQueryResult } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Filter, Search, SlidersHorizontal, Sparkles, X } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { DetailSheet } from "../components/product/DetailSheet";
import { SearchResultCard } from "../components/product/SearchResultCard";
import { SolutionPreviewPanel } from "../components/product/SolutionPreviewPanel";
import { SolverProfilePanel } from "../components/product/SolverProfilePanel";
import { Button } from "../components/ui/Button";
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";
import { StatePanel } from "../components/ui/StatePanel";
import { copy } from "../content/uiCopy";
import { getEmployeeProfile, listTechnologies, searchSolutions, type EmployeeProfile, type SearchResult } from "../services/api";

type Sort = "relevance" | "newest";

export function SearchPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const query = params.get("q") ?? "";
  const page = parsePositiveInteger(params.get("page"));
  const verification = params.get("verification");
  const verifiedOnly = verification ? verification !== "all" : params.get("verified") !== "false";
  const sort: Sort = params.get("sort") === "newest" ? "newest" : "relevance";
  const includeSummary = params.get("summary") === "true";
  const selectedSolutionId = params.get("solution");
  const selectedSolverId = params.get("solver");
  const selectedTechnologyValues = params.getAll("technology");
  const [input, setInput] = useState(query);
  const validQuery = query.trim().length >= 3;
  const workspaceKey = useMemo(() => {
    const base = new URLSearchParams(params);
    base.delete("solution");
    base.delete("solver");
    return `resolve.search.scroll:${base.toString()}`;
  }, [params]);

  const technologies = useQuery({ queryKey: ["technologies"], queryFn: listTechnologies, staleTime: 10 * 60 * 1000 });
  const technologyIds = useMemo(() => {
    if (!technologies.data) return selectedTechnologyValues.filter(isUuid);
    return selectedTechnologyValues.flatMap((value) => {
      const normalized = value.toLowerCase();
      const match = technologies.data.find((item) => item.id === value || item.slug.toLowerCase() === normalized || item.name.toLowerCase() === normalized);
      return match ? [match.id] : isUuid(value) ? [value] : [];
    });
  }, [selectedTechnologyValues, technologies.data]);

  const resultQuery = useQuery({
    queryKey: ["hybrid-search", query, page, verifiedOnly, sort, includeSummary, technologyIds.join(",")],
    queryFn: () => searchSolutions({
      query,
      filters: { verified_only: verifiedOnly, technology_ids: technologyIds },
      page,
      page_size: 10,
      sort,
      include_summary: includeSummary,
    }),
    enabled: validQuery && (selectedTechnologyValues.length === 0 || !technologies.isLoading),
    staleTime: 2 * 60 * 1000,
  });

  const response = resultQuery.data;
  const selectedResult = response?.data.results.find((result) => result.challenge_id === selectedSolutionId || result.solution_id === selectedSolutionId) ?? null;
  const activeSolverId = selectedSolverId ?? selectedResult?.solver.user_id ?? null;
  const solver = useQuery({
    queryKey: ["employee-profile", activeSolverId],
    queryFn: () => getEmployeeProfile(activeSolverId ?? ""),
    enabled: Boolean(selectedSolverId && activeSolverId),
    staleTime: 5 * 60 * 1000,
  });

  useEffect(() => setInput(query), [query]);
  useEffect(() => {
    if (!response || selectedSolutionId || selectedSolverId) return;
    const saved = Number(window.sessionStorage.getItem(workspaceKey) ?? "0");
    if (Number.isFinite(saved) && saved > 0) window.requestAnimationFrame(() => window.scrollTo({ top: saved }));
    return () => window.sessionStorage.setItem(workspaceKey, String(window.scrollY));
  }, [workspaceKey, response, selectedSolutionId, selectedSolverId]);

  const rememberScroll = () => window.sessionStorage.setItem(workspaceKey, String(window.scrollY));
  const setSearch = (changes: Record<string, string | string[] | undefined>) => {
    rememberScroll();
    const next = new URLSearchParams(params);
    Object.entries(changes).forEach(([key, value]) => {
      next.delete(key);
      if (Array.isArray(value)) value.filter(Boolean).forEach((item) => next.append(key, item));
      else if (value) next.set(key, value);
    });
    const target = next.toString() ? `/search?${next.toString()}` : "/search";
    navigate(target, { preventScrollReset: true });
  };
  const submit = (event: FormEvent) => {
    event.preventDefault();
    const normalized = input.trim();
    if (normalized.length >= 3) setSearch({ q: normalized, page: undefined, solution: undefined, solver: undefined });
  };
  const clear = () => { setInput(""); navigate("/search", { preventScrollReset: true }); };
  const closeSolution = () => setSearch({ solution: undefined, solver: undefined });
  const closeSolver = () => setSearch({ solver: undefined });
  const openSolution = (result: SearchResult) => setSearch({ solution: result.challenge_id, solver: undefined });
  const openSolver = (result: SearchResult) => setSearch({ solution: result.challenge_id, solver: result.solver.user_id });
  const setTechnology = (value: string, enabled: boolean) => {
    const values = enabled ? [...selectedTechnologyValues, value] : selectedTechnologyValues.filter((item) => item !== value);
    setSearch({ technology: Array.from(new Set(values)), page: undefined, solution: undefined, solver: undefined });
  };

  return (
    <div className="space-y-6">
      <section className="relative overflow-hidden rounded-[22px] border border-border bg-surface p-5 shadow-soft sm:p-7">
        <div className="absolute -right-20 -top-28 h-64 w-64 rounded-full bg-primary/10 blur-3xl" />
        <div className="relative max-w-4xl">
          <span className="inline-flex items-center gap-2 text-xs font-semibold text-brand-strong"><Sparkles className="h-3.5 w-3.5" />Knowledge search</span>
          <h1 className="mt-2 text-2xl font-semibold tracking-[-0.03em] sm:text-3xl">Search the fix your teams already trust</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-text-muted">Describe the roadblock, paste the exact error, or narrow the search by technology. Open solutions and expert profiles without leaving this workspace.</p>
          <form className="mt-6 flex flex-col gap-3 sm:flex-row" onSubmit={submit}>
            <label className="sr-only" htmlFor="solution-search">{copy.search.title}</label>
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-4 top-3.5 h-4 w-4 text-text-muted" aria-hidden="true" />
              <input className="h-12 w-full rounded-app border border-input bg-surface pl-11 pr-4 text-sm text-text shadow-sm outline-none transition placeholder:text-text-muted focus:border-accent focus:shadow-focus" id="solution-search" minLength={3} onChange={(event) => setInput(event.target.value)} placeholder={copy.search.placeholder} value={input} />
            </div>
            <Button className="h-12 px-5" disabled={input.trim().length < 3} type="submit" variant="primary"><Search className="h-4 w-4" />{copy.action.search}</Button>
          </form>
        </div>
      </section>

      {!validQuery && <EmptySearch onSearch={(value) => { setInput(value); setSearch({ q: value }); }} />}

      {validQuery && (
        <div className={`grid gap-6 ${selectedResult || selectedSolverId ? "xl:grid-cols-[260px_minmax(0,1fr)_440px]" : "lg:grid-cols-[260px_minmax(0,1fr)]"}`}>
          <SearchFilters selectedTechnologyValues={selectedTechnologyValues} sort={sort} technologies={technologies.data ?? []} verifiedOnly={verifiedOnly} onClear={clear} onSort={(value) => setSearch({ sort: value === "newest" ? "newest" : undefined, page: undefined, solution: undefined, solver: undefined })} onTechnology={setTechnology} onVerified={(value) => setSearch({ verification: value ? "verified" : "all", verified: undefined, page: undefined, solution: undefined, solver: undefined })} />

          <section aria-live="polite" className="min-w-0">
            <div className="mb-4 flex flex-col gap-3 rounded-app border border-border bg-surface px-4 py-3 shadow-sm sm:flex-row sm:items-center sm:justify-between">
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-text" data-testid="applied-search-query">{copy.search.appliedQuery} <span className="font-normal text-text-muted">“{query}”</span></p>
                <p className="mt-1 text-xs text-text-muted">{response ? `${response.meta.total} relevant solutions` : verifiedOnly ? copy.search.verifiedResults : copy.search.resultCount}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                {selectedTechnologyValues.map((value) => <button className="inline-flex h-8 items-center gap-1 rounded-full border border-primary/20 bg-brand-soft px-2.5 text-xs font-medium text-brand-strong" key={value} onClick={() => setTechnology(value, false)} type="button">{value}<X className="h-3 w-3" /></button>)}
                <Button aria-pressed={includeSummary} onClick={() => setSearch({ summary: includeSummary ? undefined : "true", page: undefined })}><Sparkles className="h-4 w-4" />{copy.search.generateSummary}</Button>
              </div>
            </div>

            {resultQuery.isLoading && <LoadingSkeleton rows={5} />}
            {resultQuery.isError && <StatePanel kind="error" onRetry={() => void resultQuery.refetch()} />}
            {response && <SearchResults response={response} selectedSolutionId={selectedSolutionId} onPage={(nextPage) => setSearch({ page: String(nextPage), solution: undefined, solver: undefined })} onPreview={openSolution} onSolver={openSolver} />}
          </section>

          {(selectedResult || selectedSolverId) && (
            <aside className="premium-panel hidden min-w-0 rounded-[18px] p-5 xl:sticky xl:top-[96px] xl:block xl:max-h-[calc(100vh-7rem)] xl:overflow-y-auto">
              <PanelContent selectedResult={selectedResult} selectedSolverId={selectedSolverId} solver={solver} onCloseSolution={closeSolution} onCloseSolver={closeSolver} onSolver={() => selectedResult && openSolver(selectedResult)} />
            </aside>
          )}
        </div>
      )}

      {selectedResult && !selectedSolverId && <DetailSheet title={copy.search.preview} onClose={closeSolution}><SolutionPreviewPanel result={selectedResult} onClose={closeSolution} onSolver={() => openSolver(selectedResult)} /></DetailSheet>}
      {selectedSolverId && <DetailSheet title={copy.detail.solverProfile} onClose={closeSolver}><SolverContent solver={solver} onClose={closeSolver} /></DetailSheet>}
    </div>
  );
}

function EmptySearch({ onSearch }: { onSearch: (value: string) => void }) {
  const examples = ["ModuleNotFoundError", "Terraform state lock", "CrashLoopBackOff", "AccessDenied", "CUDA out of memory", "Kafka consumer lag"];
  return <section className="rounded-[18px] border border-dashed border-border bg-surface p-8 text-center shadow-sm"><span className="mx-auto grid h-12 w-12 place-items-center rounded-app bg-brand-soft text-brand-strong"><Search className="h-5 w-5" /></span><h2 className="mt-5 text-lg font-semibold">Start with the issue in front of you</h2><p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-text-muted">Use the exact error when you have it. The platform combines structured search, verified technical context, and expert ownership.</p><div className="mt-6 flex flex-wrap justify-center gap-2">{examples.map((example) => <button className="rounded-full border border-border bg-surface px-3 py-1.5 text-xs text-text-muted transition hover:border-border-strong hover:text-text" key={example} onClick={() => onSearch(example)}>{example}</button>)}</div></section>;
}

function SearchFilters({ selectedTechnologyValues, sort, technologies, verifiedOnly, onClear, onSort, onTechnology, onVerified }: { selectedTechnologyValues: string[]; sort: Sort; technologies: { id: string; name: string; slug: string }[]; verifiedOnly: boolean; onClear: () => void; onSort: (sort: Sort) => void; onTechnology: (value: string, enabled: boolean) => void; onVerified: (value: boolean) => void }) {
  return (
    <aside className="premium-panel h-fit rounded-[18px] p-4 lg:sticky lg:top-[96px]">
      <div className="flex items-center justify-between gap-2"><div className="flex items-center gap-2"><span className="grid h-8 w-8 place-items-center rounded-control bg-brand-soft text-brand-strong"><SlidersHorizontal className="h-4 w-4" /></span><div><p className="text-sm font-semibold">{copy.search.filters}</p><p className="text-[10px] text-text-muted">Refine the workspace</p></div></div>{selectedTechnologyValues.length > 0 && <span className="rounded-full bg-brand-soft px-2 py-1 text-[10px] font-semibold text-brand-strong">{selectedTechnologyValues.length}</span>}</div>
      <label className="mt-5 flex min-h-11 items-center justify-between gap-2 rounded-control border border-border bg-surface px-3 text-sm"><span><span className="block font-medium text-text">Verified solutions</span><span className="mt-0.5 block text-[10px] text-text-muted">Reviewed and reusable</span></span><input checked={verifiedOnly} onChange={(event) => onVerified(event.target.checked)} type="checkbox" /></label>
      {technologies.length > 0 && <fieldset className="mt-5"><legend className="text-[10px] font-semibold uppercase tracking-[0.14em] text-text-muted">{copy.profile.technologies}</legend><div className="mt-3 max-h-64 space-y-1 overflow-auto pr-1">{technologies.slice(0, 18).map((technology) => { const checked = selectedTechnologyValues.includes(technology.slug) || selectedTechnologyValues.includes(technology.name) || selectedTechnologyValues.includes(technology.id); return <label className={`flex min-h-9 items-center gap-2 rounded-control px-2.5 text-xs transition ${checked ? "bg-brand-soft font-medium text-brand-strong" : "text-text-muted hover:bg-surface-muted hover:text-text"}`} key={technology.id}><input checked={checked} onChange={(event) => onTechnology(technology.slug, event.target.checked)} type="checkbox" />{technology.name}</label>; })}</div></fieldset>}
      <label className="mt-5 block text-[10px] font-semibold uppercase tracking-[0.14em] text-text-muted" htmlFor="search-sort">{copy.search.sort}</label>
      <select className="mt-2 h-10 w-full rounded-control border border-input bg-surface px-3 text-sm text-text outline-none focus:border-accent" id="search-sort" onChange={(event) => onSort(event.target.value === "newest" ? "newest" : "relevance")} value={sort}><option value="relevance">{copy.search.sortRelevance}</option><option value="newest">{copy.search.sortNewest}</option></select>
      <Button className="mt-5 w-full" onClick={onClear} variant="ghost"><Filter className="h-4 w-4" />{copy.search.clear}</Button>
    </aside>
  );
}

function SearchResults({ response, selectedSolutionId, onPreview, onSolver, onPage }: { response: Awaited<ReturnType<typeof searchSolutions>>; selectedSolutionId: string | null; onPreview: (result: SearchResult) => void; onSolver: (result: SearchResult) => void; onPage: (page: number) => void }) {
  const { data, meta } = response;
  if (data.no_answer) return <section className="rounded-[18px] border border-dashed border-border bg-surface px-6 py-10 text-center"><h2 className="text-lg font-semibold">{copy.search.noAnswerTitle}</h2><p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-text-muted">{copy.search.noAnswerBody}</p></section>;
  return <>
    {data.summary && <section className="mb-5 rounded-[18px] border border-primary/20 bg-brand-soft/45 p-5"><div className="flex items-center gap-2 text-brand-strong"><Sparkles className="h-4 w-4" /><h2 className="text-sm font-semibold">{copy.search.summary}</h2></div><p className="mt-3 text-sm leading-7 text-text">{data.summary}</p><div className="mt-4 flex flex-wrap gap-2"><span className="text-xs text-text-muted">{copy.search.sources}</span>{data.summary_citations.map((citation) => <code className="max-w-full truncate rounded-control border border-primary/15 bg-surface/75 px-2 py-1 text-[10px] text-text-muted" key={citation}>{citation}</code>)}</div></section>}
    {data.summary_error && <p className="mb-4 rounded-control border border-warning/25 bg-warning/5 px-3 py-2 text-sm text-warning">{data.summary_error}</p>}
    {data.service_status.semantic_search === "not_available" && <p className="mb-4 text-xs text-text-muted">AI semantic search is not configured. Exact-error and keyword search remain available.</p>}
    <div className="space-y-3">{data.results.map((result) => <SearchResultCard key={result.solution_id} result={result} selected={selectedSolutionId === result.challenge_id || selectedSolutionId === result.solution_id} onPreview={() => onPreview(result)} onSolver={() => onSolver(result)} />)}</div>
    <div className="mt-6 flex items-center justify-between rounded-app border border-border bg-surface px-3 py-2"><Button disabled={meta.page <= 1} onClick={() => onPage(meta.page - 1)}><ChevronLeft className="h-4 w-4" />{copy.search.previousPage}</Button><span className="text-xs text-text-muted">Page {meta.page}</span><Button disabled={!meta.has_next} onClick={() => onPage(meta.page + 1)}>{copy.search.nextPage}<ChevronRight className="h-4 w-4" /></Button></div>
  </>;
}

function PanelContent({ selectedResult, selectedSolverId, solver, onCloseSolution, onCloseSolver, onSolver }: { selectedResult: SearchResult | null; selectedSolverId: string | null; solver: UseQueryResult<EmployeeProfile, Error>; onCloseSolution: () => void; onCloseSolver: () => void; onSolver: () => void }) {
  if (selectedSolverId) return <SolverContent solver={solver} onClose={onCloseSolver} />;
  if (selectedResult) return <SolutionPreviewPanel result={selectedResult} onClose={onCloseSolution} onSolver={onSolver} />;
  return <StatePanel kind="notFound" />;
}

function SolverContent({ solver, onClose }: { solver: UseQueryResult<EmployeeProfile, Error>; onClose: () => void }) {
  if (solver.isLoading) return <LoadingSkeleton rows={5} />;
  if (solver.isError) return <StatePanel kind="error" onRetry={() => void solver.refetch()} />;
  if (!solver.data) return <StatePanel kind="notFound" />;
  return <SolverProfilePanel profile={solver.data} onClose={onClose} />;
}

function parsePositiveInteger(value: string | null) {
  if (!value || !/^\d+$/.test(value)) return 1;
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) && parsed > 0 ? parsed : 1;
}

function isUuid(value: string) {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);
}
