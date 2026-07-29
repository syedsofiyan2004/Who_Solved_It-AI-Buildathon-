import { useQuery } from "@tanstack/react-query";
import { ArrowRight, CheckCircle2, Clock3, FileClock, FilePlus2, Search, Sparkles, UsersRound } from "lucide-react";
import type { ReactNode } from "react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthProvider";
import { BrandMark } from "../components/product/BrandMark";
import { Button } from "../components/ui/Button";
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";
import { StatePanel } from "../components/ui/StatePanel";
import { copy } from "../content/uiCopy";
import { listChallenges, reviewQueue, type ChallengeSummary } from "../services/api";

export function DashboardPage() {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();
  const { user } = useAuth();
  const recent = useQuery({ queryKey: ["recent-solutions"], queryFn: () => listChallenges("verified") });
  const drafts = useQuery({ queryKey: ["home-drafts"], queryFn: () => listChallenges("draft") });
  const reviews = useQuery({ queryKey: ["home-review-queue"], queryFn: reviewQueue, enabled: user?.role === "reviewer" || user?.role === "administrator" });
  const search = () => navigate(`/search${query.trim() ? `?q=${encodeURIComponent(query.trim())}` : ""}`);

  const verifiedTotal = Number(recent.data?.meta.total ?? 0);
  const draftTotal = Number(drafts.data?.meta.total ?? 0);
  const reviewTotal = reviews.data?.length ?? 0;

  return (
    <div className="space-y-8">
      <section className="product-card relative overflow-hidden rounded-[24px] p-6 sm:p-8 lg:p-10">
        <div className="subtle-grid pointer-events-none absolute inset-0 opacity-35" />
        <div className="absolute -right-16 -top-28 h-72 w-72 rounded-full bg-primary/10 blur-3xl" />
        <div className="absolute -bottom-28 left-1/3 h-64 w-64 rounded-full bg-info/10 blur-3xl" />
        <div className="relative grid items-end gap-8 lg:grid-cols-[minmax(0,1fr)_340px]">
          <div className="max-w-3xl">
            <span className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-brand-soft px-3 py-1 text-xs font-semibold text-brand-strong"><Sparkles className="h-3.5 w-3.5" />Engineering knowledge, connected</span>
            <h1 className="mt-5 text-3xl font-semibold tracking-[-0.035em] sm:text-4xl">{copy.dashboard.title}</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-text-muted">Search the technical fixes your teams have already verified, then connect directly with the engineer who solved the issue.</p>
            <label className="sr-only" htmlFor="dashboard-search">{copy.search.title}</label>
            <div className="mt-7 flex flex-col gap-3 sm:flex-row">
              <div className="relative flex-1">
                <Search className="pointer-events-none absolute left-4 top-3.5 h-4 w-4 text-text-muted" aria-hidden="true" />
                <input className="h-12 w-full rounded-app border border-input bg-surface/95 pl-11 pr-4 text-sm text-text shadow-sm outline-none transition-all duration-160 placeholder:text-text-muted hover:border-border-strong focus:border-accent focus:shadow-focus" id="dashboard-search" onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") search(); }} placeholder={copy.dashboard.searchHint} value={query} />
              </div>
              <Button className="h-12 px-5" variant="primary" onClick={search}>{copy.search.title}<ArrowRight className="h-4 w-4" aria-hidden="true" /></Button>
            </div>
            <div className="mt-4 flex flex-wrap gap-2 text-xs text-text-muted">
              {['ModuleNotFoundError', 'Terraform state lock', 'CrashLoopBackOff', 'AccessDenied'].map((item) => <button className="pressable rounded-full border border-border bg-surface/70 px-3 py-1.5 transition hover:border-border-strong hover:bg-elevated hover:text-text hover:shadow-sm" key={item} onClick={() => navigate(`/search?q=${encodeURIComponent(item)}`)}>{item}</button>)}
            </div>
          </div>
          <div className="relative overflow-hidden rounded-[20px] border border-border bg-elevated/88 p-4 shadow-soft backdrop-blur">
            <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-primary/20 via-primary to-info/40" />
            <div className="flex items-center gap-3"><BrandMark compact /><div><p className="text-sm font-semibold">Workspace pulse</p><p className="mt-0.5 text-xs text-text-muted">Live from the local knowledge repository</p></div></div>
            <div className="mt-5 grid grid-cols-3 gap-2">
              <PulseMetric label="Verified" value={verifiedTotal} icon={<CheckCircle2 className="h-4 w-4" />} />
              <PulseMetric label="Drafts" value={draftTotal} icon={<FileClock className="h-4 w-4" />} />
              <PulseMetric label="Reviews" value={reviewTotal} icon={<Clock3 className="h-4 w-4" />} />
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <ActionPanel icon={<FilePlus2 className="h-[18px] w-[18px]" />} eyebrow="Contribute" title={copy.dashboard.logPrompt} body="Capture the root cause, steps, evidence, and owner while the solution is still fresh." to="/solutions/new" action={copy.dashboard.logAction} />
        <ActionPanel icon={<FileClock className="h-[18px] w-[18px]" />} eyebrow="Continue" title={copy.dashboard.drafts} body="Return to saved work without losing your technical context or review progress." to="/drafts" action={copy.nav.drafts} />
        <ActionPanel icon={<UsersRound className="h-[18px] w-[18px]" />} eyebrow="Connect" title="Find the right engineer" body="Browse people through the verified solutions and technologies they know best." to="/people" action="Discover expertise" />
      </section>

      <div className="grid gap-7 xl:grid-cols-[minmax(0,1.25fr)_minmax(360px,0.75fr)]">
        <ListSection empty={copy.dashboard.empty} isError={recent.isError} isLoading={recent.isLoading} items={recent.data?.data ?? []} onRetry={() => void recent.refetch()} title={copy.dashboard.recent} featured />
        <div className="space-y-7">
          {(user?.role === "reviewer" || user?.role === "administrator") && <ListSection empty={copy.review.empty} isError={reviews.isError} isLoading={reviews.isLoading} items={reviews.data ?? []} onRetry={() => void reviews.refetch()} title={copy.dashboard.reviews} />}
          {user?.role === "employee" && <ListSection empty={copy.dashboard.empty} isError={drafts.isError} isLoading={drafts.isLoading} items={drafts.data?.data ?? []} onRetry={() => void drafts.refetch()} title={copy.dashboard.drafts} edit />}
          <section className="rounded-app border border-border bg-surface p-5 shadow-soft">
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-text-muted">How it works</p>
            <div className="mt-4 space-y-4">
              <FlowStep number="01" title="Describe the roadblock" body="Use natural language or paste the exact error." />
              <FlowStep number="02" title="Review proven fixes" body="See grounded context, verification, and technical evidence." />
              <FlowStep number="03" title="Reach the solver" body="Open the engineer profile without leaving your search workspace." />
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

function PulseMetric({ icon, label, value }: { icon: ReactNode; label: string; value: number }) {
  return <div className="interactive-lift rounded-app border border-border bg-surface p-3"><span className="text-brand-strong">{icon}</span><p className="mt-3 text-xl font-semibold tracking-[-0.03em]">{value}</p><p className="mt-1 text-[10px] font-medium uppercase tracking-wide text-text-muted">{label}</p></div>;
}

function ActionPanel({ action, body, eyebrow, icon, title, to }: { action: string; body: string; eyebrow: string; icon: ReactNode; title: string; to: string }) {
  return <Link className="product-card interactive-lift group overflow-hidden rounded-app p-5" to={to}><div className="relative"><div className="flex items-center justify-between"><span className="grid h-10 w-10 place-items-center rounded-app border border-primary/15 bg-brand-soft text-brand-strong transition-transform duration-160 group-hover:scale-105">{icon}</span><ArrowRight className="h-4 w-4 text-text-muted transition-transform group-hover:translate-x-1 group-hover:text-brand-strong" /></div><p className="mt-5 text-[10px] font-semibold uppercase tracking-[0.14em] text-text-muted">{eyebrow}</p><h2 className="mt-2 text-base font-semibold tracking-[-0.015em]">{title}</h2><p className="mt-2 text-sm leading-6 text-text-muted">{body}</p><span className="mt-5 inline-flex text-sm font-semibold text-brand-strong">{action}</span></div></Link>;
}

function ListSection({ edit = false, empty, featured = false, isError, isLoading, items, onRetry, title }: { edit?: boolean; empty: string; featured?: boolean; isError?: boolean; isLoading?: boolean; items: ChallengeSummary[]; onRetry: () => void; title: string }) {
  return (
    <section>
      <div className="mb-4 flex items-center justify-between"><div><p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-text-muted">Knowledge</p><h2 className="mt-1 text-lg font-semibold tracking-[-0.02em]">{title}</h2></div><Link className="text-xs font-semibold text-brand-strong hover:underline" to={edit ? "/drafts" : "/search"}>View all</Link></div>
      {isLoading ? <LoadingSkeleton rows={5} /> : isError ? <StatePanel kind="error" onRetry={onRetry} /> : items.length ? (
        <div className="product-card overflow-hidden rounded-app">
          {items.slice(0, featured ? 7 : 5).map((item, index) => <Link className={`group relative flex items-center gap-4 px-4 py-4 transition hover:bg-surface-muted ${index ? "border-t border-border" : ""}`} key={item.id} to={edit ? `/solutions/${item.id}/edit` : `/solutions/${item.id}`}><span className="absolute inset-y-2 left-0 w-1 rounded-r-full bg-transparent transition-colors group-hover:bg-primary/50" /><span className="grid h-9 w-9 shrink-0 place-items-center rounded-control bg-brand-soft text-xs font-semibold text-brand-strong transition-transform group-hover:scale-105">{String(index + 1).padStart(2, "0")}</span><span className="min-w-0 flex-1"><span className="block truncate text-sm font-semibold transition-colors group-hover:text-brand-strong">{item.title}</span><span className="mt-1 block text-xs text-text-muted">Updated {new Date(item.updated_at).toLocaleDateString()}</span></span><span className="shrink-0 rounded-full border border-border px-2.5 py-1 text-[10px] font-semibold capitalize text-text-muted">{item.status.replace(/_/g, " ")}</span><ArrowRight className="h-4 w-4 shrink-0 text-text-muted transition-transform group-hover:translate-x-1 group-hover:text-brand-strong" /></Link>)}
        </div>
      ) : <p className="rounded-app border border-dashed border-border bg-surface p-5 text-sm text-text-muted">{empty}</p>}
    </section>
  );
}

function FlowStep({ body, number, title }: { body: string; number: string; title: string }) {
  return <div className="flex gap-3"><span className="mt-0.5 text-[10px] font-semibold text-brand-strong">{number}</span><div><p className="text-sm font-semibold">{title}</p><p className="mt-1 text-xs leading-5 text-text-muted">{body}</p></div></div>;
}
