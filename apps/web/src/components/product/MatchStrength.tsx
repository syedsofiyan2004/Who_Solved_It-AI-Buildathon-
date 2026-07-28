import { SignalHigh, SignalLow, SignalMedium } from "lucide-react";

import { copy } from "../../content/uiCopy";

export function MatchStrength({ score }: { score: number }) {
  const strength = getStrength(score);
  const Icon = strength.kind === "strong" ? SignalHigh : strength.kind === "medium" ? SignalMedium : SignalLow;
  return (
    <span className={`inline-flex min-h-7 items-center gap-1.5 rounded-control border px-2 text-xs font-medium ${strength.className}`}>
      <Icon className="h-3.5 w-3.5" aria-hidden="true" />
      {copy.search.matchStrength}: {strength.label}
    </span>
  );
}

function getStrength(score: number) {
  if (score >= 0.75) return { kind: "strong", label: copy.search.strengthStrong, className: "border-success/40 text-success" };
  if (score >= 0.45) return { kind: "medium", label: copy.search.strengthMedium, className: "border-info/40 text-info" };
  return { kind: "low", label: copy.search.strengthLow, className: "border-warning/40 text-warning" };
}
