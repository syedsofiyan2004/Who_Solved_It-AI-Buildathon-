import { ArrowUpRight, Mail, ScanSearch } from "lucide-react";
import { Link } from "react-router-dom";

import { copy } from "../../content/uiCopy";
import type { SearchResult } from "../../services/api";
import { MatchStrength } from "./MatchStrength";
import { SolverMiniProfile } from "./SolverMiniProfile";
import { VerificationBadge } from "./VerificationBadge";

export function SearchResultCard({ result, onOpen, onSolver }: { result: SearchResult; onOpen: () => void; onSolver: () => void }) {
  const verified = result.status === "verified";
  const recordId = result.solution_id.slice(0, 7);
  return (
    <article className="ledger-row group relative overflow-hidden rounded-[10px]">
      <span className={`ledger-rail ${verified ? "bg-success" : "bg-border-strong"}`} />
      <div className="relative grid gap-5 p-5 pl-6 lg:grid-cols-[minmax(0,1fr)_220px] lg:p-6 lg:pl-7">
        <div className="min-w-0">
          <button className="min-w-0 rounded-control text-left outline-none transition focus-visible:shadow-focus" onClick={onOpen} type="button">
            <div className="mb-2 flex flex-wrap items-center gap-x-2.5 gap-y-1 font-data text-[10px] uppercase tracking-[0.1em] text-text-muted">
              <span className="inline-flex items-center gap-1.5 text-brand-strong"><ScanSearch className="h-3.5 w-3.5" aria-hidden="true" />Record</span>
              <span aria-hidden="true">&middot;</span>
              <span>#{recordId}</span>
            </div>
            <h2 className="font-display text-[17px] font-semibold leading-6 tracking-[-0.01em] text-text transition-colors group-hover:text-brand-strong">{result.title}</h2>
            <p className="mt-2 line-clamp-2 max-w-3xl text-sm leading-6 text-text-muted">{result.problem_excerpt}</p>
          </button>

          <div className="mt-5 rounded-[10px] border border-border/80 bg-surface-muted/70 px-4 py-3.5 transition-colors group-hover:bg-surface-muted">
            <p className="font-data text-[10px] uppercase tracking-[0.12em] text-text-muted">{copy.search.matchedPassage}</p>
            <p className="mt-1.5 line-clamp-3 font-data text-[13px] leading-6 text-text">{result.root_cause_excerpt || result.problem_excerpt}</p>
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-2">
            {result.technologies.map((technology) => (
              <span className="rounded-control border border-border bg-surface px-2.5 py-1 text-[11px] font-medium text-text-muted transition group-hover:border-border-strong" key={technology}>{technology}</span>
            ))}
            {result.match_reasons.slice(0, 3).map((reason) => (
              <span className="rounded-control bg-brand-soft px-2.5 py-1 text-[11px] font-medium text-brand-strong" key={reason}>{reason}</span>
            ))}
          </div>

          <div className="mt-4 flex items-center gap-2 border-t border-dashed border-border pt-3 text-xs text-text-muted">
            <span aria-hidden="true" className="font-data text-text-muted/70">blame &rarr;</span>
            <button className="font-medium text-text underline decoration-border decoration-1 underline-offset-2 hover:text-brand-strong hover:decoration-brand-strong" onClick={onSolver} type="button">
              {result.solver.display_name}
            </button>
            <span className="text-text-muted">solved this</span>
          </div>
        </div>

        <aside className="flex flex-col justify-between gap-4 rounded-[10px] border border-border bg-surface-muted/55 p-4">
          <div className="space-y-3">
            <div className="flex flex-wrap gap-2">
              <MatchStrength score={result.score} />
              <VerificationBadge verified={verified} date={result.updated_at} />
            </div>
            <SolverMiniProfile solver={result.solver} compact onOpen={onSolver} />
          </div>
          <div className="flex flex-wrap gap-2">
            {result.solver.contact_email && (
              <a className="pressable inline-flex h-9 items-center justify-center gap-2 rounded-control border border-border bg-surface px-3 text-sm font-medium text-text transition-colors hover:border-border-strong hover:bg-surface-muted hover:shadow-sm" href={`mailto:${result.solver.contact_email}`}>
                <Mail className="h-4 w-4" aria-hidden="true" />
                Contact
              </a>
            )}
            <Link className="pressable inline-flex h-9 items-center justify-center gap-2 rounded-control border border-primary/25 bg-brand-soft px-3 text-sm font-medium text-brand-strong transition-colors hover:border-primary/40 hover:bg-primary/10 hover:shadow-sm" to={`/solutions/${result.challenge_id}`} title={copy.action.openFullSolution}>
              {copy.action.openFullSolution}
              <ArrowUpRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          </div>
        </aside>
      </div>
    </article>
  );
}
