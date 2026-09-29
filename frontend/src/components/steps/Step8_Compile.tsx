import React, { useState, useEffect } from "react";
import { motion } from "motion/react";
import { Cpu, Layers, Music, Zap, Check, Share2, Loader2, Play } from "lucide-react";
import LoadingDonut from "../ui/LoadingDonut";
import { compileVideo } from "../../services/api";

interface Scene {
  id: number;
  videoUrl?: string | null;
}

interface Step8Props {
  scenes: Scene[];
  audioUrl: string;
  onNext: (finalUrl: string) => void;
}

export default function Step8_Compile({ scenes, audioUrl, onNext }: Step8Props) {
  const [isCompiling, setIsCompiling] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("Idle");
  const [finalUrl, setFinalUrl] = useState<string | null>(null);

  const startCompilation = async () => {
    setIsCompiling(true);
    setProgress(0);
    setStatus("Initializing Renderer...");

    const steps = [
      { p: 10, s: "Verifying temporal assets..." },
      { p: 30, s: "Stitching cinematic sequences..." },
      { p: 50, s: "Synchronizing atmospheric audio..." },
      { p: 75, s: "Applying color grading & LUTs..." },
      { p: 90, s: "Finalizing export encode..." },
    ];

    for (const step of steps) {
      await new Promise(r => setTimeout(r, 1000));
      setProgress(step.p);
      setStatus(step.s);
    }

    try {
      setFinalUrl(await compileVideo(scenes, audioUrl));
      setProgress(100);
      setStatus("Neural Synthesis Complete");
    } catch (e) {
      console.error("Compile Error:", e);
      setStatus("Engine Malfunction - Retrying...");
      setIsCompiling(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-12">
      <div className="text-center mb-16">
        <div className="inline-flex items-center space-x-2 px-4 py-2 bg-brand-berry/10 text-brand-berry rounded-full mb-6">
           <Cpu className="w-4 h-4" />
           <span className="text-[10px] font-black uppercase tracking-[0.2em]">Phase Eight / Sequence Assembly</span>
        </div>
        <h2 className="text-5xl font-salena text-zinc-900 tracking-tighter mb-4">Neural Assembly</h2>
        <p className="text-zinc-400 font-medium text-lg max-w-2xl mx-auto italic">Merging visual motion and acoustic layers into a mastered sequence.</p>
      </div>

      <div className="glass-pane !p-12 relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/dust.png')] opacity-10 pointer-events-none" />
        
        {!isCompiling && !finalUrl ? (
          <div className="text-center space-y-8 relative z-10">
             <div className="flex justify-center -space-x-4 mb-8">
                {scenes.slice(0, 4).map((_, i) => (
                  <div key={i} className="w-20 h-20 bg-zinc-100 rounded-3xl border-4 border-white shadow-xl flex items-center justify-center">
                     <Layers className="w-8 h-8 text-zinc-300" />
                  </div>
                ))}
                <div className="w-20 h-20 bg-brand-berry text-white rounded-3xl border-4 border-white shadow-xl flex items-center justify-center transform scale-110 shadow-berry/30">
                   <Zap className="w-8 h-8" />
                </div>
             </div>

             <button 
                onClick={startCompilation}
                className="btn-primary w-full py-6 flex items-center justify-center space-x-3 text-lg group"
             >
                <Cpu className="w-6 h-6 group-hover:rotate-90 transition-transform" />
                <span>INITIATE MASTER RENDERING</span>
             </button>
          </div>
        ) : (
          <div className="space-y-12 relative z-10">
             <div className="flex flex-col items-center justify-center">
                {progress < 100 ? (
                  <div className="relative">
                    <LoadingDonut />
                    <div className="absolute inset-0 flex items-center justify-center">
                       <span className="text-2xl font-black text-brand-berry italic leading-none">{progress}%</span>
                    </div>
                  </div>
                ) : (
                  <motion.div 
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="w-32 h-32 bg-green-500 text-white rounded-full flex items-center justify-center shadow-2xl"
                  >
                    <Check className="w-16 h-16" />
                  </motion.div>
                )}
                
                <div className="mt-8 text-center">
                  <h3 className="text-xl font-black text-zinc-900 uppercase tracking-widest italic animate-pulse mb-2">
                    {status}
                  </h3>
                  <p className="text-zinc-400 font-medium text-sm">Processing through decentralized neural nodes</p>
                </div>
             </div>

             <div className="h-4 bg-zinc-100 rounded-full overflow-hidden border border-zinc-200">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  className="h-full bg-gradient-to-r from-brand-berry via-brand-primary to-brand-secondary"
                />
             </div>

             {finalUrl && (
                <motion.div 
                   initial={{ opacity: 0, y: 20 }}
                   animate={{ opacity: 1, y: 0 }}
                   className="pt-12 flex justify-center"
                >
                   <button 
                      onClick={() => onNext(finalUrl)}
                      className="btn-primary px-16 py-6 flex items-center space-x-4 shadow-2xl scale-110"
                   >
                      <Play className="w-6 h-6" />
                      <span>PREVIEW MASTERED CUT</span>
                   </button>
                </motion.div>
             )}
          </div>
        )}
      </div>

      <div className="mt-12 grid grid-cols-3 gap-6 opacity-30">
         <div className="p-6 border border-zinc-200 rounded-[32px] flex flex-col items-center text-center">
            <Layers className="w-6 h-6 mb-3" />
            <span className="text-[10px] font-black uppercase tracking-widest leading-normal">Sequence<br/>Stitching</span>
         </div>
         <div className="p-6 border border-zinc-200 rounded-[32px] flex flex-col items-center text-center">
            <Music className="w-6 h-6 mb-3" />
            <span className="text-[10px] font-black uppercase tracking-widest leading-normal">Audio<br/>Layering</span>
         </div>
         <div className="p-6 border border-zinc-200 rounded-[32px] flex flex-col items-center text-center">
            <Share2 className="w-6 h-6 mb-3" />
            <span className="text-[10px] font-black uppercase tracking-widest leading-normal">CDN<br/>Packaging</span>
         </div>
      </div>
    </div>
  );
}
