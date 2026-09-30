import { motion } from "motion/react";
import {
  Check,
  Home,
  Search,
  PenTool,
  Mic,
  Image as ImageIcon,
  Video,
  Cpu,
  Download,
} from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "../lib/utils";

export type StepStatus = 'pending' | 'in-progress' | 'completed';

export interface Step {
  id: number;
  label: string;
  status: StepStatus;
}

interface TimelineProps {
  steps: Step[];
  currentStep: number;
  onStepClick: (stepId: number) => void;
}

// Icons are keyed by step number so renaming a label never removes its icon.
const STEP_ICONS: Record<number, ReactNode> = {
  1: <Home className="w-4 h-4" />,
  2: <Search className="w-4 h-4" />,
  3: <PenTool className="w-4 h-4" />,
  4: <Mic className="w-4 h-4" />,
  5: <ImageIcon className="w-4 h-4" />,
  6: <Video className="w-4 h-4" />,
  7: <Cpu className="w-4 h-4" />,
  8: <Download className="w-4 h-4" />,
};

export default function Timeline({ steps, currentStep, onStepClick }: TimelineProps) {
  return (
    <div className="w-full pt-4 pb-10 overflow-x-auto no-scrollbar">
      <div className="flex items-center justify-between max-w-5xl mx-auto px-4 min-w-[640px]">
        {steps.map((step, index) => {
          const isCurrent = step.id === currentStep;
          const isDone = step.status === 'completed' && !isCurrent;
          return (
            <div key={step.id} className="flex items-center flex-1 last:flex-none">
              {/* Step square */}
              <div className="flex flex-col items-center relative">
                <motion.button
                  whileHover={{ scale: 1.06 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => onStepClick(step.id)}
                  disabled={step.status === 'pending' && step.id > currentStep}
                  aria-current={isCurrent ? "step" : undefined}
                  title={step.label}
                  className={cn(
                    "w-10 h-10 rounded-xl flex items-center justify-center border transition-colors relative z-10 disabled:cursor-not-allowed",
                    isDone
                      ? "bg-[var(--color-done-green)] border-[var(--color-done-green)] text-[var(--color-timeline-text)]"
                      : isCurrent
                      ? "bg-white border-[var(--color-timeline-text)] text-[var(--color-timeline-text)] ring-4 ring-[var(--color-done-green)]/50"
                      : "bg-white border-zinc-200 text-zinc-300"
                  )}
                >
                  {isDone ? <Check className="w-4 h-4" /> : STEP_ICONS[step.id]}
                </motion.button>

                {/* Label */}
                <span className={cn(
                  "absolute top-12 whitespace-nowrap text-xs font-medium transition-colors",
                  isCurrent ? "text-[var(--color-timeline-text)] font-semibold" : isDone ? "text-zinc-600" : "text-zinc-400"
                )}>
                  {step.label}
                </span>
              </div>

              {/* Connector line */}
              {index < steps.length - 1 && (
                <div className="flex-1 h-0.5 bg-zinc-100 mx-2 rounded-full relative overflow-hidden">
                  <motion.div
                    initial={{ x: "-100%" }}
                    animate={{ x: step.status === 'completed' && !isCurrent ? "0%" : "-100%" }}
                    className="absolute inset-0 bg-[var(--color-done-green)]"
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
