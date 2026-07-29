import type { ButtonHTMLAttributes } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
};

const variants = {
  primary: "border border-primary bg-primary text-primary-foreground shadow-sm hover:bg-accent-hover hover:shadow-soft",
  secondary: "border border-border bg-surface text-text shadow-sm hover:border-border-strong hover:bg-surface-muted hover:shadow-soft",
  ghost: "border border-transparent bg-transparent text-text-muted hover:bg-surface-muted hover:text-text"
};

export function Button({ className = "", variant = "secondary", type = "button", ...props }: ButtonProps) {
  return <button className={`pressable inline-flex h-9 items-center justify-center gap-2 rounded-control px-3 text-sm font-medium transition-all duration-160 disabled:cursor-not-allowed disabled:border-border disabled:bg-muted disabled:text-muted-foreground disabled:shadow-none ${variants[variant]} ${className}`} type={type} {...props} />;
}
