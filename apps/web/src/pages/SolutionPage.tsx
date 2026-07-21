import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";
import { PageHeader } from "../components/ui/PageHeader";
import { StatePanel } from "../components/ui/StatePanel";
import { copy } from "../content/uiCopy";
import { getChallenge } from "../services/api";

export function SolutionPage() {
  const { challengeId = "" } = useParams();
  const challenge = useQuery({ queryKey: ["challenge", challengeId], queryFn: () => getChallenge(challengeId), enabled: Boolean(challengeId) });
  if (challenge.isLoading) return <LoadingSkeleton rows={6} />;
  if (challenge.isError || !challenge.data) return <StatePanel kind="notFound" onRetry={() => void challenge.refetch()} />;
  const item = challenge.data;
  return <article className="mx-auto max-w-[860px] space-y-8"><PageHeader title={item.title} description={`${item.status} · ${item.visibility}`} /><Section title={copy.detail.problem}>{item.problem_description}</Section><Section title={copy.detail.symptoms}>{item.symptoms}</Section>{item.exact_error_message && <pre className="overflow-x-auto border border-border bg-code p-3 text-xs leading-5"><code>{item.exact_error_message}</code></pre>}<Section title={copy.detail.rootCause}>{item.solution.root_cause}</Section><section><h2 className="text-sm font-semibold">{copy.detail.resolution}</h2><ol className="mt-3 list-decimal space-y-2 pl-5 text-sm leading-6 text-text-muted">{item.solution.resolution_steps.map((step) => <li key={step}>{step}</li>)}</ol></section>{item.solution.code_snippets.length > 0 && <section><h2 className="text-sm font-semibold">{copy.detail.code}</h2>{item.solution.code_snippets.map((snippet) => <pre className="mt-3 overflow-x-auto border border-border bg-code p-3 text-xs leading-5" key={snippet}><code>{snippet}</code></pre>)}</section>}</article>;
}

function Section({ title, children }: { title: string; children: string }) { return <section><h2 className="text-sm font-semibold">{title}</h2><p className="mt-3 text-sm leading-6 text-text-muted">{children}</p></section>; }
