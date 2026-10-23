import type { ReactNode } from "react";
import { cn } from "../../lib/utils";

/** Accent colour of the small badge above the title. */
type Tone = "primary" | "secondary" | "accent" | "berry";

const TONE_CLASSES: Record<Tone, string> = {
  primary: "bg-brand-primary/10 text-brand-primary",
  secondary: "bg-brand-secondary/15 text-teal-700",
  accent: "bg-brand-accent/15 text-amber-700",
  berry: "bg-brand-berry/10 text-brand-berry",
};

interface StepHeaderProps {
  icon: ReactNode;
  /** Short label in the badge, e.g. "Step 2 · Topic". */
  eyebrow: string;
  title: string;
  description?: string;
  tone?: Tone;
  /** Optional buttons shown under the description. */
  actions?: ReactNode;
}

/** Consistent, compact heading used at the top of every pipeline step. */
export default function StepHeader({ icon, eyebrow, title, description, tone = "primary", actions }: StepHeaderProps) {
  return (
    <div className="text-center mb-10">
      <div className={cn("inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold mb-4 [&_svg]:w-3.5 [&_svg]:h-3.5", TONE_CLASSES[tone])}>
        {icon}
        <span>{eyebrow}</span>
      </div>
      <h2 className="text-3xl md:text-4xl font-salena font-semibold tracking-tight text-zinc-900">{title}</h2>
      {description && <p className="mt-3 text-zinc-500 text-base max-w-xl mx-auto">{description}</p>}
      {actions && <div className="mt-6 flex flex-wrap justify-center gap-3">{actions}</div>}
    </div>
  );
}
