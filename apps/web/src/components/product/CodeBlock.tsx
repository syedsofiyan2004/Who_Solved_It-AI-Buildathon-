import { Check, Copy } from "lucide-react";
import { useState } from "react";

import { copy } from "../../content/uiCopy";

export function CodeBlock({ value, label = copy.detail.code }: { value: string; label?: string }) {
  const [copied, setCopied] = useState(false);
  async function copyCode() {
    await navigator.clipboard?.writeText(value);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1400);
  }

  return (
    <div className="overflow-hidden rounded-app border border-border bg-code text-code-foreground">
      <div className="flex min-h-9 items-center justify-between border-b border-border/70 px-3">
        <span className="text-xs font-medium text-code-foreground/70">{label}</span>
        <button className="inline-flex h-8 items-center gap-1 rounded-control px-2 text-xs text-code-foreground/80 hover:bg-surface/10" onClick={() => void copyCode()} type="button">
          {copied ? <Check className="h-3.5 w-3.5" aria-hidden="true" /> : <Copy className="h-3.5 w-3.5" aria-hidden="true" />}
          {copied ? copy.detail.copied : copy.detail.copyCode}
        </button>
      </div>
      <pre className="max-h-[360px] overflow-auto p-3 text-xs leading-5"><code>{value}</code></pre>
    </div>
  );
}
