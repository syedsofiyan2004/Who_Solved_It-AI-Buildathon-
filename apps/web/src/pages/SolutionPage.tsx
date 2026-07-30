import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CalendarClock, CheckCircle2, Edit3, Mail, MessageSquareText, Paperclip, ShieldCheck, ThumbsDown, ThumbsUp, UserRound, Wrench } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { CodeBlock } from "../components/product/CodeBlock";
import { VerificationBadge } from "../components/product/VerificationBadge";
import { Button } from "../components/ui/Button";
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";
import { StatePanel } from "../components/ui/StatePanel";
import { copy } from "../content/uiCopy";
import { getChallenge, getEmployeeProfile, recordFeedback } from "../services/api";

export function SolutionPage() {
  const { challengeId = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [feedbackComment, setFeedbackComment] = useState("");
  const challenge = useQuery({ queryKey: ["challenge", challengeId], queryFn: () => getChallenge(challengeId), enabled: Boolean(challengeId) });
  const solver = useQuery({ queryKey: ["employee-profile", challenge.data?.owner_user_id], queryFn: () => getEmployeeProfile(challenge.data?.owner_user_id ?? ""), enabled: Boolean(challenge.data?.owner_user_id), staleTime: 5 * 60 * 1000 });
  const feedback = useMutation({
    mutationFn: (value: "helpful" | "not_helpful" | "resolved_my_issue") => recordFeedback({ solution_id: challenge.data?.solution_id ?? "", value, comment: feedbackComment.trim() || undefined }),
    onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ["challenge", challengeId] }); },
  });

  if (challenge.isLoading) return <LoadingSkeleton rows={8} />;
  if (challenge.isError || !challenge.data) return <StatePanel kind="notFound" onRetry={() => void challenge.refetch()} />;

  const item = challenge.data;
  const isVerified = item.status === "verified" && Boolean(item.last_verified_at);

  return (
    <div className="space-y-5">
      <button className="inline-flex items-center gap-2 text-sm font-medium text-text-muted transition-colors hover:text-text" onClick={() => navigate(-1)} type="button"><ArrowLeft className="h-4 w-4" />Back to workspace</button>

      <section className="ledger-row relative overflow-hidden rounded-[14px] px-5 py-6 sm:px-8 sm:py-8">
        <span className={`ledger-rail ${isVerified ? "bg-success" : "bg-border-strong"}`} />
        <div className="relative max-w-4xl pl-2">
          <p className="font-data text-[10px] uppercase tracking-[0.12em] text-text-muted">Record &middot; #{item.id.slice(0, 7)}</p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <span className="status-chip inline-flex items-center rounded-control border border-border px-2 py-1 uppercase text-text-muted">{item.status.replace(/_/g, " ")}</span>
            <span className="status-chip inline-flex items-center rounded-control border border-border px-2 py-1 uppercase text-text-muted">{item.visibility}</span>
            {isVerified && <VerificationBadge verified date={item.last_verified_at ?? item.updated_at} />}
          </div>
          <h1 className="mt-4 max-w-3xl font-display text-2xl font-semibold leading-tight tracking-[-0.015em] text-text sm:text-4xl">{item.title}</h1>
          <p className="mt-4 max-w-3xl text-sm leading-7 text-text-muted">{item.problem_description}</p>
          <div className="mt-5 flex flex-wrap items-center gap-2">
            {item.technologies.map((technology) => <span className="rounded-control border border-border bg-surface px-2.5 py-1 text-[11px] font-medium text-text-muted" key={technology}>{technology}</span>)}
          </div>
          {item.can_edit && <Link className="mt-6 inline-flex h-10 items-center justify-center gap-2 rounded-control border border-border bg-surface px-4 text-sm font-medium text-text transition-colors hover:bg-surface-muted" to={`/solutions/${item.id}/edit`}><Edit3 className="h-4 w-4" />{copy.action.editSolution}</Link>}
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,820px)_320px] xl:items-start">
        <article className="min-w-0 rounded-[14px] border border-border bg-surface p-5 shadow-sm sm:p-8">
          <DocumentSection index="01" title={copy.detail.symptoms}><p className="whitespace-pre-wrap text-sm leading-7 text-text-muted">{item.symptoms}</p></DocumentSection>
          {item.environment && <DocumentSection index="02" title={copy.detail.environment}><p className="whitespace-pre-wrap text-sm leading-7 text-text-muted">{item.environment}</p></DocumentSection>}
          {item.exact_error_message && <DocumentSection index="03" title={copy.detail.exactError}><CodeBlock value={item.exact_error_message} /></DocumentSection>}
          <DocumentSection index="04" title={copy.detail.rootCause}><p className="whitespace-pre-wrap text-sm leading-7 text-text-muted">{item.solution.root_cause}</p></DocumentSection>
          <DocumentSection index="05" title={copy.detail.resolution}>
            <ol className="space-y-4">
              {item.solution.resolution_steps.map((step, index) => <li className="flex gap-3 text-sm leading-7 text-text-muted" key={`${index}-${step}`}><span className="mt-1 grid h-6 w-6 shrink-0 place-items-center rounded-full bg-brand-soft text-[11px] font-semibold text-brand-strong">{index + 1}</span><span>{step}</span></li>)}
            </ol>
          </DocumentSection>
          {item.solution.prevention_notes && <DocumentSection index="06" title={copy.submit.preventionLabel}><p className="whitespace-pre-wrap text-sm leading-7 text-text-muted">{item.solution.prevention_notes}</p></DocumentSection>}
          {item.solution.code_snippets.length > 0 && <DocumentSection index={item.solution.prevention_notes ? "07" : "06"} title={copy.detail.code}><div className="space-y-4">{item.solution.code_snippets.map((snippet, index) => <CodeBlock key={`${index}-${snippet.slice(0, 20)}`} value={snippet} />)}</div></DocumentSection>}

          {item.attachments.length > 0 && <DocumentSection index={item.solution.prevention_notes ? "08" : "07"} title={copy.detail.attachments}><div className="divide-y divide-border rounded-app border border-border">{item.attachments.map((attachment) => <div className="flex items-center justify-between gap-3 px-4 py-3 text-sm" key={attachment.id}><span className="inline-flex min-w-0 items-center gap-2"><Paperclip className="h-4 w-4 shrink-0 text-text-muted" /><span className="truncate">{attachment.original_filename}</span></span><span className="shrink-0 rounded-full bg-surface-muted px-2 py-1 text-[10px] capitalize text-text-muted">{attachment.status.replace(/_/g, " ")}</span></div>)}</div></DocumentSection>}

          {item.review_history.length > 0 && <DocumentSection index="08" title={copy.detail.reviewTimeline}><div className="relative space-y-4 before:absolute before:bottom-3 before:left-[11px] before:top-3 before:w-px before:bg-border">{item.review_history.map((review) => <div className="relative flex gap-4" key={review.id}><span className="relative z-10 mt-1 h-6 w-6 shrink-0 rounded-full border-4 border-surface bg-primary" /><div className="min-w-0 rounded-app border border-border bg-surface-muted/45 p-4"><p className="text-sm font-semibold capitalize text-text">{review.decision.replace(/_/g, " ")}</p><p className="mt-1 text-xs text-text-muted">{review.reviewer_name} Â- {new Date(review.created_at).toLocaleString()}</p>{review.notes && <p className="mt-3 text-sm leading-6 text-text-muted">{review.notes}</p>}</div></div>)}</div></DocumentSection>}

          <section className="mt-10 rounded-[12px] border border-border bg-surface-muted/45 p-5">
            <div className="flex items-start gap-3"><span className="grid h-10 w-10 shrink-0 place-items-center rounded-control bg-brand-soft text-brand-strong"><MessageSquareText className="h-5 w-5" /></span><div><h2 className="text-sm font-semibold">{copy.detail.feedbackPrompt}</h2><p className="mt-1 text-xs text-text-muted">Help the next engineer understand whether this runbook worked.</p></div></div>
            <label className="mt-4 block text-xs font-medium text-text-muted">{copy.detail.feedbackComment}<textarea className="mt-2 w-full rounded-control border border-input bg-surface p-3 text-sm text-text outline-none focus:border-accent focus:shadow-focus" rows={3} value={feedbackComment} onChange={(event) => setFeedbackComment(event.target.value)} /></label>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button disabled={feedback.isPending} onClick={() => feedback.mutate("helpful")}><ThumbsUp className="h-4 w-4" />{copy.detail.helpful} ({item.feedback.helpful})</Button>
              <Button disabled={feedback.isPending} onClick={() => feedback.mutate("not_helpful")}><ThumbsDown className="h-4 w-4" />{copy.detail.notHelpful} ({item.feedback.not_helpful})</Button>
              <Button disabled={feedback.isPending} onClick={() => feedback.mutate("resolved_my_issue")} variant="primary"><CheckCircle2 className="h-4 w-4" />{copy.detail.resolved} ({item.feedback.resolved_my_issue})</Button>
            </div>
            {item.feedback.current_user_feedback && <p className="mt-3 text-sm text-success">{copy.detail.feedbackSaved}</p>}
            {feedback.isError && <p className="mt-3 text-sm text-warning">{copy.detail.feedbackError}</p>}
          </section>
        </article>

        <aside className="space-y-4 xl:sticky xl:top-[96px]">
          <section className="rounded-[12px] border border-border bg-surface p-5 shadow-sm">
            <div className="flex items-center gap-2 font-data text-[10px] uppercase tracking-[0.14em] text-brand-strong"><UserRound className="h-3.5 w-3.5" />{copy.detail.solverProfile}</div>
            {solver.isLoading && <LoadingSkeleton rows={3} />}
            {solver.data && <div className="mt-4"><div className="grid h-14 w-14 place-items-center rounded-[10px] border border-primary/20 bg-brand-soft font-data text-base font-semibold text-brand-strong">{solver.data.initials}</div><h2 className="mt-3 text-base font-semibold">{solver.data.display_name}</h2><p className="mt-1 text-sm text-text-muted">{solver.data.job_title}</p><p className="mt-2 text-xs leading-5 text-text-muted">{solver.data.team}<br />{solver.data.department}</p><div className="mt-4 flex flex-col gap-2"><a className="inline-flex h-10 items-center justify-center gap-2 rounded-control border border-primary bg-primary px-3 text-sm font-medium text-primary-foreground hover:bg-accent-hover" href={`mailto:${solver.data.contact_email}`}><Mail className="h-4 w-4" />{copy.action.contactSolver}</a><Link className="inline-flex h-10 items-center justify-center rounded-control border border-border px-3 text-sm font-medium hover:bg-surface-muted" to={`/people/${solver.data.user_id}`}>{copy.action.viewProfile}</Link></div></div>}
          </section>

          <section className="rounded-[12px] border border-border bg-surface p-5 shadow-sm">
            <div className="flex items-center gap-2 font-data text-[10px] uppercase tracking-[0.14em] text-text-muted"><ShieldCheck className="h-3.5 w-3.5" />Solution status</div>
            <div className="mt-4 space-y-3 text-sm"><Meta icon={Wrench} label="Current state" value={item.status.replace(/_/g, " ")} /><Meta icon={CalendarClock} label="Last updated" value={new Date(item.updated_at).toLocaleDateString()} />{isVerified && item.verified_by_name && <Meta icon={CheckCircle2} label="Verified by" value={item.verified_by_name} />}</div>
          </section>

          {item.related_solutions.length > 0 && <section className="rounded-[12px] border border-border bg-surface p-5 shadow-sm"><h2 className="text-sm font-semibold">{copy.detail.related}</h2><div className="mt-3 space-y-2">{item.related_solutions.map((related) => <Link className="block rounded-control border border-border p-3 text-sm transition-colors hover:border-border-strong hover:bg-surface-muted" key={related.challenge_id} to={`/solutions/${related.challenge_id}`}><span className="font-medium leading-5">{related.title}</span><span className="mt-2 block text-[11px] text-text-muted">{related.technologies.join(" Â- ")}</span></Link>)}</div></section>}
        </aside>
      </div>
    </div>
  );
}

function DocumentSection({ index, title, children }: { index: string; title: string; children: ReactNode }) {
  return <section className="grid gap-3 border-b border-border py-7 first:pt-0 last:border-0 sm:grid-cols-[42px_minmax(0,1fr)]"><span className="pt-0.5 font-data text-[10px] font-semibold text-brand-strong">{index}</span><div className="min-w-0"><h2 className="font-display text-sm font-semibold text-text">{title}</h2><div className="mt-3">{children}</div></div></section>;
}

function Meta({ icon: Icon, label, value }: { icon: LucideIcon; label: string; value: string }) {
  return <div className="flex items-start gap-3"><span className="grid h-8 w-8 shrink-0 place-items-center rounded-control bg-surface-muted text-text-muted"><Icon className="h-4 w-4" /></span><div><p className="font-data text-[10px] uppercase tracking-wide text-text-muted">{label}</p><p className="mt-0.5 text-sm font-medium capitalize text-text">{value}</p></div></div>;
}
