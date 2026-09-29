import React, { useState } from "react";
import { motion } from "motion/react";
import { Sparkles, Clock, Layers, Users, Rocket } from "lucide-react";
import { cn } from "../../lib/utils";

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
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className="max-w-4xl mx-auto"
    >
      <div className="text-center mb-16">
        <div className="inline-flex items-center space-x-2 px-4 py-2 bg-brand-primary/10 text-brand-primary rounded-full mb-6">
          <Sparkles className="w-4 h-4" />
          <span className="text-[10px] font-black uppercase tracking-[0.2em]">Phase One</span>
        </div>
        <h2 className="text-5xl font-salena text-zinc-900 mb-6 tracking-tighter">
          Visual Identity
        </h2>
        <p className="text-zinc-400 font-medium text-lg">Define the cinematic DNA of your next production.</p>
      </div>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-10 glass-pane">
        {/* Niche Section */}
        <div className="md:col-span-2 space-y-6">
          <label className="flex items-center justify-between px-2">
            <span className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.2em]">Select Your Niche</span>
            <span className="text-[10px] font-black text-brand-primary uppercase tracking-[0.2em]">Required</span>
          </label>
          <div className="flex flex-col sm:flex-row gap-6">
            <select
              disabled={useCustomNiche}
              className="flex-grow input-field disabled:opacity-30"
              value={inputs.niche}
              onChange={(e) => setInputs({ ...inputs, niche: e.target.value })}
            >
              {COMMON_NICHES.map(n => <option key={n} value={n}>{n}</option>)}
            </select>
            <div className="flex items-center space-x-3 shrink-0 px-4 py-2 bg-zinc-100/50 rounded-2xl border border-zinc-200/50">
               <input 
                  type="checkbox" 
                  id="custom" 
                  className="w-5 h-5 rounded-lg border-2 border-zinc-300 text-brand-primary focus:ring-brand-primary cursor-pointer"
                  checked={useCustomNiche}
                  onChange={(e) => setUseCustomNiche(e.target.checked)}
               />
               <label htmlFor="custom" className="text-sm font-black text-zinc-600 cursor-pointer uppercase tracking-wider">Custom</label>
            </div>
            {useCustomNiche && (
              <motion.input
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                type="text"
                placeholder="Type your niche here..."
                className="flex-grow input-field border-brand-primary/20 bg-brand-primary/5"
                value={customNiche}
                onChange={(e) => setCustomNiche(e.target.value)}
                required
              />
            )}
          </div>
        </div>

        {/* Style */}
        <div className="space-y-4">
          <label className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.2em] px-2 block">Visual Style</label>
          <select
            className="input-field"
            value={inputs.style}
            onChange={(e) => setInputs({ ...inputs, style: e.target.value })}
          >
            <option>Cinematic</option>
            <option>Documentary</option>
            <option>High-Energy Viral</option>
            <option>Minimalist Tech</option>
            <option>Dark Documentary</option>
            <option>Cyberpunk / Neon</option>
          </select>
        </div>

        {/* Aspect Ratio */}
        <div className="space-y-4">
          <label className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.2em] px-2 block">Aspect Ratio</label>
          <div className="grid grid-cols-3 gap-4">
            {(["16:9", "9:16", "1:1"] as const).map((ratio) => (
              <button
                key={ratio}
                type="button"
                onClick={() => setInputs({ ...inputs, aspectRatio: ratio })}
                className={cn(
                  "py-4 rounded-3xl font-black text-sm transition-all border-2",
                  inputs.aspectRatio === ratio 
                    ? "bg-brand-primary text-white border-brand-primary shadow-lg shadow-brand-primary/25" 
                    : "bg-zinc-100/50 text-zinc-400 border-transparent hover:bg-zinc-200/50"
                )}
              >
                {ratio}
              </button>
            ))}
          </div>
        </div>

        {/* Duration */}
        <div className="space-y-4">
          <label className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.2em] px-2 block">Video Duration</label>
          <div className="flex gap-4">
            <input
              type="number"
              min={1}
              className="w-full input-field text-center font-black text-xl"
              value={inputs.duration}
              onChange={(e) => setInputs({ ...inputs, duration: parseInt(e.target.value) || 0 })}
              required
            />
            <select 
               className="input-field w-40 font-black"
               value={inputs.durationUnit}
               onChange={(e) => setInputs({ ...inputs, durationUnit: e.target.value as any })}
            >
              <option value="minutes">MINS</option>
              <option value="seconds">SECS</option>
            </select>
          </div>
        </div>

        {/* Scene Count (Slider) */}
        <div className="space-y-6 pt-2">
          <div className="flex justify-between items-center px-2">
            <label className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.2em]">Scene Complexity</label>
            <span className="bg-brand-primary/10 text-brand-primary px-3 py-1 rounded-xl text-[10px] font-black tracking-widest">{inputs.sceneCount} SCENES</span>
          </div>
          <div className="relative group px-1">
            <input
              type="range"
              min={1}
              max={15}
              step={1}
              className="w-full h-3 bg-zinc-100 rounded-full appearance-none cursor-pointer accent-brand-primary"
              value={inputs.sceneCount}
              onChange={(e) => setInputs({ ...inputs, sceneCount: parseInt(e.target.value) })}
            />
          </div>
        </div>

        <div className="md:col-span-2 flex justify-center mt-12">
          <motion.button
            whileHover={{ scale: 1.05, y: -4 }}
            whileTap={{ scale: 0.95 }}
            type="submit"
            className="btn-berry group flex items-center space-x-4 px-24 py-6"
          >
            <span className="text-xl">INITIATE GENERATION</span>
            <Rocket className="w-7 h-7 group-hover:translate-x-2 group-hover:-translate-y-2 transition-transform" />
          </motion.button>
        </div>
      </form>
    </motion.div>
  );
}
