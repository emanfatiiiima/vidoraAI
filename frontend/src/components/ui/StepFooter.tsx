import type { ReactNode } from "react";
import { motion } from "motion/react";

interface StepFooterProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  /** Usually the "Continue" button. */
  action: ReactNode;
}

/**
 * "Ready to continue" row placed at the end of a step's content.
 * It sits in the normal page flow (no floating popup covering the content).
 */
export default function StepFooter({ icon, title, description, action }: StepFooterProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="surface mt-10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 px-5 py-4"
    >
      <div className="flex items-center gap-3 min-w-0">
        {icon && (
          <div className="w-10 h-10 rounded-xl bg-brand-primary/10 text-brand-primary flex items-center justify-center shrink-0 [&_svg]:w-5 [&_svg]:h-5">
            {icon}
          </div>
        )}
        <div className="min-w-0">
          <p className="font-semibold text-zinc-900 truncate">{title}</p>
          {description && <p className="text-sm text-zinc-500 truncate">{description}</p>}
        </div>
      </div>
      <div className="shrink-0 w-full sm:w-auto [&>*]:w-full sm:[&>*]:w-auto">{action}</div>
    </motion.div>
  );
}
