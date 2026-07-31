import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Clock3, FileSearch, Search, ShieldCheck, XCircle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../auth/AuthProvider";
import { Button } from "../components/ui/Button";
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";
import { StatePanel } from "../components/ui/StatePanel";
import { copy } from "../content/uiCopy";
import { getChallenge, reviewQueue, reviewSolution } from "../services/api";

type ReviewDecision = "verified" | "changes_requested" | "rejected";

const decisionOptions: Record<ReviewDecision, { label: string; outcome: string; nextStep: string; tone: string }> = {
  verified: {
    label: copy.review.approve,
    outcome: "Publishes this solution as verified knowledge.",
    nextStep: "It becomes searchable for authorized employees and can be cited in grounded summaries.",
    tone: "border-success/35 bg-success/5 text-success",
  },
  changes_requested: {
    label: copy.review.requestChanges,
    outcome: "Returns this solution to the author for correction.",
    nextStep: "The author sees your notes, edits the entry, and submits it again for review.",
    tone: "border-warning/35 bg-warning/5 text-warning",
  },
  rejected: {
    label: copy.review.reject,
    outcome: "Rejects this submission from the verified knowledge base.",
    nextStep: "It will not appear in search results or grounded-summary context unless resubmitted later.",
    tone: "border-danger/35 bg-danger/5 text-danger",
  },
};

export function ReviewPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const queue = useQuery({
    queryKey: ["review-queue", user?.id],
    queryFn: reviewQueue,
    enabled: Boolean(user),
    staleTime: 0,
    refetchOnMount: "always",
  });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedDecision, setSelectedDecision] = useState<ReviewDecision | null>(null);
  const [filter, setFilter] = useState("");
  const [sort, setSort] = useState<"oldest" | "newest">("oldest");
  const [notes, setNotes] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const filteredQueue = useMemo(() => {
    const rows = queue.data ?? [];
    const normalized = filter.trim().toLowerCase();
    const visible = normalized
      ? rows.filter((item) => item.title.toLowerCase().includes(normalized) || item.visibility.toLowerCase().includes(normalized))
      : rows;
    return [...visible].sort((left, right) => sort === "newest" ? right.updated_at.localeCompare(left.updated_at) : left.updated_at.localeCompare(right.updated_at));
  }, [filter, queue.data, sort]);

  const activeId = selectedId && filteredQueue.some((item) => item.id === selectedId) ? selectedId : filteredQueue[0]?.id ?? null;
  const detail = useQuery({ queryKey: ["review-detail", activeId], queryFn: () => getChallenge(activeId ?? ""), enabled: Boolean(activeId), staleTime: 0 });
  const activeDecision = selectedDecision ? decisionOptions[selectedDecision] : null;
  const notesRequired = selectedDecision === "changes_requested" || selectedDecision === "rejected";
  const canSubmitDecision = Boolean(detail.data?.solution_id && selectedDecision && (!notesRequired || notes.trim()));

  useEffect(() => {
    setSelectedDecision(null);
    setNotes("");
    setError(null);
  }, [activeId]);

  const decision = useMutation({
    mutationFn: async (value: ReviewDecision) => reviewSolution({ solution_id: detail.data?.solution_id ?? "", decision: value, notes: notes.trim() || undefined }),
    onSuccess: async (_response, value) => {
      const reviewedId = activeId;
      setSelectedDecision(null);
      setNotes("");
      setError(null);
      setMessage(decisionMessage(value));
      setSelectedId(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["review-queue"] }),
        queryClient.invalidateQueries({ queryKey: ["home-review-queue"] }),
        queryClient.invalidateQueries({ queryKey: ["review-detail"] }),
        queryClient.invalidateQueries({ queryKey: ["home-drafts"] }),
      ]);
      if (reviewedId) queryClient.removeQueries({ queryKey: ["review-detail", reviewedId] });
      await queue.refetch();
    },
    onError: (reviewError) => setError(reviewError instanceof Error ? reviewError.message : copy.state.networkBody),
  });

  if (queue.isLoading) return <LoadingSkeleton rows={7} />;
  if (queue.isError) return <StatePanel kind="error" onRetry={() => void queue.refetch()} />;

  function chooseDecision(value: ReviewDecision) {
    setError(null);
    setMessage(null);
    setSelectedDecision(value);
  }

  function recordDecision() {
    if (!selectedDecision) {
      setError("Choose a review decision before recording it.");
      return;
    }
    if (notesRequired && !notes.trim()) {
      setError(copy.review.reasonRequired);
      return;
    }
    decision.mutate(selectedDecision);
  }

  return (
    <div className="space-y-6">
      <section className="relative overflow-hidden rounded-app border border-border bg-surface p-6 shadow-soft sm:p-8">
        <div className="relative flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <span className="inline-flex items-center gap-2 font-data text-[10px] uppercase tracking-[0.14em] text-brand-strong"><ShieldCheck className="h-3.5 w-3.5" />Quality control</span>
            <h1 className="mt-2 font-display text-2xl font-semibold tracking-[-0.015em] text-text sm:text-3xl">{copy.review.title}</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-text-muted">Review the technical evidence, decide the outcome, and make the next step clear to the author.</p>
          </div>
          <div className="rounded-control border border-border bg-surface px-4 py-3 text-sm"><span className="font-display text-2xl font-semibold tracking-[-0.01em] text-text">{queue.data?.length ?? 0}</span><span className="ml-2 text-xs text-text-muted">awaiting review</span></div>
        </div>
      </section>

      <section className="grid gap-3 md:grid-cols-3">
        <WorkflowStep number="01" title="Inspect evidence" body="Read the problem, symptoms, root cause, resolution steps, and exact error." />
        <WorkflowStep number="02" title="Choose outcome" body="Approve, request changes, or reject with a visible explanation of the impact." />
        <WorkflowStep number="03" title="Record decision" body="The item leaves the pending queue and the author sees the next action." />
      </section>

      {message && <p className="rounded-app border border-success/25 bg-success/5 px-4 py-3 text-sm text-success">{message}</p>}
      {error && <p className="rounded-app border border-warning/25 bg-warning/5 px-4 py-3 text-sm text-warning">{error}</p>}

      {!queue.data || queue.data.length === 0 ? <section className="rounded-app border border-dashed border-border bg-surface p-10 text-center"><span className="mx-auto grid h-12 w-12 place-items-center rounded-control bg-brand-soft text-brand-strong"><CheckCircle2 className="h-5 w-5" /></span><h2 className="mt-4 font-display text-lg font-semibold">Review queue is clear</h2><p className="mt-2 text-sm text-text-muted">{copy.review.empty}</p></section> : (
        <div className="grid gap-6 xl:grid-cols-[340px_minmax(0,1fr)]">
          <aside className="h-fit rounded-app border border-border bg-surface p-3 shadow-sm xl:sticky xl:top-[96px]">
            <div className="p-2">
              <div className="flex items-center justify-between"><h2 className="font-display text-sm font-semibold">{copy.review.queue}</h2><span className="status-chip rounded-control bg-brand-soft px-2 py-1 text-brand-strong">{filteredQueue.length}</span></div>
              <div className="relative mt-4"><Search className="absolute left-3 top-3 h-4 w-4 text-text-muted" /><input className="h-10 w-full rounded-control border border-input bg-surface pl-9 pr-3 text-sm outline-none focus:border-accent" id="review-filter" placeholder={copy.review.filter} value={filter} onChange={(event) => setFilter(event.target.value)} /></div>
              <select className="mt-2 h-10 w-full rounded-control border border-input bg-surface px-3 text-sm outline-none focus:border-accent" id="review-sort" value={sort} onChange={(event) => setSort(event.target.value === "newest" ? "newest" : "oldest")}><option value="oldest">{copy.review.sortOldest}</option><option value="newest">{copy.review.sortNewest}</option></select>
            </div>
            <div className="mt-2 space-y-1">{filteredQueue.length === 0 && <p className="px-3 py-6 text-center text-sm text-text-muted">{copy.review.noFilteredResults}</p>}{filteredQueue.map((item) => <button className={`w-full rounded-control border p-3.5 text-left transition-all ${item.id === activeId ? "border-primary/30 bg-brand-soft text-text shadow-sm" : "border-transparent text-text-muted hover:border-border hover:bg-surface-muted hover:text-text"}`} key={item.id} onClick={() => setSelectedId(item.id)} type="button"><span className="block text-sm font-semibold leading-5">{item.title}</span><span className="mt-2 flex items-center justify-between font-data text-[10px]"><span className="uppercase">{item.visibility}</span><span>{new Date(item.updated_at).toLocaleDateString()}</span></span></button>)}</div>
          </aside>

          <section className="min-w-0 rounded-app border border-border bg-surface p-5 shadow-sm sm:p-7">
            {detail.isLoading && <LoadingSkeleton rows={8} />}
            {detail.isError && <StatePanel kind="error" onRetry={() => void detail.refetch()} />}
            {detail.data && <>
              <div className="flex flex-col gap-4 border-b border-border pb-5 sm:flex-row sm:items-start sm:justify-between"><div><div className="flex flex-wrap gap-2"><span className="status-chip inline-flex items-center rounded-control border border-border px-2.5 py-1 uppercase text-text-muted">{detail.data.status.replace(/_/g, " ")}</span><span className="status-chip inline-flex items-center rounded-control border border-border px-2.5 py-1 uppercase text-text-muted">{detail.data.visibility}</span></div><h2 className="mt-3 font-display text-xl font-semibold tracking-[-0.01em] text-text">{detail.data.title}</h2></div><Link className="inline-flex h-9 items-center justify-center gap-2 rounded-control border border-border px-3 text-sm font-medium hover:bg-surface-muted" to={`/solutions/${detail.data.id}`}><FileSearch className="h-4 w-4" />{copy.action.viewSolution}</Link></div>
              <div className="grid gap-5 py-6 lg:grid-cols-2"><ReviewSection title={copy.detail.problem} body={detail.data.problem_description} /><ReviewSection title={copy.detail.symptoms} body={detail.data.symptoms} /></div>
              {detail.data.exact_error_message && <pre className="overflow-x-auto rounded-app border border-border bg-code p-4 text-xs text-code-foreground"><code>{detail.data.exact_error_message}</code></pre>}
              <div className="grid gap-5 py-6 lg:grid-cols-2"><ReviewSection title={copy.detail.rootCause} body={detail.data.solution.root_cause} /><section><h3 className="font-display text-sm font-semibold">{copy.detail.resolution}</h3><ol className="mt-3 space-y-3">{detail.data.solution.resolution_steps.map((step, index) => <li className="flex gap-3 text-sm leading-6 text-text-muted" key={`${index}-${step}`}><span className="grid h-5 w-5 shrink-0 place-items-center rounded-full bg-brand-soft font-data text-[10px] font-semibold text-brand-strong">{index + 1}</span>{step}</li>)}</ol></section></div>

              <section className="rounded-app border border-border bg-surface-muted/45 p-4">
                <div>
                  <h3 className="font-display text-sm font-semibold">Review decision</h3>
                  <p className="mt-1 text-sm text-text-muted">Choose one outcome. The platform will update the solution status and remove it from the pending queue after confirmation.</p>
                </div>
                <div className="mt-4 grid gap-3 lg:grid-cols-3">
                  <DecisionButton active={selectedDecision === "verified"} decision="verified" icon={<CheckCircle2 className="h-4 w-4" />} label={copy.review.approve} onClick={() => chooseDecision("verified")} text="Publish as verified." />
                  <DecisionButton active={selectedDecision === "changes_requested"} decision="changes_requested" icon={<Clock3 className="h-4 w-4" />} label={copy.review.requestChanges} onClick={() => chooseDecision("changes_requested")} text="Return to author." />
                  <DecisionButton active={selectedDecision === "rejected"} decision="rejected" icon={<XCircle className="h-4 w-4" />} label={copy.review.reject} onClick={() => chooseDecision("rejected")} text="Remove from review flow." />
                </div>
                {activeDecision && <div className={`mt-4 rounded-control border p-3.5 text-sm ${activeDecision.tone}`}><p className="font-semibold">If you choose {activeDecision.label}</p><p className="mt-1 leading-6">{activeDecision.outcome}</p><p className="mt-1 leading-6">{activeDecision.nextStep}</p></div>}
                <label className="mt-4 block text-sm font-semibold">{copy.review.notes}{notesRequired && <span className="ml-1 text-warning">(required)</span>}<textarea className="mt-2 w-full rounded-control border border-input bg-surface p-3 text-sm outline-none focus:border-accent focus:shadow-focus" placeholder={notesRequired ? "Explain exactly what the author must change before resubmitting." : "Optional: add reviewer notes for the audit trail."} rows={4} value={notes} onChange={(event) => setNotes(event.target.value)} /></label>
                <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
                  <p className="max-w-lg text-xs leading-5 text-text-muted">{selectedDecision ? "This action is recorded in the review history and audit log." : "Select an outcome to see what will happen next."}</p>
                  <Button disabled={!canSubmitDecision || decision.isPending} onClick={recordDecision} variant="primary">{decision.isPending ? "Recording decision" : "Record review decision"}</Button>
                </div>
              </section>

              {detail.data.review_history.length > 0 && <section className="mt-7"><h3 className="font-display text-sm font-semibold">{copy.review.history}</h3><div className="mt-3 space-y-2">{detail.data.review_history.map((review) => <div className="rounded-control border border-border p-3.5 text-sm" key={review.id}><p className="font-medium capitalize">{review.decision.replace(/_/g, " ")} &middot; {review.reviewer_name}</p>{review.notes && <p className="mt-2 leading-6 text-text-muted">{review.notes}</p>}</div>)}</div></section>}
            </>}
          </section>
        </div>
      )}
    </div>
  );
}

function decisionMessage(value: ReviewDecision) {
  if (value === "verified") return "Approved. The solution is now verified and available to authorized search users.";
  if (value === "changes_requested") return "Changes requested. The solution has been returned to the author with your notes.";
  return "Rejected. The solution was removed from the pending review queue.";
}

function WorkflowStep({ number, title, body }: { number: string; title: string; body: string }) {
  return <div className="rounded-app border border-border bg-surface p-4 shadow-sm"><span className="font-data text-[10px] font-semibold uppercase tracking-[0.14em] text-brand-strong">{number}</span><h2 className="mt-2 font-display text-sm font-semibold">{title}</h2><p className="mt-1 text-xs leading-5 text-text-muted">{body}</p></div>;
}

function DecisionButton({ active, decision, icon, label, text, onClick }: { active: boolean; decision: ReviewDecision; icon: ReactNode; label: string; text: string; onClick: () => void }) {
  const styles = {
    verified: active
      ? "border-success bg-success text-white shadow-[0_8px_20px_rgb(var(--color-success)_/_0.24)]"
      : "border-success/70 bg-success/20 text-success shadow-sm hover:border-success hover:bg-success/30 hover:shadow-[0_8px_18px_rgb(var(--color-success)_/_0.16)]",
    changes_requested: active
      ? "border-warning bg-warning text-white shadow-[0_8px_20px_rgb(var(--color-warning)_/_0.22)]"
      : "border-warning/70 bg-warning/20 text-warning shadow-sm hover:border-warning hover:bg-warning/30 hover:shadow-[0_8px_18px_rgb(var(--color-warning)_/_0.16)]",
    rejected: active
      ? "border-danger bg-danger text-white shadow-[0_8px_20px_rgb(var(--color-danger)_/_0.22)]"
      : "border-danger/70 bg-danger/20 text-danger shadow-sm hover:border-danger hover:bg-danger/30 hover:shadow-[0_8px_18px_rgb(var(--color-danger)_/_0.16)]",
  } satisfies Record<ReviewDecision, string>;

  return <button aria-pressed={active} className={`min-h-[94px] rounded-control border p-3.5 text-left transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-surface ${styles[decision]}`} onClick={onClick} type="button"><span className="flex items-center gap-2 text-sm font-semibold">{icon}{label}</span><span className={`mt-1 block text-xs leading-5 ${active ? "text-white/85" : "text-current/80"}`}>{text}</span></button>;
}

function ReviewSection({ title, body }: { title: string; body: string }) {
  return <section><h3 className="font-display text-sm font-semibold">{title}</h3><p className="mt-2 whitespace-pre-wrap text-sm leading-7 text-text-muted">{body || "-"}</p></section>;
}
