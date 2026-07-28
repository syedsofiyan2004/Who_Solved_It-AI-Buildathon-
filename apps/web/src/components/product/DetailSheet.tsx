import { X } from "lucide-react";
import { type ReactNode, useEffect, useRef } from "react";

import { copy } from "../../content/uiCopy";

export function DetailSheet({ title, children, onClose }: { title: string; children: ReactNode; onClose: () => void }) {
  const panelRef = useRef<HTMLElement>(null);
  const returnFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    returnFocusRef.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const panel = panelRef.current;
    const focusable = panel?.querySelector<HTMLElement>("button, a[href], input, select, textarea, [tabindex]:not([tabindex='-1'])");
    focusable?.focus();

    const handleKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }
      if (event.key !== "Tab" || !panel) return;
      const items = Array.from(panel.querySelectorAll<HTMLElement>("button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex='-1'])"));
      if (items.length === 0) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    window.addEventListener("keydown", handleKey);
    return () => {
      window.removeEventListener("keydown", handleKey);
      document.body.style.overflow = previousOverflow;
      returnFocusRef.current?.focus();
    };
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 bg-text/35 backdrop-blur-[2px] xl:hidden" onMouseDown={onClose} role="presentation">
      <aside ref={panelRef} aria-label={title} className="absolute inset-x-0 bottom-0 max-h-[94vh] overflow-y-auto rounded-t-[22px] border border-border bg-elevated p-5 shadow-overlay sm:inset-y-3 sm:left-auto sm:right-3 sm:w-[540px] sm:rounded-[22px]" onMouseDown={(event) => event.stopPropagation()} role="dialog" aria-modal="true">
        <div className="mb-5 flex items-center justify-between gap-3 border-b border-border pb-4">
          <div><p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-brand-strong">Workspace detail</p><p className="mt-1 text-sm font-semibold text-text">{title}</p></div>
          <button aria-label={copy.action.close} className="grid h-10 w-10 place-items-center rounded-control border border-border bg-surface text-text-muted transition-colors hover:bg-surface-muted hover:text-text" onClick={onClose} type="button">
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>
        {children}
      </aside>
    </div>
  );
}
