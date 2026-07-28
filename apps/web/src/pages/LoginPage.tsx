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

const demoAccounts = [
  { label: "Syed Sofiyan", email: "syed.sofiyan@minfytech.com", context: "Cloud delivery workspace" },
  { label: "Srikar Deshmukh", email: "srikar.deshmukh@minfytech.com", context: "Review queue workspace" },
  { label: "Anant Joshi", email: "anant.joshi@minfytech.com", context: "Administration workspace" },
];

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [error, setError] = useState<string | null>(null);
  const { register, handleSubmit, setValue, formState: { errors, isSubmitting } } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "syed.sofiyan@minfytech.com", password: "development-only-password" },
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

  const fillAccount = (email: string) => {
    setValue("email", email, { shouldValidate: true });
    setValue("password", "development-only-password", { shouldValidate: true });
  };

  return (
    <main className="relative min-h-screen overflow-hidden bg-canvas px-4 py-5 text-text sm:px-6 lg:px-8">
      <div className="subtle-grid pointer-events-none absolute inset-0 opacity-45" />
      <section className="relative mx-auto grid min-h-[calc(100vh-2.5rem)] w-full max-w-[1240px] overflow-hidden rounded-[24px] border border-border bg-surface/88 shadow-overlay backdrop-blur-xl lg:grid-cols-[minmax(0,1.25fr)_440px]">
        <div className="relative flex flex-col justify-between overflow-hidden border-b border-border p-6 sm:p-10 lg:border-b-0 lg:border-r lg:p-14">
          <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-primary/10 blur-3xl" />
          <BrandMark />
          <div className="relative my-12 max-w-2xl lg:my-16">
            <span className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-brand-soft px-3 py-1 text-xs font-semibold text-brand-strong">
              <Sparkles className="h-3.5 w-3.5" aria-hidden="true" /> Internal engineering intelligence
            </span>
            <h1 className="mt-6 text-4xl font-semibold leading-[1.08] tracking-[-0.04em] sm:text-5xl">{copy.login.statement}</h1>
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
              <span className="grid h-11 w-11 place-items-center rounded-app border border-primary/20 bg-brand-soft text-brand-strong"><ShieldCheck className="h-5 w-5" aria-hidden="true" /></span>
              <h2 className="mt-5 text-2xl font-semibold tracking-[-0.025em]">{copy.login.title}</h2>
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

            <div className="my-7 flex items-center gap-3"><span className="h-px flex-1 bg-border" /><span className="text-[10px] font-semibold uppercase tracking-[0.14em] text-text-muted">{copy.login.seededAccess}</span><span className="h-px flex-1 bg-border" /></div>
            <p className="-mt-3 mb-3 text-xs leading-5 text-text-muted">{copy.login.seededAccessBody}</p>
            <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
              {demoAccounts.map((account) => (
                <button className="rounded-control border border-border bg-surface px-3 py-2 text-left transition hover:border-border-strong hover:bg-surface-muted" key={account.email} onClick={() => fillAccount(account.email)} type="button">
                  <span className="block text-xs font-semibold text-text">{account.label}</span>
                  <span className="mt-1 block text-[10px] leading-4 text-text-muted">{account.context}</span>
                </button>
              ))}
            </div>
          </form>
        </div>
      </section>
    </main>
  );
}

function ValuePoint({ body, title }: { body: string; title: string }) {
  return <div className="rounded-app border border-border bg-surface/70 p-3.5"><CheckCircle2 className="h-4 w-4 text-brand-strong" /><p className="mt-3 text-sm font-semibold">{title}</p><p className="mt-1 text-xs leading-5 text-text-muted">{body}</p></div>;
}

function ProductPreview() {
  return (
    <div className="relative rounded-[18px] border border-border bg-elevated/90 p-4 shadow-soft sm:p-5">
      <div className="flex items-center gap-3 border-b border-border pb-4">
        <span className="grid h-9 w-9 place-items-center rounded-control bg-brand-soft text-brand-strong"><Search className="h-4 w-4" /></span>
        <div className="min-w-0"><p className="truncate text-sm font-medium">ModuleNotFoundError after Docker deployment</p><p className="mt-1 text-xs text-text-muted">3 verified matches · 2 relevant engineers</p></div>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-[minmax(0,1fr)_180px]">
        <div className="rounded-app border border-border bg-surface p-4">
          <div className="flex items-center justify-between gap-2"><span className="text-xs font-semibold text-success">Verified solution</span><span className="rounded-full bg-brand-soft px-2 py-1 text-[10px] font-semibold text-brand-strong">94% match</span></div>
          <p className="mt-3 text-sm font-semibold">Container copied the package outside Python’s module path</p>
          <p className="mt-2 text-xs leading-5 text-text-muted">Correct the final-stage COPY path, rebuild the image, and verify imports in a clean container.</p>
        </div>
        <div className="rounded-app border border-border bg-surface p-4">
          <span className="grid h-9 w-9 place-items-center rounded-full bg-brand-soft text-xs font-semibold text-brand-strong">SS</span>
          <p className="mt-3 text-sm font-semibold">Syed Sofiyan</p>
          <p className="mt-1 text-xs leading-5 text-text-muted">Cloud & DevOps Engineer</p>
          <span className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-brand-strong"><UserRound className="h-3.5 w-3.5" />View expert</span>
        </div>
      </div>
    </div>
  );
}
