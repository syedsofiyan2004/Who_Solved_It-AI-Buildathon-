import type { ButtonHTMLAttributes } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
};

const variants = {
  primary: "border border-accent bg-accent text-white hover:bg-accent-hover",
  secondary: "border border-border bg-surface text-text hover:bg-surface-muted",
  ghost: "border border-transparent bg-transparent text-text-muted hover:bg-surface-muted hover:text-text"
};

export function Button({ className = "", variant = "secondary", type = "button", ...props }: ButtonProps) {
  return <button className={`inline-flex h-9 items-center justify-center gap-2 rounded-control px-3 text-sm font-medium transition-colors duration-120 disabled:cursor-not-allowed disabled:opacity-50 ${variants[variant]} ${className}`} type={type} {...props} />;
}
