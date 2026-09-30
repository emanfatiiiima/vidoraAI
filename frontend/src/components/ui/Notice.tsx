import type { ReactNode } from "react";
import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";
import { cn } from "../../lib/utils";

type Tone = "error" | "success" | "info";

const STYLES: Record<Tone, { box: string; icon: ReactNode }> = {
  error: { box: "bg-red-50 border-red-200 text-red-700", icon: <AlertCircle className="w-4 h-4 shrink-0" /> },
  success: { box: "bg-emerald-50 border-emerald-200 text-emerald-700", icon: <CheckCircle2 className="w-4 h-4 shrink-0" /> },
  info: { box: "bg-sky-50 border-sky-200 text-sky-700", icon: <Info className="w-4 h-4 shrink-0" /> },
};

interface NoticeProps {
  tone?: Tone;
  children: ReactNode;
  /** Shows a close button when provided. */
  onDismiss?: () => void;
  className?: string;
}

/** Inline message shown in the page flow - used instead of alert() popups. */
export default function Notice({ tone = "error", children, onDismiss, className }: NoticeProps) {
  const style = STYLES[tone];
  return (
    <div role={tone === "error" ? "alert" : "status"} className={cn("flex items-start gap-2.5 px-4 py-3 rounded-xl border text-sm text-left", style.box, className)}>
      <span className="mt-0.5">{style.icon}</span>
      <div className="flex-1 min-w-0 break-words">{children}</div>
      {onDismiss && (
        <button onClick={onDismiss} aria-label="Dismiss" className="opacity-60 hover:opacity-100 transition">
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}
