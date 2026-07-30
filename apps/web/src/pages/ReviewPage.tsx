import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Clock3, FileSearch, Search, ShieldCheck, XCircle } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { Button } from "../components/ui/Button";
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";
import { StatePanel } from "../components/ui/StatePanel";
import { copy } from "../content/uiCopy";
import { getChallenge, reviewQueue, reviewSolution } from "../services/api";

export function ReviewPage() {
  const queryClient = useQueryClient();
  const queue = useQuery({ queryKey: ["review-queue"], queryFn: reviewQueue });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const [sort, setSort] = useState<"oldest" | "newest">("oldest");
  const filteredQueue = useMemo(() => {
    const rows = queue.data ?? [];
    const normalized = filter.trim().toLowerCase();
    const visible = normalized ? rows.filter((item) => item.title.toLowerCase().includes(normalized) || item.visibility.toLowerCase().includes(normalized)) : rows;
    return [...visible].sort((left, right) => sort === "newest" ? right.updated_at.localeCompare(left.updated_at) : left.updated_at.localeCompare(right.updated_at));
  }, [filter, queue.data, sort]);
  const activeId = selectedId && filteredQueue.some((item) => item.id === selectedId) ? selectedId : filteredQueue[0]?.id ?? null;
  const detail = useQuery({ queryKey: ["review-detail", activeId], queryFn: () => getChallenge(activeId ?? ""), enabled: Boolean(activeId) });
  const [notes, setNotes] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const decision = useMutation({
    mutationFn: async (value: "verified" | "changes_requested" | "rejected") => reviewSolution({ solution_id: detail.data?.solution_id ?? "", decision: value, notes: notes || undefined }),
    onSuccess: async () => {
      setNotes("");
      setMessage(copy.review.decisionSaved);
      await queryClient.invalidateQueries({ queryKey: ["review-queue"] });
      await queryClient.invalidateQueries({ queryKey: ["review-detail", activeId] });
    },
    onError: (reviewError) => setError(reviewError instanceof Error ? reviewError.message : copy.state.networkBody),
  });

  if (queue.isLoading) return <LoadingSkeleton rows={7} />;
  if (queue.isError) return <StatePanel kind="error" onRetry={() => void queue.refetch()} />;

  function record(value: "verified" | "changes_requested" | "rejected") {
    setError(null);
    if (value !== "verified" && !notes.trim()) {
      setError(copy.review.reasonRequired);
      return;
    }
    decision.mutate(value);
  }

  return (
    <div className="space-y-6">
      <section className="relative overflow-hidden rounded-app border border-border bg-surface p-6 shadow-soft sm:p-8">
        <div className="relative flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
          <div><span className="inline-flex items-center gap-2 font-data text-[10px] uppercase tracking-[0.14em] text-brand-strong"><ShieldCheck className="h-3.5 w-3.5" />Quality control</span><h1 className="mt-2 font-display text-2xl font-semibold tracking-[-0.015em] text-text sm:text-3xl">{copy.review.title}</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-text-muted">Review the technical evidence, request precise changes, and publish only reusable solutions.</p></div>
          <div className="rounded-control border border-border bg-surface px-4 py-3 text-sm"><span className="font-display text-2xl font-semibold tracking-[-0.01em] text-text">{queue.data?.length ?? 0}</span><span className="ml-2 text-xs text-text-muted">awaiting review</span></div>
        </div>
      </section>

      {message && <p className="rounded-app border border-success/25 bg-success/5 px-4 py-3 text-sm text-success">{message}</p>}
      {error && <p className="rounded-app border border-warning/25 bg-warning/5 px-4 py-3 text-sm text-warning">{error}</p>}

      {!queue.data || queue.data.length === 0 ? <section className="rounded-app border border-dashed border-border bg-surface p-10 text-center"><span className="mx-auto grid h-12 w-12 place-items-center rounded-control bg-brand-soft text-brand-strong"><CheckCircle2 className="h-5 w-5" /></span><h2 className="mt-4 font-display text-lg font-semibold">Review queue is clear</h2><p className="mt-2 text-sm text-text-muted">{copy.review.empty}</p></section> : (
        <div className="grid gap-6 xl:grid-cols-[340px_minmax(0,1fr)]">
          <aside className="h-fit rounded-app border border-border bg-surface p-3 shadow-sm xl:sticky xl:top-[96px]">
            <div className="p-2"><div className="flex items-center justify-between"><h2 className="font-display text-sm font-semibold">{copy.review.queue}</h2><span className="status-chip rounded-control bg-brand-soft px-2 py-1 text-brand-strong">{filteredQueue.length}</span></div><div className="relative mt-4"><Search className="absolute left-3 top-3 h-4 w-4 text-text-muted" /><input className="h-10 w-full rounded-control border border-input bg-surface pl-9 pr-3 text-sm outline-none focus:border-accent" id="review-filter" placeholder={copy.review.filter} value={filter} onChange={(event) => setFilter(event.target.value)} /></div><select className="mt-2 h-10 w-full rounded-control border border-input bg-surface px-3 text-sm outline-none focus:border-accent" id="review-sort" value={sort} onChange={(event) => setSort(event.target.value === "newest" ? "newest" : "oldest")}><option value="oldest">{copy.review.sortOldest}</option><option value="newest">{copy.review.sortNewest}</option></select></div>
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
              <section className="rounded-app border border-border bg-surface-muted/45 p-4"><label className="block text-sm font-semibold">{copy.review.notes}<textarea className="mt-2 w-full rounded-control border border-input bg-surface p-3 text-sm outline-none focus:border-accent focus:shadow-focus" placeholder="Add a clear reason when requesting changes or rejecting." rows={4} value={notes} onChange={(event) => setNotes(event.target.value)} /></label><div className="mt-4 flex flex-wrap gap-2"><Button disabled={decision.isPending} onClick={() => record("verified")} variant="primary"><CheckCircle2 className="h-4 w-4" />{copy.review.approve}</Button><Button disabled={decision.isPending} onClick={() => record("changes_requested")}><Clock3 className="h-4 w-4" />{copy.review.requestChanges}</Button><Button disabled={decision.isPending} onClick={() => record("rejected")}><XCircle className="h-4 w-4" />{copy.review.reject}</Button></div></section>
              {detail.data.review_history.length > 0 && <section className="mt-7"><h3 className="font-display text-sm font-semibold">{copy.review.history}</h3><div className="mt-3 space-y-2">{detail.data.review_history.map((review) => <div className="rounded-control border border-border p-3.5 text-sm" key={review.id}><p className="font-medium capitalize">{review.decision.replace(/_/g, " ")} &middot; {review.reviewer_name}</p>{review.notes && <p className="mt-2 leading-6 text-text-muted">{review.notes}</p>}</div>)}</div></section>}
            </>}
          </section>
        </div>
      )}
    </div>
  );
}

function ReviewSection({ title, body }: { title: string; body: string }) {
  return <section><h3 className="font-display text-sm font-semibold">{title}</h3><p className="mt-2 whitespace-pre-wrap text-sm leading-7 text-text-muted">{body || "-"}</p></section>;
}
