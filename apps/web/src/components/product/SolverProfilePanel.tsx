import { ArrowUpRight, Mail, UserRound } from "lucide-react";
import { Link } from "react-router-dom";

import { copy } from "../../content/uiCopy";
import type { EmployeeProfile } from "../../services/api";
import { Button } from "../ui/Button";

export function SolverProfilePanel({ profile, onClose }: { profile: EmployeeProfile; onClose: () => void }) {
  return (
    <div className="space-y-6">
      <header className="relative overflow-hidden rounded-app border border-border bg-surface-muted/55 p-5">
        <div className="relative flex items-start gap-4">
          <div className="grid h-16 w-16 shrink-0 place-items-center rounded-[14px] border border-primary/20 bg-brand-soft font-data text-lg font-semibold text-brand-strong shadow-sm">
            {profile.avatar_key ? <UserRound className="h-7 w-7" aria-hidden="true" /> : profile.initials}
          </div>
          <div className="min-w-0 pt-1">
            <p className="font-data text-[10px] uppercase tracking-[0.14em] text-brand-strong">Technical expert</p>
            <h2 className="mt-1 break-words font-display text-xl font-semibold tracking-[-0.01em]">{profile.display_name}</h2>
            <p className="mt-1 text-sm text-text-muted">{profile.job_title}</p>
            <p className="mt-1 text-xs text-text-muted">{profile.team} &middot; {profile.department}</p>
          </div>
        </div>
      </header>

      {profile.bio && <p className="text-sm leading-6 text-text-muted">{profile.bio}</p>}
      <div className="grid grid-cols-2 gap-3">
        <Metric label={copy.profile.contributions} value={profile.contribution_count} />
        <Metric label={copy.profile.helpful} value={profile.helpful_contribution_count ?? 0} />
      </div>
      <TagSection title={copy.profile.skills} values={profile.skills} accent />
      <TagSection title={copy.profile.technologies} values={profile.technologies} />

      <section>
        <div className="flex items-center justify-between gap-3"><h3 className="font-display text-sm font-semibold">{copy.profile.relevantSolutions}</h3><span className="text-xs text-text-muted">{profile.verified_solutions.length} verified</span></div>
        <div className="mt-3 space-y-2">
          {profile.verified_solutions.slice(0, 4).map((solution) => (
            <Link className="group block rounded-app border border-border bg-surface p-3.5 text-sm transition-all hover:border-border-strong hover:shadow-sm" key={solution.solution_id} to={`/solutions/${solution.challenge_id}`}>
              <span className="flex items-start justify-between gap-3"><span className="font-medium leading-5 text-text group-hover:text-brand-strong">{solution.title}</span><ArrowUpRight className="mt-0.5 h-4 w-4 shrink-0 text-text-muted" /></span>
              <span className="mt-2 block text-xs text-text-muted">
                {solution.technologies.map((technology, index) => <span key={`${solution.solution_id}-${technology}`}>{index > 0 && <span aria-hidden="true"> · </span>}{technology}</span>)}
              </span>
            </Link>
          ))}
          {profile.verified_solutions.length === 0 && <p className="rounded-app border border-dashed border-border p-4 text-sm text-text-muted">{copy.profile.emptySolutions}</p>}
        </div>
      </section>

      <div className="-mx-5 flex flex-wrap gap-2 border-t border-border bg-elevated px-5 pb-1 pt-4">
        <a className="inline-flex h-9 items-center justify-center gap-2 rounded-control border border-primary bg-primary px-3 text-sm font-medium text-primary-foreground transition-colors hover:bg-accent-hover" href={`mailto:${profile.contact_email}`}>
          <Mail className="h-4 w-4" aria-hidden="true" />{copy.action.contactSolver}
        </a>
        <Link className="inline-flex h-9 items-center justify-center gap-2 rounded-control border border-border bg-surface px-3 text-sm font-medium text-text transition-colors hover:bg-surface-muted" to={`/people/${profile.user_id}`}>
          {copy.action.openFullProfile}<ArrowUpRight className="h-4 w-4" />
        </Link>
        <Button className="ml-auto" onClick={onClose} variant="ghost">{copy.action.close}</Button>
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return <div className="rounded-control border border-border bg-surface p-3.5"><p className="font-display text-xl font-semibold tracking-[-0.01em] text-text">{value}</p><p className="mt-1 text-[11px] text-text-muted">{label}</p></div>;
}

function TagSection({ title, values, accent = false }: { title: string; values: string[]; accent?: boolean }) {
  return <section><h3 className="font-display text-sm font-semibold">{title}</h3><div className="mt-3 flex flex-wrap gap-2">{values.length ? values.map((value) => <span className={`rounded-control px-2.5 py-1 text-[11px] font-medium ${accent ? "bg-brand-soft text-brand-strong" : "border border-border bg-surface text-text-muted"}`} key={value}>{value}</span>) : <span className="text-sm text-text-muted">-</span>}</div></section>;
}
