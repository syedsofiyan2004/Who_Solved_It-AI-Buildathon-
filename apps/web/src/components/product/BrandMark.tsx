import { Waypoints } from "lucide-react";

export function BrandMark({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex min-w-0 items-center gap-3">
      <span className="relative grid h-9 w-9 shrink-0 place-items-center overflow-hidden rounded-[10px] border border-primary/25 bg-brand-soft text-brand-strong">
        <Waypoints className="h-[18px] w-[18px]" aria-hidden="true" />
        <span className="absolute inset-x-0 bottom-0 h-[3px] bg-gradient-to-r from-success via-primary to-warning" />
      </span>
      {!compact && (
        <span className="min-w-0 leading-none">
          <span className="block truncate font-display text-sm font-semibold tracking-[-0.01em] text-text">Minfy Resolve</span>
          <span className="mt-1 block truncate font-data text-[10px] uppercase tracking-[0.14em] text-text-muted">Knowledge &amp; expert ledger</span>
        </span>
      )}
    </div>
  );
}
