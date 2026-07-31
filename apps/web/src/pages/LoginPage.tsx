import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, CheckCircle2, Search, ShieldCheck, Sparkles, UserRound } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useLocation, useNavigate } from "react-router-dom";
import { z } from "zod";

import { useAuth } from "../auth/AuthProvider";
import { BrandMark } from "../components/product/BrandMark";
import { Button } from "../components/ui/Button";
import { copy } from "../content/uiCopy";

const loginSchema = z.object({
  email: z.string().email(copy.login.emailInvalid),
  password: z.string().min(8, copy.login.passwordInvalid).max(128, copy.login.passwordInvalid),
});
type LoginFormValues = z.infer<typeof loginSchema>;

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [error, setError] = useState<string | null>(null);
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = async (values: LoginFormValues) => {
    setError(null);
    try {
      await login(values);
      const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
      navigate(from ?? "/", { replace: true });
    } catch {
      setError(copy.login.invalid);
    }
  };

  return (
    <main className="relative min-h-screen overflow-hidden bg-canvas px-4 py-5 text-text sm:px-6 lg:px-8">
      <div className="subtle-grid pointer-events-none absolute inset-0 opacity-45" />
      <section className="relative mx-auto grid min-h-[calc(100vh-2.5rem)] w-full max-w-[1240px] overflow-hidden rounded-[18px] border border-border bg-surface/95 shadow-overlay lg:grid-cols-[minmax(0,1.25fr)_440px]">
        <div className="relative flex flex-col justify-between overflow-hidden border-b border-border p-6 sm:p-10 lg:border-b-0 lg:border-r lg:p-14">
          <BrandMark />
          <div className="relative my-12 max-w-2xl lg:my-16">
            <span className="inline-flex items-center gap-2 font-data text-[11px] uppercase tracking-[0.14em] text-brand-strong">
              <Sparkles className="h-3.5 w-3.5" aria-hidden="true" /> Internal engineering intelligence
            </span>
            <h1 className="mt-6 font-display text-4xl font-semibold leading-[1.1] tracking-[-0.02em] sm:text-5xl">{copy.login.statement}</h1>
            <p className="mt-5 max-w-xl text-base leading-7 text-text-muted">{copy.login.description}</p>
            <div className="mt-9 grid gap-3 sm:grid-cols-3">
              <ValuePoint title="Search" body="Find verified fixes using errors, technology, and technical context." />
              <ValuePoint title="Understand" body="See the root cause, exact steps, and evidence that worked." />
              <ValuePoint title="Connect" body="Reach the engineer who solved the issue before." />
            </div>
          </div>
          <ProductPreview />
        </div>

        <div className="flex items-center p-6 sm:p-10">
          <form className="w-full" onSubmit={handleSubmit(onSubmit)} noValidate>
            <div className="mb-8">
              <span className="grid h-11 w-11 place-items-center rounded-control border border-primary/20 bg-brand-soft text-brand-strong"><ShieldCheck className="h-5 w-5" aria-hidden="true" /></span>
              <h2 className="mt-5 font-display text-2xl font-semibold tracking-[-0.015em]">{copy.login.title}</h2>
              <p className="mt-2 text-sm leading-6 text-text-muted">{copy.login.accessIntro}</p>
            </div>

            <label className="block text-sm font-medium" htmlFor="email">
              {copy.login.email}
              <input id="email" type="email" autoComplete="email" className="mt-2 block h-11 w-full rounded-control border border-input bg-surface px-3.5 text-sm text-text shadow-sm outline-none transition focus:border-accent focus:shadow-focus" aria-invalid={Boolean(errors.email)} aria-describedby={errors.email ? "email-error" : undefined} {...register("email")} />
            </label>
            {errors.email && <p id="email-error" className="mt-2 text-sm text-danger">{errors.email.message}</p>}

            <label className="mt-5 block text-sm font-medium" htmlFor="password">
              {copy.login.password}
              <input id="password" type="password" autoComplete="current-password" className="mt-2 block h-11 w-full rounded-control border border-input bg-surface px-3.5 text-sm text-text shadow-sm outline-none transition focus:border-accent focus:shadow-focus" aria-invalid={Boolean(errors.password)} aria-describedby={errors.password ? "password-error" : undefined} {...register("password")} />
            </label>
            {errors.password && <p id="password-error" className="mt-2 text-sm text-danger">{errors.password.message}</p>}
            {error && <p className="mt-4 rounded-control border border-danger/25 bg-danger/5 px-3 py-2.5 text-sm text-danger" role="alert">{error}</p>}

            <Button className="mt-6 h-11 w-full" disabled={isSubmitting} type="submit" variant="primary">
              {isSubmitting ? copy.login.submitting : copy.login.submit}<ArrowRight className="h-4 w-4" />
            </Button>

            <p className="mt-5 rounded-control border border-border bg-surface-muted/50 px-3 py-2.5 text-xs leading-5 text-text-muted">{copy.login.accessNote}</p>
          </form>
        </div>
      </section>
    </main>
  );
}

function ValuePoint({ body, title }: { body: string; title: string }) {
  return <div className="rounded-[10px] border border-border bg-surface/70 p-3.5"><CheckCircle2 className="h-4 w-4 text-brand-strong" /><p className="mt-3 text-sm font-semibold">{title}</p><p className="mt-1 text-xs leading-5 text-text-muted">{body}</p></div>;
}

function ProductPreview() {
  return (
    <div className="relative overflow-hidden rounded-[12px] border border-border bg-elevated/95 p-4 shadow-soft sm:p-5">
      <div className="flex items-center gap-3 border-b border-border pb-4">
        <span className="grid h-9 w-9 place-items-center rounded-control bg-brand-soft text-brand-strong"><Search className="h-4 w-4" /></span>
        <div className="min-w-0"><p className="truncate text-sm font-medium">ModuleNotFoundError after Docker deployment</p><p className="mt-1 font-data text-[11px] text-text-muted">3 verified matches &middot; 2 relevant engineers</p></div>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-[minmax(0,1fr)_180px]">
        <div className="ledger-row relative overflow-hidden rounded-[10px] p-4">
          <span className="ledger-rail bg-success" />
          <div className="flex items-center justify-between gap-2 pl-1"><span className="status-chip inline-flex items-center gap-1 uppercase text-success"><CheckCircle2 className="h-3.5 w-3.5" />Verified</span><span className="status-chip rounded-control bg-brand-soft px-2 py-1 text-brand-strong">94% match</span></div>
          <p className="mt-3 pl-1 text-sm font-semibold">Container copied the package outside Python's module path</p>
          <p className="mt-2 pl-1 text-xs leading-5 text-text-muted">Correct the final-stage COPY path, rebuild the image, and verify imports in a clean container.</p>
        </div>
        <div className="rounded-[10px] border border-border bg-surface p-4">
          <span className="grid h-9 w-9 place-items-center rounded-full bg-brand-soft font-data text-xs font-semibold text-brand-strong">EX</span>
          <p className="mt-3 text-sm font-semibold">Verified solution owner</p>
          <p className="mt-1 text-xs leading-5 text-text-muted">Approved contact details come from the employee profile.</p>
          <span className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-brand-strong"><UserRound className="h-3.5 w-3.5" />View expert</span>
        </div>
      </div>
    </div>
  );
}
