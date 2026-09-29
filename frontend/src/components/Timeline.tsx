import { motion } from "motion/react";
import { 
  Check, 
  Home, 
  Search, 
  PenTool, 
  Mic, 
  Film, 
  Image as ImageIcon, 
  Video, 
  Cpu, 
  Download 
} from "lucide-react";
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

const getStepIcon = (label: string) => {
  switch (label.toLowerCase()) {
    case 'start': return <Home className="w-5 h-5" />;
    case 'topic': return <Search className="w-5 h-5" />;
    case 'narrative': return <PenTool className="w-5 h-5" />;
    case 'audio': return <Mic className="w-5 h-5" />;
    case 'visuals': return <ImageIcon className="w-5 h-5" />;
    case 'motion': return <Video className="w-5 h-5" />;
    case 'finalize': return <Cpu className="w-5 h-5" />;
    case 'download': return <Download className="w-5 h-5" />;
    default: return null;
  }
};

export default function Timeline({ steps, currentStep, onStepClick }: TimelineProps) {
  return (
    <div className="w-full py-8 overflow-hidden">
      <div className="flex items-center justify-between max-w-6xl mx-auto px-4">
        {steps.map((step, index) => (
          <div key={step.id} className="flex items-center flex-1 last:flex-none">
            {/* Step Circle */}
            <div className="flex flex-col items-center relative group">
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={() => onStepClick(step.id)}
                disabled={step.status === 'pending' && step.id > currentStep}
                className={cn(
                  "w-12 h-12 rounded-2xl flex items-center justify-center border-2 transition-all duration-300 relative z-10",
                  step.status === 'completed' 
                    ? "bg-[#c6e9c8] border-[#c6e9c8] text-[#718804]" 
                    : step.id === currentStep 
                    ? "bg-white border-[#718804] text-[#718804]" 
                    : "bg-white border-[#8bb7df] text-zinc-300"
                )}
              >
                {getStepIcon(step.label)}
              </motion.button>
              
              {/* Label */}
              <span className={cn(
                "absolute -bottom-9 whitespace-nowrap text-[11px] font-black uppercase tracking-widest transition-all",
                step.id === currentStep ? "text-[#718804] opacity-100" : "text-zinc-500 opacity-40"
              )}>
                {step.label}
              </span>
            </div>

            {/* Connector Line */}
            {index < steps.length - 1 && (
              <div className="flex-1 h-[2px] bg-zinc-100 mx-4 relative overflow-hidden">
                <motion.div
                  initial={{ x: "-100%" }}
                  animate={{ x: step.status === 'completed' ? "0%" : "-100%" }}
                  className="absolute inset-0 bg-[#c6e9c8]"
                />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
