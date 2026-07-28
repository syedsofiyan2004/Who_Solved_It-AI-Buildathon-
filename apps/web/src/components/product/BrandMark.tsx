import { Waypoints } from "lucide-react";

export function BrandMark({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex min-w-0 items-center gap-3">
      <span className="relative grid h-9 w-9 shrink-0 place-items-center overflow-hidden rounded-[12px] border border-primary/20 bg-brand-soft text-brand-strong shadow-soft">
        <Waypoints className="h-[18px] w-[18px]" aria-hidden="true" />
        <span className="absolute inset-x-1 bottom-0 h-px bg-primary/35" />
      </span>
      {!compact && (
        <span className="min-w-0 leading-none">
          <span className="block truncate text-sm font-semibold tracking-[-0.02em] text-text">Minfy Resolve</span>
          <span className="mt-1 block truncate text-[10px] font-medium uppercase tracking-[0.14em] text-text-muted">Knowledge & expert discovery</span>
        </span>
      )}
    </div>
  );
}
