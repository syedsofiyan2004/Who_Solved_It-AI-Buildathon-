import { ArrowUpRight, Mail, UserRound } from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { copy } from "../../content/uiCopy";
import type { SearchResult } from "../../services/api";
import { Button } from "../ui/Button";
import { CodeBlock } from "./CodeBlock";
import { MatchStrength } from "./MatchStrength";
import { SolverMiniProfile } from "./SolverMiniProfile";
import { VerificationBadge } from "./VerificationBadge";

export function SolutionPreviewPanel({ result, onClose, onSolver }: { result: SearchResult; onClose: () => void; onSolver: () => void }) {
  return (
    <div className="space-y-6">
      <header className="relative overflow-hidden rounded-app border border-border bg-surface-muted/55 p-4">
        <div className="relative">
          <div className="flex flex-wrap items-center gap-2">
            <MatchStrength score={result.score} />
            <VerificationBadge verified={result.status === "verified"} date={result.updated_at} />
          </div>
          <h2 className="mt-4 font-display text-xl font-semibold leading-7 tracking-[-0.01em] text-text">{result.title}</h2>
          <p className="mt-2 text-sm leading-6 text-text-muted">{result.problem_excerpt}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {result.match_reasons.slice(0, 3).map((reason) => <span className="rounded-control bg-brand-soft px-2.5 py-1 text-[11px] font-medium text-brand-strong" key={reason}>{reason}</span>)}
          </div>
        </div>
      </header>

      <PreviewSection number="01" title={copy.detail.rootCause}>
        <p className="text-sm leading-6 text-text-muted">{result.root_cause_excerpt}</p>
      </PreviewSection>
      <PreviewSection number="02" title={copy.detail.resolution}>
        <ol className="space-y-3">
          {result.resolution_steps.map((step, index) => (
            <li className="flex gap-3 text-sm leading-6 text-text-muted" key={`${index}-${step}`}>
              <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-brand-soft font-data text-[10px] font-semibold text-brand-strong">{index + 1}</span>
              <span>{step}</span>
            </li>
          ))}
        </ol>
      </PreviewSection>
      {result.exact_error_message && <CodeBlock label={copy.detail.exactError} value={result.exact_error_message} />}

      <section>
        <h3 className="font-data text-[10px] uppercase tracking-[0.14em] text-text-muted">{copy.detail.technologies}</h3>
        <div className="mt-3 flex flex-wrap gap-2">
          {result.technologies.map((technology) => <span className="rounded-control border border-border bg-surface px-2.5 py-1 text-[11px] font-medium text-text-muted" key={technology}>{technology}</span>)}
        </div>
      </section>

      <section className="product-card rounded-app p-4">
        <div className="relative">
          <div className="mb-3 flex items-center justify-between gap-3">
            <h3 className="font-display text-sm font-semibold">{copy.detail.solverProfile}</h3>
            <button className="text-xs font-medium text-brand-strong hover:underline" onClick={onSolver} type="button">View expertise</button>
          </div>
          <SolverMiniProfile solver={result.solver} onOpen={onSolver} />
        </div>
      </section>

      <div className="sticky bottom-0 -mx-5 flex flex-wrap gap-2 border-t border-border bg-elevated px-5 pb-1 pt-4">
        {result.solver.contact_email && <a className="inline-flex h-9 items-center justify-center gap-2 rounded-control border border-primary bg-primary px-3 text-sm font-medium text-primary-foreground transition-colors hover:bg-accent-hover" href={`mailto:${result.solver.contact_email}`}><Mail className="h-4 w-4" />{copy.action.contactSolver}</a>}
        <Button onClick={onSolver}><UserRound className="h-4 w-4" aria-hidden="true" />{copy.action.viewSolverPanel}</Button>
        <Link className="inline-flex h-9 items-center justify-center gap-2 rounded-control border border-border bg-surface px-3 text-sm font-medium text-text transition-colors hover:bg-surface-muted" to={`/solutions/${result.challenge_id}`}>
          {copy.action.openFullSolution}<ArrowUpRight className="h-4 w-4" />
        </Link>
        <Button className="ml-auto" onClick={onClose} variant="ghost">{copy.action.close}</Button>
      </div>
    </div>
  );
}

function PreviewSection({ number, title, children }: { number: string; title: string; children: ReactNode }) {
  return <section className="grid gap-3 sm:grid-cols-[32px_minmax(0,1fr)]"><span className="pt-0.5 font-data text-[10px] font-semibold text-brand-strong">{number}</span><div><h3 className="font-display text-sm font-semibold text-text">{title}</h3><div className="mt-2">{children}</div></div></section>;
}
