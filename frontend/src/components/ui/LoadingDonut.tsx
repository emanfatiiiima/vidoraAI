import { motion } from "motion/react";
import { Loader2 } from "lucide-react";
import { cn } from "../../lib/utils";

interface LoadingDonutProps {
  /** Optional caption under the donut. */
  label?: string;
}

/** Colourful page-level loader (use <Spinner /> inside buttons). */
export default function LoadingDonut({ label }: LoadingDonutProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-4">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 1.6, ease: "linear" }}
        className="w-14 h-14 rounded-full border-[6px] border-transparent border-t-pink-400 border-r-yellow-400 border-b-cyan-400 border-l-purple-400"
      />
      {label && <p className="text-sm font-medium text-zinc-500 animate-pulse">{label}</p>}
    </div>
  );
}

/** Small inline spinner for buttons and compact areas. */
export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cn("w-4 h-4 animate-spin", className)} />;
}
