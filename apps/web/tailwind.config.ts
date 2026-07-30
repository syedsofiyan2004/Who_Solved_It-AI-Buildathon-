import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["\"Space Grotesk\"", "Inter", "ui-sans-serif", "sans-serif"],
        mono: ["\"IBM Plex Mono\"", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"]
      },
      colors: {
        background: "rgb(var(--color-background) / <alpha-value>)",
        foreground: "rgb(var(--color-foreground) / <alpha-value>)",
        canvas: "rgb(var(--color-canvas) / <alpha-value>)",
        surface: "rgb(var(--color-surface) / <alpha-value>)",
        "surface-foreground": "rgb(var(--color-surface-foreground) / <alpha-value>)",
        card: "rgb(var(--color-card) / <alpha-value>)",
        "card-foreground": "rgb(var(--color-card-foreground) / <alpha-value>)",
        elevated: "rgb(var(--color-elevated) / <alpha-value>)",
        muted: "rgb(var(--color-muted) / <alpha-value>)",
        "muted-foreground": "rgb(var(--color-muted-foreground) / <alpha-value>)",
        "surface-muted": "rgb(var(--color-surface-muted) / <alpha-value>)",
        border: "rgb(var(--color-border) / <alpha-value>)",
        "border-strong": "rgb(var(--color-border-strong) / <alpha-value>)",
        input: "rgb(var(--color-input) / <alpha-value>)",
        text: "rgb(var(--color-text) / <alpha-value>)",
        "text-muted": "rgb(var(--color-text-muted) / <alpha-value>)",
        primary: "rgb(var(--color-primary) / <alpha-value>)",
        "primary-foreground": "rgb(var(--color-primary-foreground) / <alpha-value>)",
        accent: "rgb(var(--color-accent) / <alpha-value>)",
        "accent-foreground": "rgb(var(--color-accent-foreground) / <alpha-value>)",
        "accent-hover": "rgb(var(--color-accent-hover) / <alpha-value>)",
        success: "rgb(var(--color-success) / <alpha-value>)",
        warning: "rgb(var(--color-warning) / <alpha-value>)",
        destructive: "rgb(var(--color-destructive) / <alpha-value>)",
        danger: "rgb(var(--color-danger) / <alpha-value>)",
        info: "rgb(var(--color-info) / <alpha-value>)",
        code: "rgb(var(--color-code) / <alpha-value>)",
        "code-foreground": "rgb(var(--color-code-foreground) / <alpha-value>)",
        "brand-soft": "rgb(var(--color-brand-soft) / <alpha-value>)",
        "brand-strong": "rgb(var(--color-brand-strong) / <alpha-value>)"
      },
      borderRadius: {
        control: "0.625rem",
        app: "0.875rem",
        dialog: "1.125rem"
      },
      boxShadow: {
        soft: "0 1px 2px rgb(15 23 42 / 0.04), 0 10px 28px rgb(15 23 42 / 0.05)",
        overlay: "0 24px 64px rgb(15 23 42 / 0.20)",
        focus: "0 0 0 4px rgb(var(--color-accent) / 0.14)"
      },
      transitionDuration: {
        120: "120ms",
        160: "160ms",
        220: "220ms"
      },
      maxWidth: {
        reading: "760px"
      }
    }
  },
  plugins: []
} satisfies Config;
