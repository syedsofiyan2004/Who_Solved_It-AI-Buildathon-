import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertTriangle, Check, CheckCircle2, FileCheck2, Save, ShieldCheck, Sparkles, Upload } from "lucide-react";
import { ChangeEvent, useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";

import { Button } from "../components/ui/Button";
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";
import { PageHeader } from "../components/ui/PageHeader";
import { StatePanel } from "../components/ui/StatePanel";
import { copy } from "../content/uiCopy";
import { createChallenge, getChallenge, listTechnologies, submitChallenge, updateChallenge, uploadChallengeAttachment, type ChallengeDetail } from "../services/api";

const steps = [
  copy.submit.stepProblem,
  copy.submit.stepCause,
  copy.submit.stepResolution,
  copy.submit.stepReview,
];

type FormState = {
  id: string | null;
  expectedUpdatedAt: string | null;
  title: string;
  problemDescription: string;
  environment: string;
  symptoms: string;
  exactErrorMessage: string;
  rootCause: string;
  resolutionSteps: string;
  codeSnippets: string;
  preventionNotes: string;
  technologyIds: string[];
  visibility: "company" | "department" | "team" | "restricted" | "administrator";
};

const emptyForm: FormState = {
  id: null,
  expectedUpdatedAt: null,
  title: "",
  problemDescription: "",
  environment: "",
  symptoms: "",
  exactErrorMessage: "",
  rootCause: "",
  resolutionSteps: "",
  codeSnippets: "",
  preventionNotes: "",
  technologyIds: [],
  visibility: "company",
};

export function AuthoringPage() {
  const { challengeId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const initialMessage = (location.state as { message?: string } | null)?.message ?? null;
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [dirty, setDirty] = useState(false);
  const [autosavePulse, setAutosavePulse] = useState(0);
  const [message, setMessage] = useState<string | null>(initialMessage);
  const [error, setError] = useState<string | null>(null);
  const formRef = useRef(form);
  const editVersionRef = useRef(0);
  const activeSaveRef = useRef<Promise<ChallengeDetail | null> | null>(null);
  const technologies = useQuery({ queryKey: ["technologies"], queryFn: listTechnologies });
  const existing = useQuery({
    queryKey: ["authoring-challenge", challengeId],
    queryFn: () => getChallenge(challengeId ?? ""),
    enabled: Boolean(challengeId),
  });
  const saveMutation = useMutation({ mutationFn: saveDraft });
  const submitMutation = useMutation({ mutationFn: submitChallenge });
  const attachmentMutation = useMutation({ mutationFn: async ({ id, file }: { id: string; file: File }) => uploadChallengeAttachment(id, file) });
  const hasSecretWarning = useMemo(() => /(AKIA|ASIA|BEGIN PRIVATE KEY|password\s*=|secret\s*=|api[_-]?key\s*=)/i.test(Object.values(form).join(" ")), [form]);

  useEffect(() => {
    formRef.current = form;
  }, [form]);

  useEffect(() => {
    if (!existing.data) return;
    setForm(fromChallenge(existing.data));
    editVersionRef.current = 0;
    setDirty(false);
    setMessage((current) => current ?? copy.submit.restore);
  }, [existing.data]);

  useEffect(() => {
    if (!dirty || !form.id) return;
    const timer = window.setTimeout(() => {
      void persist("autosave");
    }, 1400);
    return () => window.clearTimeout(timer);
  }, [autosavePulse, dirty, form]);

  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => {
      if (!dirty) return;
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  if (existing.isLoading) return <LoadingSkeleton rows={8} />;
  if (existing.isError) return <StatePanel kind="notFound" onRetry={() => void existing.refetch()} />;

  const canSave = form.title.trim().length > 0;
  const canSubmit = canSave && form.problemDescription.trim() && form.symptoms.trim() && form.rootCause.trim() && form.resolutionSteps.trim();
  const completion = Math.round(([form.title, form.problemDescription, form.symptoms, form.rootCause, form.resolutionSteps].filter((value) => value.trim()).length / 5) * 100);
  const headerDescription = message ?? (form.id && !dirty ? copy.submit.saved : dirty ? copy.submit.unsaved : undefined);

  async function persist(mode: "manual" | "autosave"): Promise<ChallengeDetail | null> {
    if (activeSaveRef.current) {
      if (mode === "autosave") return activeSaveRef.current;
      await activeSaveRef.current;
    }

    const snapshot = { ...formRef.current, technologyIds: [...formRef.current.technologyIds] };
    if (!snapshot.title.trim()) return null;
    const startVersion = editVersionRef.current;
    setError(null);

    const operation = saveMutation
      .mutateAsync(snapshot)
      .then((saved) => {
        const hasNewerEdits = editVersionRef.current !== startVersion;
        setForm((current) => hasNewerEdits
          ? { ...current, id: saved.id, expectedUpdatedAt: saved.updated_at }
          : fromChallenge(saved));
        setDirty(hasNewerEdits);
        setMessage(hasNewerEdits ? null : mode === "autosave" ? copy.submit.autosaved : copy.submit.saved);
        if (!challengeId) navigate(`/solutions/${saved.id}/edit`, { replace: true, state: { message: copy.submit.saved } });
        return saved;
      })
      .catch((saveError) => {
        setError(saveError instanceof Error ? saveError.message : copy.state.networkBody);
        return null;
      })
      .finally(() => {
        activeSaveRef.current = null;
        if (editVersionRef.current !== startVersion) setAutosavePulse((value) => value + 1);
      });

    activeSaveRef.current = operation;
    const saved = await operation;
    if (saved && mode === "manual" && editVersionRef.current !== startVersion) return persist("manual");
    return saved;
  }

  async function submitForReview() {
    if (!canSubmit) {
      setError(copy.submit.validation);
      return;
    }
    const saved = await persist("manual");
    if (!saved) return;
    try {
      const submitted = await submitMutation.mutateAsync(saved.id);
      setDirty(false);
      setMessage(copy.submit.submitSuccess);
      navigate(`/solutions/${submitted.id}`);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : copy.state.networkBody);
    }
  }

  async function upload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    let targetId = form.id;
    if (!targetId) {
      if (!canSave) {
        setError(copy.submit.validation);
        return;
      }
      const saved = await persist("manual");
      if (!saved) return;
      targetId = saved.id;
    }
    try {
      await attachmentMutation.mutateAsync({ id: targetId, file });
      setMessage(copy.submit.attachmentSaved);
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : copy.state.networkBody);
    }
  }

  return (
    <div className="space-y-6">
      <section className="product-card relative overflow-hidden rounded-app p-5 sm:p-7">
        <div className="subtle-grid pointer-events-none absolute inset-0 opacity-20" />
        <div className="relative flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-2xl"><span className="inline-flex items-center gap-2 font-data text-[10px] uppercase tracking-[0.14em] text-brand-strong"><Sparkles className="h-3.5 w-3.5" />Knowledge authoring</span><PageHeader title={copy.nav.submit} description={headerDescription ?? "Document the problem, the reasoning behind the fix, and the engineer who can help others apply it."} /></div>
          <div className="relative w-full max-w-sm rounded-control border border-border bg-surface p-4 shadow-sm"><div className="flex items-center justify-between text-xs"><span className="font-medium text-text">Entry completeness</span><span className="font-data font-semibold text-brand-strong">{completion}%</span></div><div className="mt-3 h-1.5 overflow-hidden rounded-full bg-muted"><div className="h-full rounded-full bg-gradient-to-r from-warning via-primary to-success transition-[width] duration-220" style={{ width: `${completion}%` }} /></div><p className="mt-2 text-[11px] text-text-muted">Complete the technical context before submitting for review.</p></div>
        </div>
      </section>
      {hasSecretWarning && <Notice tone="warning" text={copy.submit.secretWarning} />}
      {error && <Notice tone="error" text={error} />}
      <div className="grid gap-6 xl:grid-cols-[230px_minmax(0,1fr)_260px]">
        <aside className="product-card h-fit rounded-app p-3 xl:sticky xl:top-[96px]">
          <div className="px-3 pb-3"><p className="font-data text-[10px] uppercase tracking-[0.14em] text-text-muted">Sections</p><p className="mt-1 text-xs text-text-muted">Move between sections without losing your draft.</p></div>
          {steps.map((label, index) => (
            <button className={`pressable mb-1 flex min-h-11 w-full items-center gap-3 rounded-control px-3 text-left text-sm transition-colors ${index === step ? "bg-brand-soft font-semibold text-brand-strong shadow-sm" : "text-text-muted hover:bg-surface-muted hover:text-text"}`} key={label} onClick={() => setStep(index)}>
              <span className={`grid h-6 w-6 shrink-0 place-items-center rounded-full border font-data text-[10px] font-semibold ${index < step ? "border-primary bg-primary text-primary-foreground" : index === step ? "border-primary/30 bg-surface text-brand-strong" : "border-border bg-surface"}`}>{index < step ? <Check className="h-3.5 w-3.5" /> : index + 1}</span><span>{label}</span>
            </button>
          ))}
        </aside>
        <form className="product-card min-w-0 rounded-app p-5 sm:p-7" onSubmit={(event) => event.preventDefault()}>
          <div className="mb-6 border-b border-border pb-5"><p className="font-data text-[10px] uppercase tracking-[0.14em] text-brand-strong">Step {step + 1} of {steps.length}</p><h2 className="mt-1 font-display text-lg font-semibold tracking-[-0.01em] text-text">{steps[step]}</h2></div>
          {step === 0 && <Fields><TextInput label={copy.submit.titleLabel} required value={form.title} onChange={(title) => update("title", title)} /><TextArea label={copy.submit.problemLabel} value={form.problemDescription} onChange={(value) => update("problemDescription", value)} rows={6} /><TextArea label={copy.submit.environmentLabel} value={form.environment} onChange={(value) => update("environment", value)} rows={4} /><TextArea label={copy.submit.symptomsLabel} value={form.symptoms} onChange={(value) => update("symptoms", value)} rows={5} /><TextArea label={copy.submit.errorLabel} value={form.exactErrorMessage} onChange={(value) => update("exactErrorMessage", value)} rows={4} code /></Fields>}
          {step === 1 && <Fields><TextArea label={copy.submit.rootCauseLabel} value={form.rootCause} onChange={(value) => update("rootCause", value)} rows={7} /><fieldset><legend className="text-sm font-semibold">{copy.submit.technologiesLabel}</legend><div className="mt-3 flex max-h-64 flex-wrap gap-2 overflow-auto rounded-app border border-border bg-surface-muted/30 p-3">{technologies.data?.map((technology) => <label className="inline-flex min-h-9 items-center gap-2 rounded-control border border-border bg-surface px-3 text-sm" key={technology.id}><input checked={form.technologyIds.includes(technology.id)} onChange={() => toggleTechnology(technology.id)} type="checkbox" />{technology.name}</label>)}</div></fieldset><label className="block text-sm font-semibold" htmlFor="visibility">{copy.submit.visibilityLabel}<select className="mt-2 h-10 w-full rounded-control border border-border bg-surface px-2 text-sm" id="visibility" value={form.visibility} onChange={(event) => update("visibility", event.target.value as FormState["visibility"])}><option value="company">Company</option><option value="department">Department</option><option value="team">Team</option><option value="restricted">Restricted</option></select></label></Fields>}
          {step === 2 && <Fields><TextArea label={copy.submit.stepsLabel} value={form.resolutionSteps} onChange={(value) => update("resolutionSteps", value)} rows={9} /><TextArea label={copy.submit.preventionLabel} value={form.preventionNotes} onChange={(value) => update("preventionNotes", value)} rows={4} /><TextArea label={copy.submit.codeLabel} value={form.codeSnippets} onChange={(value) => update("codeSnippets", value)} rows={8} code /><label className="inline-flex h-9 cursor-pointer items-center gap-2 rounded-control border border-border px-3 text-sm font-medium hover:bg-surface-muted"><Upload className="h-4 w-4" aria-hidden="true" />{copy.submit.uploadAttachment}<input className="sr-only" type="file" onChange={upload} /></label></Fields>}
          {step === 3 && <Review form={form} canSubmit={Boolean(canSubmit)} />}
          <div className="mt-8 flex flex-wrap items-center justify-between gap-3 border-t border-border pt-5">
            <div className="flex gap-2"><Button disabled={step === 0} onClick={() => setStep((value) => Math.max(0, value - 1))}>{copy.action.back}</Button><Button disabled={step === steps.length - 1} onClick={() => setStep((value) => Math.min(steps.length - 1, value + 1))}>{copy.action.next}</Button></div>
            <div className="flex gap-2"><Button disabled={!canSave || saveMutation.isPending} onClick={() => void persist("manual")}><Save className="h-4 w-4" />{saveMutation.isPending ? copy.submit.saving : copy.action.saveDraft}</Button><Button disabled={!canSubmit || submitMutation.isPending} onClick={() => void submitForReview()} variant="primary"><FileCheck2 className="h-4 w-4" />{copy.action.submitReview}</Button></div>
          </div>
        </form>
        <aside className="h-fit space-y-4 xl:sticky xl:top-[96px]">
          <section className="product-card rounded-app p-4"><div className="relative flex items-center gap-2 font-display text-sm font-semibold"><Save className="h-4 w-4 text-brand-strong" />Draft status</div><p className="relative mt-3 text-sm text-text-muted">{saveMutation.isPending ? copy.submit.saving : dirty ? copy.submit.unsaved : form.id ? copy.submit.saved : "Not saved yet"}</p>{form.expectedUpdatedAt && <p className="relative mt-2 font-data text-[10px] text-text-muted">Server version: {new Date(form.expectedUpdatedAt).toLocaleTimeString()}</p>}</section>
          <section className="product-card rounded-app p-4"><div className="relative flex items-center gap-2 font-display text-sm font-semibold"><ShieldCheck className="h-4 w-4 text-brand-strong" />Before you submit</div><ul className="relative mt-3 space-y-2 text-xs leading-5 text-text-muted"><CheckItem done={Boolean(form.problemDescription.trim())} text="Problem is clearly described" /><CheckItem done={Boolean(form.symptoms.trim())} text="Symptoms or error are captured" /><CheckItem done={Boolean(form.rootCause.trim())} text="Root cause is documented" /><CheckItem done={Boolean(form.resolutionSteps.trim())} text="Resolution steps are reusable" /><CheckItem done={Boolean(form.preventionNotes.trim())} text="Prevention guidance is included" /><CheckItem done={!hasSecretWarning} text="No obvious secret is present" /></ul></section>
        </aside>
      </div>
    </div>
  );

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    editVersionRef.current += 1;
    setForm((current) => ({ ...current, [key]: value }));
    setDirty(true);
  }

  function toggleTechnology(technologyId: string) {
    const selected = form.technologyIds.includes(technologyId)
      ? form.technologyIds.filter((id) => id !== technologyId)
      : [...form.technologyIds, technologyId];
    update("technologyIds", selected);
  }

  async function saveDraft(snapshot: FormState) {
    const payload = toPayload(snapshot);
    if (snapshot.id && snapshot.expectedUpdatedAt) {
      return updateChallenge(snapshot.id, { ...payload, expected_updated_at: snapshot.expectedUpdatedAt });
    }
    return createChallenge(payload);
  }
}

function fromChallenge(challenge: ChallengeDetail): FormState {
  return {
    id: challenge.id,
    expectedUpdatedAt: challenge.updated_at,
    title: challenge.title,
    problemDescription: challenge.problem_description,
    environment: challenge.environment ?? "",
    symptoms: challenge.symptoms,
    exactErrorMessage: challenge.exact_error_message ?? "",
    rootCause: challenge.solution.root_cause,
    resolutionSteps: challenge.solution.resolution_steps.join("\n"),
    codeSnippets: challenge.solution.code_snippets.join("\n---\n"),
    preventionNotes: challenge.solution.prevention_notes ?? "",
    technologyIds: challenge.technology_ids,
    visibility: challenge.visibility as FormState["visibility"],
  };
}

function toPayload(form: FormState) {
  return {
    title: form.title,
    problem_description: form.problemDescription,
    symptoms: form.symptoms,
    exact_error_message: form.exactErrorMessage || null,
    environment: form.environment || null,
    visibility: form.visibility,
    technology_ids: form.technologyIds,
    solution: {
      root_cause: form.rootCause,
      resolution_steps: form.resolutionSteps.split("\n").map((item) => item.trim()).filter(Boolean),
      code_snippets: form.codeSnippets.split("\n---\n").map((item) => item.trim()).filter(Boolean),
      prevention_notes: form.preventionNotes.trim() || null,
      solved_at: null,
    },
  };
}

function Fields({ children }: { children: ReactNode }) {
  return <div className="space-y-5">{children}</div>;
}

function TextInput({ label, value, onChange, required = false }: { label: string; value: string; required?: boolean; onChange: (value: string) => void }) {
  return <label className="block text-sm font-semibold">{label}<input className="mt-2 h-11 w-full rounded-app border border-input bg-surface px-3 text-sm text-text outline-none transition-all duration-160 hover:border-border-strong focus:border-accent focus:shadow-focus" required={required} value={value} onChange={(event) => onChange(event.target.value)} /></label>;
}

function TextArea({ label, value, onChange, rows, code = false }: { label: string; value: string; rows: number; code?: boolean; onChange: (value: string) => void }) {
  return <label className="block text-sm font-semibold">{label}<textarea className={`mt-2 w-full rounded-app border border-input bg-surface p-3.5 text-sm leading-6 text-text outline-none transition-all duration-160 hover:border-border-strong focus:border-accent focus:shadow-focus ${code ? "font-mono" : ""}`} rows={rows} value={value} onChange={(event) => onChange(event.target.value)} /></label>;
}

function Review({ form, canSubmit }: { form: FormState; canSubmit: boolean }) {
  return <section className="space-y-4"><p className="text-sm text-text-muted">{copy.submit.reviewReady}</p><ReviewItem label={copy.submit.titleLabel} value={form.title} /><ReviewItem label={copy.submit.problemLabel} value={form.problemDescription} /><ReviewItem label={copy.submit.rootCauseLabel} value={form.rootCause} /><ReviewItem label={copy.submit.stepsLabel} value={form.resolutionSteps} /><ReviewItem label={copy.submit.preventionLabel} value={form.preventionNotes} />{!canSubmit && <p className="text-sm text-warning">{copy.submit.validation}</p>}</section>;
}

function ReviewItem({ label, value }: { label: string; value: string }) {
  return <div><h3 className="text-sm font-semibold">{label}</h3><p className="mt-1 whitespace-pre-wrap text-sm leading-6 text-text-muted">{value || "-"}</p></div>;
}

function Notice({ tone, text }: { tone: "warning" | "error"; text: string }) {
  const Icon = tone === "warning" ? AlertTriangle : CheckCircle2;
  return <div className={`flex items-center gap-2 rounded-app border p-3 text-sm ${tone === "warning" ? "border-warning/30 bg-warning/5 text-warning" : "border-danger/30 bg-danger/5 text-danger"}`}><Icon className="h-4 w-4" aria-hidden="true" />{text}</div>;
}

function CheckItem({ done, text }: { done: boolean; text: string }) {
  return <li className="flex items-start gap-2"><span className={`mt-0.5 grid h-4 w-4 shrink-0 place-items-center rounded-full ${done ? "bg-success text-primary-foreground" : "border border-border bg-surface"}`}>{done && <Check className="h-3 w-3" />}</span><span className={done ? "text-text" : "text-text-muted"}>{text}</span></li>;
}
