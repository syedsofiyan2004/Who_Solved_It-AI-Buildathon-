import { ArrowRight, Search } from "lucide-react";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { copy } from "../content/uiCopy";
import { Button } from "../components/ui/Button";
import { PageHeader } from "../components/ui/PageHeader";
import { StatePanel } from "../components/ui/StatePanel";
import { listChallenges } from "../services/api";

export function DashboardPage() {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();
  const recent = useQuery({ queryKey: ["recent-solutions"], queryFn: () => listChallenges() });
  const search = () => navigate(`/search${query.trim() ? `?q=${encodeURIComponent(query.trim())}` : ""}`);

  return <div className="space-y-8"><PageHeader title={copy.dashboard.title} /><section className="border border-border bg-surface p-5 sm:p-6"><label className="sr-only" htmlFor="dashboard-search">{copy.search.title}</label><div className="flex flex-col gap-3 sm:flex-row"><div className="relative flex-1"><Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-text-muted" aria-hidden="true" /><input className="h-10 w-full rounded-control border border-border bg-surface pl-10 pr-3 text-sm placeholder:text-text-muted" id="dashboard-search" onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") search(); }} placeholder={copy.dashboard.searchHint} value={query} /></div><Button variant="primary" onClick={search}>{copy.action.openSearch}<ArrowRight className="h-4 w-4" aria-hidden="true" /></Button></div></section><section className="flex flex-col gap-4 border-b border-border pb-6 sm:flex-row sm:items-center sm:justify-between"><div><h2 className="text-base font-semibold">{copy.dashboard.logPrompt}</h2><p className="mt-1 text-sm text-text-muted">{copy.page.authoringBody}</p></div><Button onClick={() => navigate("/solutions/new")}>{copy.dashboard.logAction}</Button></section><section><h2 className="mb-4 text-base font-semibold">{copy.dashboard.recent}</h2>{recent.isLoading ? <p className="text-sm text-text-muted">{copy.state.loading}</p> : recent.isError ? <StatePanel kind="error" onRetry={() => void recent.refetch()} /> : recent.data?.data.length ? <div className="divide-y divide-border border border-border bg-surface">{recent.data.data.map((item) => <button className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left hover:bg-surface-muted" key={item.id} onClick={() => navigate(`/solutions/${item.id}`)}><span className="text-sm font-medium">{item.title}</span><span className="text-xs text-text-muted">{item.status}</span></button>)}</div> : <StatePanel kind="empty" />}</section></div>;
}
