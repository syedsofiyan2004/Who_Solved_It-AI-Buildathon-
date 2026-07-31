import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowUpRight, BadgeCheck, Mail, Pencil, Save, UserRound, X } from "lucide-react";
import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { useAuth } from "../auth/AuthProvider";
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";
import { StatePanel } from "../components/ui/StatePanel";
import { copy } from "../content/uiCopy";
import { getEmployeeProfile, updateMyProfile, type EmployeeProfile } from "../services/api";

type ProfileForm = {
  display_name: string;
  job_title: string;
  contact_email: string;
  contact_handle: string;
  bio: string;
  skills: string;
};

export function ProfilePage() {
  const { userId = "me" } = useParams();
  const navigate = useNavigate();
  const { refreshUser, user } = useAuth();
  const queryClient = useQueryClient();
  const profile = useQuery({ queryKey: ["employee-profile", userId], queryFn: () => getEmployeeProfile(userId), staleTime: 5 * 60 * 1000 });
  const [editing, setEditing] = useState(false);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);
  const canEdit = userId === "me" || (profile.data && user?.id === profile.data.user_id);
  const updateMutation = useMutation({
    mutationFn: updateMyProfile,
    onSuccess: async (updated) => {
      queryClient.setQueryData(["employee-profile", userId], updated);
      queryClient.setQueryData(["employee-profile", "me"], updated);
      queryClient.setQueryData(["employee-profile", updated.user_id], updated);
      await queryClient.invalidateQueries({ queryKey: ["employee-directory"] });
      await refreshUser();
      setEditing(false);
      setSavedMessage(copy.profile.profileSaved);
    },
  });

  if (profile.isLoading) return <LoadingSkeleton rows={7} />;
  if (profile.isError) return <StatePanel kind="error" onRetry={() => void profile.refetch()} />;
  if (!profile.data) return <StatePanel kind="notFound" />;

  const item = profile.data;
  return (
    <div className="space-y-5">
      <button className="pressable inline-flex items-center gap-2 rounded-control px-2 py-1 text-sm font-medium text-text-muted hover:bg-surface-muted hover:text-text" onClick={() => navigate(-1)} type="button"><ArrowLeft className="h-4 w-4" />Back to workspace</button>

      <section className="product-card relative overflow-hidden rounded-[14px] p-6 sm:p-8">
        <div className="subtle-grid pointer-events-none absolute inset-0 opacity-20" />
        <div className="relative flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex min-w-0 items-start gap-5">
            <div className="grid h-20 w-20 shrink-0 place-items-center rounded-[14px] border border-primary/20 bg-brand-soft font-data text-2xl font-semibold text-brand-strong shadow-sm">
              {item.avatar_key ? <UserRound className="h-8 w-8" aria-hidden="true" /> : item.initials}
            </div>
            <div className="min-w-0 pt-1">
              <div className="flex flex-wrap items-center gap-2"><span className="font-data text-[10px] uppercase tracking-[0.14em] text-brand-strong">Employee profile</span><span className="status-chip inline-flex items-center gap-1 rounded-control bg-success/10 px-2 py-1 uppercase text-success"><BadgeCheck className="h-3 w-3" />Internal expert</span></div>
              <h1 className="mt-2 break-words font-display text-2xl font-semibold tracking-[-0.015em] text-text sm:text-3xl">{item.display_name}</h1>
              <p className="mt-1 text-sm text-text-muted">{item.job_title}</p>
              <p className="mt-2 text-xs text-text-muted">{item.team} &middot; {item.department}</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {canEdit && <button className="pressable inline-flex h-10 items-center justify-center gap-2 rounded-control border border-border bg-surface px-4 text-sm font-medium text-text hover:bg-surface-muted hover:shadow-sm" onClick={() => { setSavedMessage(null); setEditing((value) => !value); }} type="button">{editing ? <X className="h-4 w-4" /> : <Pencil className="h-4 w-4" />}{editing ? copy.action.cancel : copy.action.editProfile}</button>}
            <a className="pressable inline-flex h-10 items-center justify-center gap-2 rounded-control border border-primary bg-primary px-4 text-sm font-medium text-primary-foreground shadow-sm hover:bg-accent-hover hover:shadow-soft" href={`mailto:${item.contact_email}`}><Mail className="h-4 w-4" />{copy.action.contactSolver}</a>
          </div>
        </div>
      </section>
      {savedMessage && <p className="rounded-control border border-success/25 bg-success/10 px-3 py-2 text-sm text-success">{savedMessage}</p>}
      {editing && <ProfileEditor error={updateMutation.error instanceof Error ? updateMutation.error.message : null} isSaving={updateMutation.isPending} profile={item} onCancel={() => setEditing(false)} onSave={(payload) => updateMutation.mutate(payload)} />}

      <div className="grid gap-6 xl:grid-cols-[320px_minmax(0,1fr)] xl:items-start">
        <aside className="space-y-4 xl:sticky xl:top-[96px]">
          <section className="product-card rounded-[12px] p-5">
            <h2 className="font-display text-sm font-semibold">About</h2>
            <p className="mt-3 text-sm leading-7 text-text-muted">{item.bio || `${item.display_name} contributes technical knowledge across ${item.team}.`}</p>
            <dl className="mt-5 space-y-4 border-t border-border pt-4 text-sm">
              <Meta label={copy.profile.department} value={item.department} />
              <Meta label={copy.profile.team} value={item.team} />
              <Meta label={copy.profile.contact} value={item.contact_handle || item.contact_email} />
            </dl>
          </section>
          <section className="grid grid-cols-2 gap-3">
            <Metric label={copy.profile.contributions} value={item.contribution_count} />
            <Metric label={copy.profile.helpful} value={item.helpful_contribution_count ?? 0} />
          </section>
        </aside>

        <main className="min-w-0 space-y-5">
          <section className="product-card rounded-[12px] p-5 sm:p-6">
            <div className="grid gap-6 lg:grid-cols-2">
              <TagSection title={copy.profile.skills} empty={copy.profile.emptySkills} values={item.skills} accent />
              <TagSection title={copy.profile.technologies} empty={copy.profile.emptyTags} values={item.technologies} />
            </div>
          </section>

          <section className="product-card rounded-[12px] p-5 sm:p-6">
            <div className="flex flex-wrap items-center justify-between gap-3"><div><p className="font-data text-[10px] uppercase tracking-[0.14em] text-brand-strong">Knowledge contributions</p><h2 className="mt-1 font-display text-lg font-semibold tracking-[-0.01em]">{copy.profile.verifiedSolutions}</h2></div><span className="status-chip rounded-control bg-brand-soft px-2.5 py-1 text-brand-strong">{item.verified_solutions.length}</span></div>
            {item.verified_solutions.length === 0 ? <p className="mt-5 rounded-[10px] border border-dashed border-border bg-surface-muted/40 p-5 text-sm text-text-muted">{copy.profile.emptySolutions}</p> : <div className="mt-5 grid gap-3 lg:grid-cols-2">{item.verified_solutions.map((solution) => <Link className="ledger-row group relative overflow-hidden rounded-[10px] p-4" key={solution.solution_id} to={`/solutions/${solution.challenge_id}`}><span className="ledger-rail bg-success" /><div className="flex items-start justify-between gap-3 pl-1"><h3 className="text-sm font-semibold leading-6 text-text group-hover:text-brand-strong">{solution.title}</h3><ArrowUpRight className="mt-0.5 h-4 w-4 shrink-0 text-text-muted" /></div><div className="mt-4 flex flex-wrap gap-2 pl-1">{solution.technologies.map((technology) => <span className="rounded-control border border-border px-2.5 py-1 text-[10px] font-medium text-text-muted" key={technology}>{technology}</span>)}</div><div className="mt-4 flex items-center justify-between pl-1 font-data text-[10px] text-text-muted"><span className="uppercase">{solution.visibility}</span><span>{new Date(solution.updated_at).toLocaleDateString()}</span></div></Link>)}</div>}
          </section>
        </main>
      </div>
    </div>
  );
}

function ProfileEditor({ error, isSaving, onCancel, onSave, profile }: { error: string | null; isSaving: boolean; profile: EmployeeProfile; onCancel: () => void; onSave: (payload: { display_name: string; job_title: string; contact_email: string; contact_handle: string | null; bio: string | null; skills: string[] }) => void }) {
  const [form, setForm] = useState<ProfileForm>(() => fromProfile(profile));

  useEffect(() => {
    setForm(fromProfile(profile));
  }, [profile]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const skills = form.skills.split(",").map((skill) => skill.trim()).filter(Boolean);
    onSave({
      display_name: form.display_name.trim(),
      job_title: form.job_title.trim(),
      contact_email: form.contact_email.trim().toLowerCase(),
      contact_handle: form.contact_handle.trim() || null,
      bio: form.bio.trim() || null,
      skills,
    });
  }

  return (
    <form className="product-card rounded-[12px] p-5 sm:p-6" onSubmit={submit}>
      <div className="flex flex-col gap-2 border-b border-border pb-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="font-display text-base font-semibold">{copy.action.editProfile}</h2>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-text-muted">{copy.profile.editHint}</p>
        </div>
        <div className="flex gap-2">
          <button className="pressable inline-flex h-9 items-center justify-center rounded-control border border-border px-3 text-sm font-medium hover:bg-surface-muted" disabled={isSaving} onClick={onCancel} type="button">{copy.action.cancel}</button>
          <button className="pressable inline-flex h-9 items-center justify-center gap-2 rounded-control border border-primary bg-primary px-3 text-sm font-medium text-primary-foreground hover:bg-accent-hover disabled:opacity-60" disabled={isSaving || !form.display_name.trim() || !form.job_title.trim() || !form.contact_email.trim()} type="submit"><Save className="h-4 w-4" />{isSaving ? copy.submit.saving : copy.action.saveProfile}</button>
        </div>
      </div>
      {error && <p className="mt-4 rounded-control border border-danger/25 bg-danger/5 px-3 py-2 text-sm text-danger">{error}</p>}
      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <TextField label={copy.profile.displayName} required value={form.display_name} onChange={(display_name) => setForm((current) => ({ ...current, display_name }))} />
        <TextField label={copy.profile.jobTitle} required value={form.job_title} onChange={(job_title) => setForm((current) => ({ ...current, job_title }))} />
        <TextField label={copy.profile.workEmail} required type="email" value={form.contact_email} onChange={(contact_email) => setForm((current) => ({ ...current, contact_email }))} />
        <TextField label={copy.profile.contactHandle} value={form.contact_handle} onChange={(contact_handle) => setForm((current) => ({ ...current, contact_handle }))} />
        <TextField help={copy.profile.skillsHelp} label={copy.profile.skills} value={form.skills} onChange={(skills) => setForm((current) => ({ ...current, skills }))} />
        <label className="block text-sm font-semibold lg:col-span-2">{copy.profile.bio}<textarea className="mt-2 min-h-28 w-full rounded-app border border-input bg-surface p-3 text-sm leading-6 text-text outline-none transition focus:border-accent focus:shadow-focus" value={form.bio} onChange={(event) => setForm((current) => ({ ...current, bio: event.target.value }))} /></label>
      </div>
    </form>
  );
}

function fromProfile(profile: EmployeeProfile): ProfileForm {
  return {
    display_name: profile.display_name,
    job_title: profile.job_title,
    contact_email: profile.contact_email,
    contact_handle: profile.contact_handle ?? "",
    bio: profile.bio ?? "",
    skills: profile.skills.join(", "),
  };
}

function TextField({ help, label, onChange, required = false, type = "text", value }: { help?: string; label: string; required?: boolean; type?: "email" | "text"; value: string; onChange: (value: string) => void }) {
  return <label className="block text-sm font-semibold">{label}<input className="mt-2 h-10 w-full rounded-control border border-input bg-surface px-3 text-sm text-text outline-none transition focus:border-accent focus:shadow-focus" required={required} type={type} value={value} onChange={(event) => onChange(event.target.value)} />{help && <span className="mt-1 block text-xs font-normal text-text-muted">{help}</span>}</label>;
}

function Meta({ label, value }: { label: string; value: string }) {
  return <div><dt className="font-data text-[10px] uppercase tracking-[0.12em] text-text-muted">{label}</dt><dd className="mt-1 font-medium text-text">{value}</dd></div>;
}

function Metric({ label, value }: { label: string; value: number }) {
  return <div className="product-card interactive-lift rounded-[10px] p-4"><p className="relative font-display text-2xl font-semibold tracking-[-0.01em] text-text">{value}</p><p className="relative mt-1 text-[11px] text-text-muted">{label}</p></div>;
}

function TagSection({ title, empty, values, accent = false }: { title: string; empty: string; values: string[]; accent?: boolean }) {
  return <section><h2 className="font-display text-sm font-semibold">{title}</h2>{values.length === 0 ? <p className="mt-3 text-sm text-text-muted">{empty}</p> : <div className="mt-3 flex flex-wrap gap-2">{values.map((value) => <span className={`rounded-control px-2.5 py-1 text-[11px] font-medium ${accent ? "bg-brand-soft text-brand-strong" : "border border-border bg-surface text-text-muted"}`} key={value}>{value}</span>)}</div>}</section>;
}
