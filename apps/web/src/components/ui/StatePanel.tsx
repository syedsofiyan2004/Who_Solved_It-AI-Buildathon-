import { AlertCircle, FileQuestion, LockKeyhole, RefreshCw } from "lucide-react";

import { copy } from "../../content/uiCopy";
import { Button } from "./Button";

type StateKind = "empty" | "error" | "denied" | "notFound" | "comingSoon";

const details = {
  empty: { icon: FileQuestion, title: copy.dashboard.empty, body: copy.search.emptyBody },
  error: { icon: AlertCircle, title: copy.state.networkTitle, body: copy.state.networkBody },
  denied: { icon: LockKeyhole, title: copy.state.permissionTitle, body: copy.state.permissionBody },
  notFound: { icon: FileQuestion, title: copy.page.notFoundTitle, body: copy.page.notFoundBody },
  comingSoon: { icon: FileQuestion, title: copy.state.comingSoon, body: copy.search.emptyBody }
};

export function StatePanel({ kind, onRetry }: { kind: StateKind; onRetry?: () => void }) {
  const item = details[kind];
  const Icon = item.icon;
  return <section className="flex min-h-56 flex-col items-start justify-center border border-dashed border-border bg-surface px-6 py-8"><Icon className="h-5 w-5 text-text-muted" aria-hidden="true" /><h2 className="mt-4 text-base font-semibold text-text">{item.title}</h2><p className="mt-1 max-w-md text-sm leading-6 text-text-muted">{item.body}</p>{onRetry && <Button className="mt-5" onClick={onRetry}><RefreshCw className="h-4 w-4" aria-hidden="true" />{copy.action.retry}</Button>}</section>;
}
