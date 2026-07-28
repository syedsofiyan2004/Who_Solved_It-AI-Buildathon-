import { Mail, UserRound } from "lucide-react";

import { copy } from "../../content/uiCopy";
import type { SearchResult } from "../../services/api";

type Solver = SearchResult["solver"];

export function SolverMiniProfile({ solver, compact = false, onOpen }: { solver: Solver; compact?: boolean; onOpen?: () => void }) {
  const initials = solver.initials ?? initialsFromName(solver.display_name);
  return (
    <div className="flex min-w-0 items-center gap-3">
      <div className="grid h-10 w-10 shrink-0 place-items-center rounded-full border border-border bg-surface-muted text-xs font-semibold text-text">
        {solver.avatar_key ? <UserRound className="h-4 w-4" aria-hidden="true" /> : initials}
      </div>
      <div className="min-w-0">
        <button className="block max-w-full truncate text-left text-sm font-semibold text-text hover:underline" onClick={onOpen} type="button">
          {solver.display_name}
        </button>
        <p className="truncate text-xs text-text-muted">{solver.job_title}{solver.team ? ` / ${solver.team}` : ""}</p>
        {!compact && solver.contact_email && (
          <a className="mt-2 inline-flex min-h-8 items-center gap-1.5 rounded-control border border-border px-2 text-xs font-medium text-text hover:bg-surface-muted" href={`mailto:${solver.contact_email}`}>
            <Mail className="h-3.5 w-3.5" aria-hidden="true" />
            {copy.action.contactSolver}
          </a>
        )}
      </div>
    </div>
  );
}

function initialsFromName(name: string) {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase()).join("") || "?";
}
