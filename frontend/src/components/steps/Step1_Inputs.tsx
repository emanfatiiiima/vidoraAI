import React, { useState } from "react";
import { motion } from "motion/react";
import { Sparkles, ArrowRight } from "lucide-react";
import { cn } from "../../lib/utils";
import StepHeader from "../ui/StepHeader";

export interface VideoInputs {
  niche: string;
  style: string;
  duration: number;
  durationUnit: "minutes" | "seconds";
  sceneCount: number;
  aspectRatio: "16:9" | "9:16" | "1:1";
}

interface Step1Props {
  onNext: (inputs: VideoInputs) => void;
  initialData?: VideoInputs;
  key?: string;
}

const COMMON_NICHES = [
  "AI & Future Technology",
  "Cooking & Healthy Eating",
  "Tech Product Reviews",
  "True Crime Documentaries",
  "Travel Vlogs & Guides",
  "Gaming News & Gameplay",
  "History & Ancient Civilizations",
  "Personal Finance & Investing"
];

const STYLES = ["Cinematic", "Documentary", "High-Energy Viral", "Minimalist Tech", "Dark Documentary", "Cyberpunk / Neon"];
const ASPECT_RATIOS = ["16:9", "9:16", "1:1"] as const;

export default function Step1_Inputs({ onNext, initialData }: Step1Props) {
  const [inputs, setInputs] = useState<VideoInputs>(initialData || {
    niche: COMMON_NICHES[0],
    style: "Cinematic",
    duration: 10,
    durationUnit: "minutes",
    sceneCount: 5,
    aspectRatio: "16:9"
  });
  const [customNiche, setCustomNiche] = useState("");
  const [useCustomNiche, setUseCustomNiche] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onNext({
      ...inputs,
      niche: useCustomNiche ? customNiche : inputs.niche
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-3xl mx-auto"
    >
      <StepHeader
        icon={<Sparkles />}
        eyebrow="Step 1 · Start"
        title="Visual identity"
        description="Define the style and format of your next video."
      />

      <form onSubmit={handleSubmit} className="glass-pane grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-6">
        {/* Niche */}
        <div className="md:col-span-2 space-y-2">
          <div className="flex items-center justify-between">
            <label className="field-label">Niche</label>
            <label className="flex items-center gap-2 text-sm font-medium text-zinc-700 cursor-pointer select-none">
              <input
                type="checkbox"
                className="w-4 h-4 rounded border-zinc-300 accent-[var(--color-brand-primary)] cursor-pointer"
                checked={useCustomNiche}
                onChange={(e) => setUseCustomNiche(e.target.checked)}
              />
              Custom niche
            </label>
          </div>
          {useCustomNiche ? (
            <motion.input
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              type="text"
              placeholder="Type your niche here..."
              className="input-field"
              value={customNiche}
              onChange={(e) => setCustomNiche(e.target.value)}
              autoFocus
              required
            />
          ) : (
            <select
              className="input-field"
              value={inputs.niche}
              onChange={(e) => setInputs({ ...inputs, niche: e.target.value })}
            >
              {COMMON_NICHES.map(n => <option key={n} value={n}>{n}</option>)}
            </select>
          )}
        </div>

        {/* Style */}
        <div className="space-y-2">
          <label className="field-label">Visual style</label>
          <select
            className="input-field"
            value={inputs.style}
            onChange={(e) => setInputs({ ...inputs, style: e.target.value })}
          >
            {STYLES.map(s => <option key={s}>{s}</option>)}
          </select>
        </div>

        {/* Aspect ratio */}
        <div className="space-y-2">
          <label className="field-label">Aspect ratio</label>
          <div className="grid grid-cols-3 gap-1 p-1 bg-white/60 rounded-xl border border-[var(--color-box-border)]">
            {ASPECT_RATIOS.map((ratio) => (
              <button
                key={ratio}
                type="button"
                onClick={() => setInputs({ ...inputs, aspectRatio: ratio })}
                className={cn(
                  "py-1.5 rounded-lg text-sm font-semibold transition-colors",
                  inputs.aspectRatio === ratio
                    ? "bg-brand-primary text-white shadow-sm"
                    : "text-zinc-500 hover:text-zinc-800 hover:bg-white"
                )}
              >
                {ratio}
              </button>
            ))}
          </div>
        </div>

        {/* Duration */}
        <div className="space-y-2">
          <label className="field-label">Video duration</label>
          <div className="flex gap-2">
            <input
              type="number"
              min={1}
              className="input-field"
              value={inputs.duration}
              onChange={(e) => setInputs({ ...inputs, duration: parseInt(e.target.value) || 0 })}
              required
            />
            <select
              className="input-field !w-32"
              value={inputs.durationUnit}
              onChange={(e) => setInputs({ ...inputs, durationUnit: e.target.value as VideoInputs["durationUnit"] })}
            >
              <option value="minutes">Minutes</option>
              <option value="seconds">Seconds</option>
            </select>
          </div>
        </div>

        {/* Scene count */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <label className="field-label">Number of scenes</label>
            <span className="text-xs font-semibold text-brand-primary bg-white/70 px-2 py-0.5 rounded-md">{inputs.sceneCount} scenes</span>
          </div>
          <input
            type="range"
            min={1}
            max={15}
            step={1}
            className="w-full mt-3 accent-[var(--color-brand-primary)] cursor-pointer"
            value={inputs.sceneCount}
            onChange={(e) => setInputs({ ...inputs, sceneCount: parseInt(e.target.value) })}
          />
          <div className="flex justify-between text-xs text-zinc-500">
            <span>1</span>
            <span>15</span>
          </div>
        </div>

        <div className="md:col-span-2 flex justify-end pt-2 border-t border-black/5">
          <button type="submit" className="btn-berry btn-lg mt-4">
            <span>Generate topics</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </form>
    </motion.div>
  );
}
