import type { ReactNode } from "react";

export function PageHeader({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return <header className="flex flex-col gap-4 border-b border-border pb-5 sm:flex-row sm:items-start sm:justify-between"><div><h1 className="font-display text-xl font-semibold tracking-[-0.005em] text-text">{title}</h1>{description && <p className="mt-1 max-w-2xl text-sm leading-6 text-text-muted">{description}</p>}</div>{action}</header>;
}
