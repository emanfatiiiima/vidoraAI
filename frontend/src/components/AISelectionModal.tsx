import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { AlertCircle, Check, Clapperboard, Cpu, Film, HardDrive, Image as ImageIcon, Lightbulb, Mic, PenTool, RotateCcw, Sparkles } from "lucide-react";
import type { ReactNode } from "react";
import { Spinner } from "./ui/LoadingDonut";
import { cn } from "../lib/utils";
import { REQUIRED_TASKS, type AIChoice, type AISelection } from "../lib/aiSelection";
import { fetchAIOptions, verifyAIProvider, type AITaskId, type AITaskOptions, type ProviderStatus } from "../services/api";

const TASK_ICONS: Record<AITaskId, ReactNode> = {
  topics: <Lightbulb className="w-4 h-4" />,
  script: <PenTool className="w-4 h-4" />,
  voice: <Mic className="w-4 h-4" />,
  image: <ImageIcon className="w-4 h-4" />,
  video: <Film className="w-4 h-4" />,
  compile: <Clapperboard className="w-4 h-4" />,
};

type RequiredTask = (typeof REQUIRED_TASKS)[number];
type Choices = Partial<Record<RequiredTask, AIChoice>>;

interface AISelectionModalProps {
  /** The current selection, when the popup is reopened mid-project. */
  initial: AISelection | null;
  onConfirm: (selection: AISelection) => void;
  /** Closes without changing anything (first time: leaves the studio). */
  onCancel: () => void;
}

/**
 * Popup shown before Step 1: the user picks one AI per task.
 *
 * Picking an AI checks it on the server right away (cloud: API key accepted;
 * local: Ollama / the GPU worker running and the model downloaded). If it
 * can't be used, the reason is shown and the user must pick another AI.
 */
export default function AISelectionModal({ initial, onConfirm, onCancel }: AISelectionModalProps) {
  const [tasks, setTasks] = useState<AITaskOptions[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [choices, setChoices] = useState<Choices>(initial ?? {});
  // Providers checked in this popup: id -> reason it failed (null = works).
  // A key is shared across tasks, so one check covers every task it appears in.
  const [checked, setChecked] = useState<Record<string, string | null>>({});
  const [verifying, setVerifying] = useState<{ task: RequiredTask; provider: string } | null>(null);
  const [taskErrors, setTaskErrors] = useState<Partial<Record<RequiredTask, string>>>({});

  const loadOptions = async () => {
    setLoadError(null);
    try {
      setTasks(await fetchAIOptions());
    } catch (e) {
      console.error("AI options error:", e);
      setLoadError("Couldn't load the AI options. Please check that the server is running.");
    }
  };

  useEffect(() => {
    loadOptions();
  }, []);

  /** Why ``option`` can't be used, or null if it can (as far as we know). */
  const problemWith = (option: ProviderStatus): string | null =>
    !option.available ? option.reason : checked[option.id] ?? null;

  const choose = async (task: RequiredTask, option: ProviderStatus) => {
    setTaskErrors(prev => ({ ...prev, [task]: undefined }));

    // 1. Key missing on the server - no need to ask the provider.
    const knownProblem = problemWith(option);
    if (knownProblem) {
      setTaskErrors(prev => ({ ...prev, [task]: `${knownProblem} Please choose another AI.` }));
      return;
    }

    // 2. Ask the server to test the key (once per provider).
    if (!(option.id in checked)) {
      setVerifying({ task, provider: option.id });
      let reason: string | null;
      try {
        const status = await verifyAIProvider(option.id);
        reason = status.available ? null : status.reason ?? `${option.label} is unavailable.`;
      } catch (e) {
        console.error("AI verify error:", e);
        reason = `Couldn't check ${option.label}. Please try again.`;
      }
      setVerifying(null);
      setChecked(prev => ({ ...prev, [option.id]: reason }));
      if (reason) {
        setTaskErrors(prev => ({ ...prev, [task]: `${reason} Please choose another AI.` }));
        // Drop the choice if this provider was picked before (e.g. reopened popup).
        setChoices(prev => (prev[task]?.id === option.id ? { ...prev, [task]: undefined } : prev));
        return;
      }
    }

    setChoices(prev => ({ ...prev, [task]: { id: option.id, label: option.label } }));
  };

  const allChosen = REQUIRED_TASKS.every(task => choices[task]);
  const confirm = () => {
    if (allChosen) onConfirm(choices as AISelection);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start sm:items-center justify-center bg-zinc-900/40 backdrop-blur-sm p-4 overflow-y-auto">
      <motion.div
        initial={{ opacity: 0, y: 12, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        role="dialog"
        aria-modal="true"
        aria-labelledby="ai-selection-title"
        className="surface w-full max-w-2xl p-5 sm:p-7 my-auto"
      >
        <div className="flex items-start gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-brand-primary/10 text-brand-primary flex items-center justify-center shrink-0">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h2 id="ai-selection-title" className="text-xl font-salena font-bold text-zinc-900">Choose your AIs</h2>
            <p className="text-sm text-zinc-500">Pick which AI handles each part of your video. Only the AI you pick is used. <span className="whitespace-nowrap"><HardDrive className="inline w-3 h-3 -mt-0.5" /> Local</span> models run on your own GPU, free and offline.</p>
          </div>
        </div>

        {loadError ? (
          <div className="py-8 text-center">
            <p className="text-sm text-red-600 mb-4">{loadError}</p>
            <button onClick={loadOptions} className="btn-dark inline-flex items-center gap-2">
              <RotateCcw className="w-4 h-4" /> <span>Try again</span>
            </button>
          </div>
        ) : !tasks ? (
          <div className="py-12 flex justify-center"><Spinner className="w-6 h-6 text-zinc-400" /></div>
        ) : (
          <div className="space-y-5">
            {tasks.map(task => (
              <section key={task.id}>
                <div className="flex items-center gap-2 mb-2 text-sm font-semibold text-zinc-800">
                  <span className="text-zinc-500">{TASK_ICONS[task.id]}</span>
                  {task.label}
                  {task.comingSoon && <span className="chip !text-[10px] uppercase tracking-wide">Coming soon</span>}
                </div>

                {task.comingSoon ? (
                  <p className="text-xs text-zinc-500 px-1">Available in a later update.</p>
                ) : (
                  <>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                      {task.options.map(option => {
                        const requiredTask = task.id as RequiredTask;
                        const selected = choices[requiredTask]?.id === option.id;
                        const problem = problemWith(option);
                        const isVerifying = verifying?.task === requiredTask && verifying.provider === option.id;
                        return (
                          <button
                            key={option.id}
                            onClick={() => choose(requiredTask, option)}
                            disabled={verifying !== null}
                            aria-pressed={selected}
                            title={problem ?? `Use ${option.label} for ${task.label.toLowerCase()}`}
                            className={cn(
                              "px-4 py-2.5 rounded-xl text-sm font-semibold border transition-all inline-flex items-center justify-center gap-2 disabled:cursor-wait",
                              selected
                                ? "bg-zinc-900 text-white border-zinc-900 shadow-md"
                                : problem
                                  ? "bg-zinc-50 text-zinc-400 border-zinc-200 line-through"
                                  : "bg-white text-zinc-800 border-zinc-200 hover:border-zinc-400 hover:shadow-sm"
                            )}
                          >
                            {isVerifying ? <Spinner className="w-4 h-4" /> : selected ? <Check className="w-4 h-4" /> : option.local ? <HardDrive className="w-4 h-4" /> : <Sparkles className="w-4 h-4" />}
                            <span className="truncate">{option.label}</span>
                          </button>
                        );
                      })}
                    </div>
                    {(() => {
                      const note = task.options.find(o => o.id === choices[task.id as RequiredTask]?.id)?.note;
                      return note ? <p className="mt-2 text-xs text-zinc-500 px-1">{note}</p> : null;
                    })()}
                    {taskErrors[task.id as RequiredTask] && (
                      <p role="alert" className="mt-2 flex items-start gap-1.5 text-xs text-red-600">
                        <AlertCircle className="w-3.5 h-3.5 mt-px shrink-0" />
                        {taskErrors[task.id as RequiredTask]}
                      </p>
                    )}
                  </>
                )}
              </section>
            ))}
          </div>
        )}

        <div className="flex flex-col-reverse sm:flex-row sm:justify-end gap-2 mt-7 pt-5 border-t border-zinc-100">
          <button onClick={onCancel} className="btn-ghost">{initial ? "Cancel" : "Back"}</button>
          <button onClick={confirm} disabled={!allChosen || verifying !== null} className="btn-primary">
            <span>{initial ? "Save choices" : "Start project"}</span>
          </button>
        </div>
      </motion.div>
    </div>
  );
}
