import { CheckCircle2, CircleDashed } from "lucide-react";

import { copy } from "../../content/uiCopy";

export function VerificationBadge({ verified = false, date }: { verified?: boolean; date?: string | null }) {
  const Icon = verified ? CheckCircle2 : CircleDashed;
  return (
    <span className={`status-chip inline-flex min-h-7 items-center gap-1.5 rounded-control border px-2 uppercase ${verified ? "border-success/40 bg-success/[0.07] text-success" : "border-border text-text-muted"}`}>
      <Icon className="h-3.5 w-3.5" aria-hidden="true" />
      {verified ? copy.detail.verified : copy.detail.unverified}
      {verified && date && <span className="normal-case text-text-muted">&middot; {formatDate(date)}</span>}
    </span>
  );
}

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}
