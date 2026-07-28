import { ArrowUpRight, Eye, Mail, ScanSearch } from "lucide-react";
import { Link } from "react-router-dom";

import { copy } from "../../content/uiCopy";
import type { SearchResult } from "../../services/api";
import { Button } from "../ui/Button";
import { MatchStrength } from "./MatchStrength";
import { SolverMiniProfile } from "./SolverMiniProfile";
import { VerificationBadge } from "./VerificationBadge";

export function SearchResultCard({ result, selected, onPreview, onSolver }: { result: SearchResult; selected?: boolean; onPreview: () => void; onSolver: () => void }) {
  return (
    <article className={`group relative overflow-hidden rounded-[18px] border bg-card text-card-foreground shadow-sm transition-all duration-160 hover:-translate-y-px hover:border-border-strong hover:shadow-soft ${selected ? "border-primary/55 ring-4 ring-primary/5" : "border-border"}`}>
      <div className={`absolute inset-y-0 left-0 w-1 transition-colors ${selected ? "bg-primary" : "bg-transparent group-hover:bg-primary/45"}`} />
      <div className="p-5 sm:p-6">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <button className="min-w-0 flex-1 text-left" onClick={onPreview} type="button">
            <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-text-muted">
              <ScanSearch className="h-3.5 w-3.5 text-brand-strong" aria-hidden="true" />
              Previous solution
            </div>
            <h2 className="text-[17px] font-semibold leading-6 tracking-[-0.015em] text-text transition-colors group-hover:text-brand-strong">{result.title}</h2>
            <p className="mt-2 line-clamp-2 max-w-3xl text-sm leading-6 text-text-muted">{result.problem_excerpt}</p>
          </button>
          <div className="flex shrink-0 flex-wrap gap-2 xl:justify-end">
            <MatchStrength score={result.score} />
            <VerificationBadge verified={result.status === "verified"} date={result.updated_at} />
          </div>
        </div>

        <div className="mt-5 rounded-app border border-border/80 bg-surface-muted/70 px-4 py-3.5">
          <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-text-muted">{copy.search.matchedPassage}</p>
          <p className="mt-1.5 line-clamp-3 text-sm leading-6 text-text">{result.root_cause_excerpt || result.problem_excerpt}</p>
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          {result.technologies.map((technology) => (
            <span className="rounded-full border border-border bg-surface px-2.5 py-1 text-[11px] font-medium text-text-muted" key={technology}>{technology}</span>
          ))}
          {result.match_reasons.slice(0, 3).map((reason) => (
            <span className="rounded-full bg-brand-soft px-2.5 py-1 text-[11px] font-medium text-brand-strong" key={reason}>{reason}</span>
          ))}
        </div>

        <div className="mt-5 flex flex-col gap-4 border-t border-border pt-4 md:flex-row md:items-center md:justify-between">
          <SolverMiniProfile solver={result.solver} compact onOpen={onSolver} />
          <div className="flex flex-wrap gap-2">
            {result.solver.contact_email && (
              <a className="inline-flex h-9 items-center justify-center gap-2 rounded-control border border-border bg-surface px-3 text-sm font-medium text-text transition-colors hover:border-border-strong hover:bg-surface-muted" href={`mailto:${result.solver.contact_email}`}>
                <Mail className="h-4 w-4" aria-hidden="true" />
                {copy.action.contactSolver}
              </a>
            )}
            <Button onClick={onPreview}><Eye className="h-4 w-4" aria-hidden="true" />{copy.action.previewSolution}</Button>
            <Link className="inline-flex h-9 items-center justify-center gap-2 rounded-control border border-primary/25 bg-brand-soft px-3 text-sm font-medium text-brand-strong transition-colors hover:border-primary/40 hover:bg-primary/10" to={`/solutions/${result.challenge_id}`}>
              {copy.action.openFullSolution}
              <ArrowUpRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          </div>
        </div>
      </div>
    </article>
  );
}
