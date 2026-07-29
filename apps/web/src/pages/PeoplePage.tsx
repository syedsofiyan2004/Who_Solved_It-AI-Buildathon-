import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, Mail, Search, UsersRound } from "lucide-react";
import { useDeferredValue, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";
import { StatePanel } from "../components/ui/StatePanel";
import { listEmployeeProfiles } from "../services/api";

export function PeoplePage() {
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query);
  const profiles = useQuery({ queryKey: ["employee-directory", deferredQuery], queryFn: () => listEmployeeProfiles(deferredQuery), staleTime: 5 * 60 * 1000 });
  const groupedProfiles = useMemo(() => {
    const rows = profiles.data?.data ?? [];
    return rows.reduce<Record<string, typeof rows>>((groups, profile) => {
      const key = profile.department || "Other";
      return { ...groups, [key]: [...(groups[key] ?? []), profile] };
    }, {});
  }, [profiles.data]);

  return (
    <div className="space-y-6">
      <section className="product-card relative overflow-hidden rounded-[24px] p-6 sm:p-8">
        <div className="absolute -right-20 -top-24 h-64 w-64 rounded-full bg-primary/10 blur-3xl" />
        <div className="subtle-grid pointer-events-none absolute inset-0 opacity-25" />
        <div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div><span className="inline-flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-brand-strong"><UsersRound className="h-3.5 w-3.5" />Expert directory</span><h1 className="mt-2 text-2xl font-semibold tracking-[-0.035em] text-text sm:text-3xl">Find the person behind the solution</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-text-muted">Search by name, role, team, or department and open the expert record connected to verified solutions.</p></div>
          <div className="relative w-full max-w-md"><Search className="absolute left-3.5 top-3.5 h-4 w-4 text-text-muted" /><input className="h-11 w-full rounded-app border border-input bg-surface pl-10 pr-3 text-sm outline-none transition-all duration-160 hover:border-border-strong focus:border-accent focus:shadow-focus" onChange={(event) => setQuery(event.target.value)} placeholder="Search by name, role, team, or department" value={query} /></div>
        </div>
      </section>

      {profiles.isLoading && <LoadingSkeleton rows={8} />}
      {profiles.isError && <StatePanel kind="error" onRetry={() => void profiles.refetch()} />}
      {profiles.data && <>
        <div className="flex items-center justify-between"><p className="text-sm text-text-muted"><span className="font-semibold text-text">{profiles.data.meta.total}</span> people available</p></div>
        {profiles.data.data.length === 0 ? <section className="product-card rounded-[20px] p-10 text-center"><h2 className="text-lg font-semibold">No people match that search</h2><p className="mt-2 text-sm text-text-muted">Try a department, technology, or shorter name.</p></section> : <div className="space-y-5">{Object.entries(groupedProfiles).map(([department, rows]) => <section className="product-card overflow-hidden rounded-[20px]" key={department}><div className="flex items-center justify-between border-b border-border px-4 py-3"><div><h2 className="text-sm font-semibold">{department}</h2><p className="mt-0.5 text-xs text-text-muted">{rows.length} {rows.length === 1 ? "person" : "people"}</p></div><span className="rounded-full bg-brand-soft px-2.5 py-1 text-[10px] font-semibold text-brand-strong">{rows[0]?.team}</span></div><div className="divide-y divide-border">{rows.map((profile) => <article className="group grid gap-4 px-4 py-4 transition hover:bg-surface-muted/70 lg:grid-cols-[minmax(220px,0.8fr)_minmax(0,1fr)_190px] lg:items-center" key={profile.user_id}><div className="flex min-w-0 items-center gap-3"><div className="grid h-11 w-11 shrink-0 place-items-center rounded-[14px] border border-primary/20 bg-brand-soft text-sm font-semibold text-brand-strong transition-transform group-hover:scale-105">{profile.initials}</div><div className="min-w-0"><h3 className="truncate text-sm font-semibold text-text group-hover:text-brand-strong">{profile.display_name}</h3><p className="mt-1 line-clamp-1 text-xs text-text-muted">{profile.job_title}</p></div></div><div className="flex min-w-0 flex-wrap gap-2">{profile.skills.slice(0, 5).map((skill) => <span className="rounded-full border border-border bg-surface px-2.5 py-1 text-[10px] font-medium text-text-muted" key={skill}>{skill}</span>)}</div><div className="flex gap-2 lg:justify-end"><a aria-label={`Email ${profile.display_name}`} className="pressable grid h-9 w-9 place-items-center rounded-control border border-border text-text-muted hover:bg-surface hover:text-text hover:shadow-sm" href={`mailto:${profile.contact_email}`}><Mail className="h-4 w-4" /></a><Link className="pressable inline-flex h-9 items-center justify-center gap-2 rounded-control border border-primary/25 bg-brand-soft px-3 text-sm font-medium text-brand-strong hover:bg-primary/10 hover:shadow-sm" to={`/people/${profile.user_id}`}>View profile<ArrowUpRight className="h-4 w-4" /></Link></div></article>)}</div></section>)}</div>}
      </>}
    </div>
  );
}
