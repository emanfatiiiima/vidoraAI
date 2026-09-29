import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Image as ImageIcon, Sparkles, Wand2, RefreshCw, ChevronRight, Check, AlertCircle, Edit3, Film } from "lucide-react";
import LoadingDonut from "../ui/LoadingDonut";
import { cn } from "../../lib/utils";
import { generateImage as requestImage, generateScenePrompt, splitScriptIntoScenes } from "../../services/api";

interface Scene {
  id: number;
  text: string;
  prompt: string;
  selectedImage: string | null;
  status: 'pending' | 'generating' | 'ready';
}

interface Step6Props {
  script: string;
  sceneCount: number;
  style: string;
  onNext: (updatedScenes: Scene[]) => void;
  key?: string;
}

export default function Step6_Images({ script, sceneCount, style, onNext }: Step6Props) {
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [isSplitting, setIsSplitting] = useState(true);
  const [isGenerating, setIsGenerating] = useState<Record<number, boolean>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    splitScript();
  }, [script]);

  const splitScript = async () => {
    setIsSplitting(true);
    setError(null);
    try {
      // The backend splits the script with AI (and falls back to an even
      // sentence split if needed) - see core/services/scenes.py.
      const chunks = await splitScriptIntoScenes(script, sceneCount);

      const initial: Scene[] = chunks.map((text, i) => ({
        id: i + 1,
        text,
        prompt: "", 
        selectedImage: null,
        status: 'pending'
      }));

      setScenes(initial.slice(0, sceneCount));
      
      // Auto-trigger prompt generation for all
      const updatedScenes = [...initial.slice(0, sceneCount)];
      for (let i = 0; i < updatedScenes.length; i++) {
        generatePromptSequentially(i, updatedScenes);
      }
    } catch (e) {
      console.error("Split Error:", e);
      setError("AI Engine busy. Retrying script decomposition...");
    } finally {
      setIsSplitting(false);
    }
  };

  const generatePromptSequentially = async (index: number, currentScenes: Scene[]) => {
    const updated = [...currentScenes];
    updated[index].status = 'generating';
    setScenes([...updated]);

    try {
      updated[index].prompt = await generateScenePrompt(updated[index].text, style);
      updated[index].status = 'ready';
    } catch (e) {
      console.error("Sequential Gen Error:", e);
      updated[index].status = 'pending';
    }
    setScenes([...updated]);
  };

  const generateImage = async (index: number) => {
    setIsGenerating(prev => ({ ...prev, [index]: true }));
    setError(null);
    try {
      const url = await requestImage(scenes[index].prompt);

      const updated = [...scenes];
      updated[index].selectedImage = url;
      setScenes(updated);
    } catch (err) {
      console.error("Image Gen Error:", err);
      setError("Visual synthesis nodes are at capacity. Retry in a moment.");
    } finally {
      setIsGenerating(prev => ({ ...prev, [index]: false }));
    }
  };

  const generateAllImages = async () => {
    for (let i = 0; i < scenes.length; i++) {
       if (!scenes[i].selectedImage && scenes[i].prompt) {
         await generateImage(i);
       }
    }
  };

  const allReady = scenes.length > 0 && scenes.every(s => s.selectedImage);

  if (isSplitting) {
    return (
      <div className="flex flex-col items-center justify-center p-20 py-32">
        <LoadingDonut />
        <p className="mt-10 text-zinc-400 animate-pulse font-black uppercase tracking-[0.3em] text-xs">Architecting Visual Sequence...</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto pb-64">
      <div className="text-center mb-16">
        <div className="inline-flex items-center space-x-2 px-4 py-2 bg-brand-primary/10 text-brand-primary rounded-full mb-6">
           <ImageIcon className="w-4 h-4" />
           <span className="text-[10px] font-black uppercase tracking-[0.2em]">Phase Five / Visual Synthesis</span>
        </div>
        <h2 className="text-5xl font-salena text-zinc-900 tracking-tighter mb-4">Visual Manifestation</h2>
        <p className="text-zinc-400 font-medium text-lg max-w-2xl mx-auto italic">Refining prompts and synthesizing cinematic assets for your narrative.</p>
        
        <div className="mt-8 flex justify-center space-x-4">
          <button 
            onClick={generateAllImages}
            disabled={Object.values(isGenerating).some(v => v)}
            className="btn-primary px-10 py-5 flex items-center space-x-3 group"
          >
            <Sparkles className="w-5 h-5 group-hover:rotate-12 transition-transform" />
            <span>SYNTHESIZE ALL VISUALS</span>
          </button>
        </div>

        {error && (
          <div className="mt-6 p-4 bg-red-50 text-red-600 rounded-2xl text-xs font-black uppercase tracking-widest border border-red-100 max-w-md mx-auto flex items-center justify-center space-x-2">
             <AlertCircle className="w-4 h-4" />
             <span>{error}</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-12">
        {scenes.map((scene, index) => (
          <motion.div
            key={scene.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className={cn(
               "glass-pane !p-0 overflow-hidden grid grid-cols-1 lg:grid-cols-2 min-h-[500px] border-2",
               index % 2 === 0 ? "border-brand-primary/10" : "border-brand-secondary/10"
            )}
          >
            {/* Left Side: Script & Prompt */}
            <div className="p-10 flex flex-col justify-between bg-white/30 backdrop-blur-sm">
               <div className="space-y-8">
                 <div className="flex items-center justify-between">
                    <span className="text-3xl font-salena italic text-zinc-300">#0{scene.id}</span>
                    <span className="px-3 py-1 bg-zinc-100 text-zinc-400 text-[9px] font-black uppercase tracking-widest rounded-md">{style}</span>
                 </div>

                 {/* Script Label Change: Narrator -> Script */}
                 <div className="space-y-3">
                    <div className="flex items-center space-x-2 px-2">
                       <Film className="w-4 h-4 text-zinc-400" />
                       <span className="text-[10px] font-black text-zinc-400 uppercase tracking-widest">Script Segment</span>
                    </div>
                    <div className="p-6 bg-white/80 rounded-2xl text-sm font-medium text-zinc-800 leading-relaxed italic border border-zinc-100">
                       {scene.text}
                    </div>
                 </div>

                 <div className="space-y-4">
                    <div className="flex items-center justify-between px-2">
                       <div className="flex items-center space-x-2">
                          <Wand2 className="w-4 h-4 text-brand-primary" />
                          <span className="text-[10px] font-black text-zinc-400 uppercase tracking-widest">Visual AI Prompt</span>
                       </div>
                       <button 
                         onClick={() => generatePromptSequentially(index, scenes)}
                         className="text-[9px] font-black uppercase tracking-widest text-brand-primary hover:bg-brand-primary/5 px-3 py-1 rounded-lg transition-all flex items-center space-x-1"
                       >
                         <RefreshCw className={cn("w-3 h-3", scene.status === 'generating' && "animate-spin")} />
                         <span>Regen</span>
                       </button>
                    </div>
                    <textarea
                       className="w-full p-6 bg-zinc-900 rounded-3xl text-xs font-mono text-[#c6e9c8] border-2 border-transparent focus:border-brand-primary/30 outline-none transition-all h-32 leading-relaxed"
                       value={scene.prompt}
                       onChange={(e) => {
                         const updated = [...scenes];
                         updated[index].prompt = e.target.value;
                         setScenes(updated);
                       }}
                    />
                 </div>
               </div>

               <div className="mt-8">
                  <button 
                    onClick={() => generateImage(index)}
                    disabled={isGenerating[index] || !scene.prompt}
                    className={cn(
                      "w-full py-4 rounded-2xl font-black text-xs uppercase tracking-widest transition-all flex items-center justify-center space-x-3",
                      scene.selectedImage ? "bg-zinc-100 text-zinc-400 hover:bg-zinc-200" : "bg-zinc-900 text-white hover:bg-brand-primary"
                    )}
                  >
                    {isGenerating[index] ? <LoadingDonut /> : (
                      <>
                        <Sparkles className="w-4 h-4" />
                        <span>{scene.selectedImage ? "REFINE ASSET" : "GENERATE VISUAL"}</span>
                      </>
                    )}
                  </button>
               </div>
            </div>

            {/* Right Side: Image Result */}
            <div className="relative bg-zinc-900 overflow-hidden min-h-[300px]">
               {scene.selectedImage ? (
                  <motion.img 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    src={scene.selectedImage} 
                    className="w-full h-full object-cover"
                    referrerPolicy="no-referrer"
                  />
               ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center text-zinc-700 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-zinc-800 to-zinc-900 px-12 text-center">
                     {isGenerating[index] ? (
                       <div className="flex flex-col items-center">
                         <LoadingDonut />
                         <span className="mt-6 text-[10px] font-black uppercase tracking-[0.2em] text-white/40 animate-pulse">Neural Rendering...</span>
                       </div>
                     ) : (
                       <>
                         <ImageIcon className="w-20 h-20 opacity-10 mb-6" />
                         <p className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-600">Awaiting Synthesis</p>
                       </>
                     )}
                  </div>
               )}

               {scene.selectedImage && (
                 <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent pointer-events-none" />
               )}

               <div className="absolute top-6 right-6">
                 {scene.selectedImage && (
                   <div className="flex items-center space-x-2 px-4 py-2 bg-green-500/20 backdrop-blur-md border border-green-500/30 rounded-full">
                      <Check className="w-3 h-3 text-green-400" />
                      <span className="text-[9px] font-black text-green-400 uppercase tracking-widest">Mastered Asset</span>
                   </div>
                 )}
               </div>
            </div>
          </motion.div>
        ))}
      </div>

      {allReady && (
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="fixed bottom-12 left-1/2 -translate-x-1/2 w-full max-w-4xl bg-zinc-900 p-8 rounded-[40px] shadow-2xl flex items-center justify-between border-4 border-zinc-800 z-50 overflow-hidden"
        >
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-brand-primary via-brand-secondary to-brand-accent" />
          
          <div className="flex items-center space-x-6 px-4">
            <div className="w-16 h-16 bg-white/5 rounded-2xl flex items-center justify-center border border-white/10">
               <ImageIcon className="w-8 h-8 text-brand-primary" />
            </div>
            <div>
              <h4 className="text-white font-black text-2xl tracking-tighter italic uppercase">Production Ready</h4>
              <p className="text-zinc-500 text-[10px] font-black uppercase tracking-[0.4em]">Visual storyboard finalized</p>
            </div>
          </div>

          <button 
            onClick={() => onNext(scenes)}
            className="px-12 py-5 bg-white text-zinc-900 rounded-[28px] font-black text-sm uppercase tracking-widest hover:bg-brand-primary hover:text-white transition-all shadow-xl flex items-center space-x-3"
          >
            <span>PROCEED TO MOTION</span>
            <ChevronRight className="w-5 h-5" />
          </button>
        </motion.div>
      )}
    </div>
  );
}
