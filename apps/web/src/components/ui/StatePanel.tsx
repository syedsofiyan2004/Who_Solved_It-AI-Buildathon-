import { AlertCircle, FileQuestion, LockKeyhole, RefreshCw } from "lucide-react";

import { copy } from "../../content/uiCopy";
import { Button } from "./Button";

type StateKind = "empty" | "error" | "denied" | "notFound" | "comingSoon";

const details = {
  empty: { icon: FileQuestion, tag: "Empty", tone: "text-text-muted", rail: "bg-border-strong", title: copy.dashboard.empty, body: copy.search.emptyBody },
  error: { icon: AlertCircle, tag: "Error", tone: "text-danger", rail: "bg-danger", title: copy.state.networkTitle, body: copy.state.networkBody },
  denied: { icon: LockKeyhole, tag: "Restricted", tone: "text-warning", rail: "bg-warning", title: copy.state.permissionTitle, body: copy.state.permissionBody },
  notFound: { icon: FileQuestion, tag: "Not found", tone: "text-text-muted", rail: "bg-border-strong", title: copy.page.notFoundTitle, body: copy.page.notFoundBody },
  comingSoon: { icon: FileQuestion, tag: "Coming soon", tone: "text-brand-strong", rail: "bg-primary", title: copy.state.comingSoon, body: copy.search.emptyBody }
};

export function StatePanel({ kind, onRetry }: { kind: StateKind; onRetry?: () => void }) {
  const item = details[kind];
  const Icon = item.icon;
  return (
    <section className="ledger-row relative flex min-h-56 flex-col items-start justify-center overflow-hidden rounded-[10px] px-6 py-8">
      <span className={`ledger-rail ${item.rail}`} />
      <span className={`status-chip inline-flex items-center gap-1.5 uppercase ${item.tone}`}>
        <Icon className="h-3.5 w-3.5" aria-hidden="true" />
        {item.tag}
      </span>
      <h2 className="mt-3 font-display text-base font-semibold text-text">{item.title}</h2>
      <p className="mt-1 max-w-md text-sm leading-6 text-text-muted">{item.body}</p>
      {onRetry && <Button className="mt-5" onClick={onRetry}><RefreshCw className="h-4 w-4" aria-hidden="true" />{copy.action.retry}</Button>}
    </section>
  );
}
