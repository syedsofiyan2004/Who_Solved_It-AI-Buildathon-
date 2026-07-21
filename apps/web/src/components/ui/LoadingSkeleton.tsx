import { copy } from "../../content/uiCopy";

export function LoadingSkeleton({ rows = 3 }: { rows?: number }) {
  return <div className="space-y-3" aria-label={copy.state.loading} role="status">{Array.from({ length: rows }, (_, index) => <div className="h-12 animate-pulse rounded-app bg-surface-muted" key={index} />)}</div>;
}
