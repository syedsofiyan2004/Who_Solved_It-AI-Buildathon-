import { useQuery } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Search, SlidersHorizontal, X } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { Button } from "../components/ui/Button";
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";
import { PageHeader } from "../components/ui/PageHeader";
import { StatePanel } from "../components/ui/StatePanel";
import { copy } from "../content/uiCopy";
import { searchSolutions, type SearchResult } from "../services/api";

type Sort = "relevance" | "newest";

export function SearchPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const query = params.get("q") ?? "";
  const page = Math.max(Number(params.get("page") ?? "1"), 1);
  const verifiedOnly = params.get("verified") !== "false";
  const sort: Sort = params.get("sort") === "newest" ? "newest" : "relevance";
  const includeSummary = params.get("summary") === "true";
  const [input, setInput] = useState(query);
  const [selected, setSelected] = useState<SearchResult | null>(null);
  const validQuery = query.trim().length >= 3;
  const resultQuery = useQuery({
    queryKey: ["hybrid-search", query, page, verifiedOnly, sort, includeSummary],
    queryFn: () => searchSolutions({ query, filters: { verified_only: verifiedOnly }, page, page_size: 10, sort, include_summary: includeSummary }),
    enabled: validQuery
  });

  useEffect(() => setInput(query), [query]);
  useEffect(() => {
    const close = (event: KeyboardEvent) => { if (event.key === "Escape") setSelected(null); };
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, []);

  const setSearch = (changes: Record<string, string | undefined>) => {
    const next = new URLSearchParams(params);
    Object.entries(changes).forEach(([key, value]) => value ? next.set(key, value) : next.delete(key));
    navigate(`/search?${next.toString()}`);
  };
  const submit = (event: FormEvent) => {
    event.preventDefault();
    const normalized = input.trim();
    if (normalized.length >= 3) setSearch({ q: normalized, page: undefined });
  };
  const clear = () => { setInput(""); navigate("/search"); };
  const response = resultQuery.data;

  return <div className="space-y-6">
    <PageHeader title={copy.search.title} />
    <form className="border border-border bg-surface p-4" onSubmit={submit}>
      <label className="sr-only" htmlFor="solution-search">{copy.search.title}</label>
      <div className="flex flex-col gap-3 sm:flex-row"><div className="relative flex-1"><Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-text-muted" aria-hidden="true" /><input className="h-10 w-full rounded-control border border-border bg-surface pl-10 pr-3 text-sm placeholder:text-text-muted" id="solution-search" minLength={3} onChange={(event) => setInput(event.target.value)} placeholder={copy.search.placeholder} value={input} /></div><Button disabled={input.trim().length < 3} type="submit" variant="primary">{copy.action.search}</Button></div>
    </form>
    {!validQuery && <StatePanel kind="empty" />}
    {validQuery && <div className="grid gap-6 lg:grid-cols-[248px_minmax(0,1fr)]">
      <aside className="h-fit border border-border bg-surface p-4 lg:sticky lg:top-20"><div className="flex items-center gap-2"><SlidersHorizontal className="h-4 w-4 text-text-muted" aria-hidden="true" /><h2 className="text-sm font-semibold">{copy.search.filters}</h2></div><label className="mt-4 flex min-h-11 items-center gap-2 text-sm text-text-muted"><input checked={verifiedOnly} onChange={(event) => setSearch({ verified: event.target.checked ? undefined : "false", page: undefined })} type="checkbox" />{copy.search.verifiedOnly}</label><label className="mt-4 block text-sm text-text-muted" htmlFor="search-sort">{copy.search.sort}</label><select className="mt-2 h-10 w-full rounded-control border border-border bg-surface px-2 text-sm" id="search-sort" onChange={(event) => setSearch({ sort: event.target.value === "newest" ? "newest" : undefined, page: undefined })} value={sort}><option value="relevance">{copy.search.sortRelevance}</option><option value="newest">{copy.search.sortNewest}</option></select><Button className="mt-4 w-full" onClick={clear} variant="ghost">{copy.search.clear}</Button></aside>
      <section aria-live="polite" className="min-w-0"><div className="mb-4 flex flex-col gap-3 border-b border-border pb-4 sm:flex-row sm:items-center sm:justify-between"><div><p className="text-sm text-success">{copy.search.keywordAvailable}</p><p className="mt-1 text-sm text-text-muted">{copy.search.summaryAvailable}</p></div><Button aria-pressed={includeSummary} onClick={() => setSearch({ summary: includeSummary ? undefined : "true", page: undefined })}>{copy.search.generateSummary}</Button></div>{resultQuery.isLoading && <LoadingSkeleton rows={4} />}{resultQuery.isError && <StatePanel kind="error" onRetry={() => void resultQuery.refetch()} />}{response && <SearchResults response={response} onSelect={setSelected} onPage={(nextPage) => setSearch({ page: String(nextPage) })} />}</section>
    </div>}
    {selected && <PreviewDrawer result={selected} onClose={() => setSelected(null)} />}
  </div>;
}

function SearchResults({ response, onSelect, onPage }: { response: Awaited<ReturnType<typeof searchSolutions>>; onSelect: (result: SearchResult) => void; onPage: (page: number) => void }) {
  const { data, meta } = response;
  if (data.no_answer) return <section className="border border-dashed border-border bg-surface px-6 py-8"><h2 className="text-base font-semibold">{copy.search.noAnswerTitle}</h2><p className="mt-2 max-w-lg text-sm leading-6 text-text-muted">{copy.search.noAnswerBody}</p></section>;
  return <>{data.summary && <section className="mb-5 border border-border bg-surface p-4"><h2 className="text-sm font-semibold">{copy.search.summary}</h2><p className="mt-2 text-sm leading-6 text-text-muted">{data.summary}</p><div className="mt-3 flex flex-wrap gap-2"><span className="text-xs text-text-muted">{copy.search.sources}</span>{data.summary_citations.map((citation) => <code className="rounded-control border border-border px-2 py-1 text-xs" key={citation}>{citation}</code>)}</div></section>}{data.summary_error && <p className="mb-4 text-sm text-warning">{data.summary_error}</p>}<p className="mb-3 text-sm text-text-muted">{meta.total} {copy.search.resultCount}</p><div className="space-y-3">{data.results.map((result) => <article className="border border-border bg-surface p-4 transition-colors hover:border-border-strong" key={result.solution_id}><button className="w-full text-left" onClick={() => onSelect(result)}><div className="flex flex-col justify-between gap-2 sm:flex-row"><h2 className="text-base font-semibold text-text">{result.title}</h2><span className="text-xs text-text-muted">{result.match_reasons.includes(copy.search.exactError) ? copy.search.exactError : copy.search.keywordMatch}</span></div><p className="mt-2 text-sm leading-6 text-text-muted">{result.problem_excerpt}</p><p className="mt-3 text-sm text-text"><span className="text-text-muted">{copy.detail.solvedBy}: </span>{result.solver.display_name}</p><div className="mt-3 flex flex-wrap gap-2">{result.technologies.map((technology) => <span className="rounded-control border border-border px-2 py-1 text-xs text-text-muted" key={technology}>{technology}</span>)}</div></button><Button className="mt-4" onClick={() => onSelect(result)}>{copy.action.viewSolution}</Button></article>)}</div><div className="mt-6 flex items-center justify-between"><Button disabled={meta.page <= 1} onClick={() => onPage(meta.page - 1)}><ChevronLeft className="h-4 w-4" aria-hidden="true" />{copy.search.previousPage}</Button><Button disabled={!meta.has_next} onClick={() => onPage(meta.page + 1)}>{copy.search.nextPage}<ChevronRight className="h-4 w-4" aria-hidden="true" /></Button></div></>;
}

function PreviewDrawer({ result, onClose }: { result: SearchResult; onClose: () => void }) {
  return <div className="fixed inset-0 z-40 bg-text/30" onMouseDown={onClose} role="presentation"><aside aria-label={copy.search.preview} className="absolute inset-y-0 right-0 w-full max-w-xl overflow-y-auto bg-elevated p-5 shadow-overlay sm:p-6" onMouseDown={(event) => event.stopPropagation()} role="dialog" aria-modal="true"><div className="flex items-start justify-between gap-4"><div><p className="text-sm text-text-muted">{copy.search.preview}</p><h2 className="mt-1 text-xl font-semibold">{result.title}</h2></div><button aria-label={copy.action.close} className="grid h-10 w-10 place-items-center rounded-control text-text-muted hover:bg-surface-muted" onClick={onClose}><X className="h-5 w-5" aria-hidden="true" /></button></div><section className="mt-8"><h3 className="text-sm font-semibold">{copy.detail.rootCause}</h3><p className="mt-2 text-sm leading-6 text-text-muted">{result.root_cause_excerpt}</p></section><section className="mt-6"><h3 className="text-sm font-semibold">{copy.detail.resolution}</h3><ol className="mt-2 list-decimal space-y-2 pl-5 text-sm leading-6 text-text-muted">{result.resolution_steps.map((step) => <li key={step}>{step}</li>)}</ol></section>{result.exact_error_message && <pre className="mt-6 overflow-x-auto border border-border bg-code p-3 text-xs leading-5 text-text"><code>{result.exact_error_message}</code></pre>}<p className="mt-6 text-sm text-text"><span className="text-text-muted">{copy.detail.solvedBy}: </span>{result.solver.display_name}, {result.solver.job_title}</p><Button className="mt-6" onClick={onClose} variant="primary">{copy.action.close}</Button></aside></div>;
}
