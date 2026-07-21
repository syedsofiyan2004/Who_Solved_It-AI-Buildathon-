import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useLocation, useNavigate } from "react-router-dom";
import { z } from "zod";

import { useAuth } from "../auth/AuthProvider";
import { copy } from "../content/uiCopy";

const loginSchema = z.object({
  email: z.string().email(copy.login.emailInvalid),
  password: z.string().min(8, copy.login.passwordInvalid).max(128, copy.login.passwordInvalid)
});
type LoginFormValues = z.infer<typeof loginSchema>;

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [error, setError] = useState<string | null>(null);
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<LoginFormValues>({ resolver: zodResolver(loginSchema) });
  const onSubmit = async (values: LoginFormValues) => {
    setError(null);
    try {
      await login(values);
      const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
      navigate(from ?? "/dashboard", { replace: true });
    } catch { setError(copy.login.invalid); }
  };
  return <main className="grid min-h-screen place-items-center bg-surface px-4 py-8 text-text"><section className="w-full max-w-sm border border-border bg-surface-muted p-6 shadow-sm sm:p-8"><p className="text-sm font-medium text-text-muted">{copy.app.name}</p><h1 className="mt-2 text-2xl font-semibold tracking-normal">{copy.login.title}</h1><p className="mt-3 text-sm leading-6 text-text-muted">{copy.login.description}</p><form className="mt-6 space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate><label className="block text-sm font-medium" htmlFor="email">{copy.login.email}<input id="email" type="email" autoComplete="email" className="mt-1 block h-10 w-full border border-border bg-surface px-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20" aria-invalid={Boolean(errors.email)} aria-describedby={errors.email ? "email-error" : undefined} {...register("email")} /></label>{errors.email && <p id="email-error" className="text-sm text-red-700">{errors.email.message}</p>}<label className="block text-sm font-medium" htmlFor="password">{copy.login.password}<input id="password" type="password" autoComplete="current-password" className="mt-1 block h-10 w-full border border-border bg-surface px-3 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20" aria-invalid={Boolean(errors.password)} aria-describedby={errors.password ? "password-error" : undefined} {...register("password")} /></label>{errors.password && <p id="password-error" className="text-sm text-red-700">{errors.password.message}</p>}{error && <p className="text-sm text-red-700" role="alert">{error}</p>}<button className="flex h-10 w-full items-center justify-center bg-accent px-4 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60" disabled={isSubmitting} type="submit">{isSubmitting ? copy.login.submitting : copy.login.submit}</button></form></section></main>;
}
