import React, { useState } from "react";
import { motion } from "motion/react";
import { Video, Sparkles, Play, RefreshCw, ChevronRight, Check, AlertCircle, Film } from "lucide-react";
import LoadingDonut from "../ui/LoadingDonut";
import { cn } from "../../lib/utils";
import { generateSceneVideo } from "../../services/api";

interface Scene {
  id: number;
  text: string;
  selectedImage: string | null;
  videoUrl?: string | null;
}

interface Step7Props {
  scenes: Scene[];
  onNext: (updatedScenes: Scene[]) => void;
}

export default function Step7_Videos({ scenes: initialScenes, onNext }: Step7Props) {
  const [scenes, setScenes] = useState<Scene[]>(initialScenes);
  const [isGenerating, setIsGenerating] = useState<Record<number, boolean>>({});
  const [error, setError] = useState<string | null>(null);

  const generateVideo = async (index: number) => {
    if (!scenes[index].selectedImage) return;

    setIsGenerating(prev => ({ ...prev, [index]: true }));
    setError(null);
    try {
      const url = await generateSceneVideo(scenes[index].selectedImage!, scenes[index].text);

      const updated = [...scenes];
      updated[index].videoUrl = url;
      setScenes(updated);
    } catch (err) {
      console.error("Video Gen Error:", err);
      setError("Failed to synthesize motion. Neural network busy.");
    } finally {
      setIsGenerating(prev => ({ ...prev, [index]: false }));
    }
  };

  const generateAll = async () => {
    for (let i = 0; i < scenes.length; i++) {
       if (!scenes[i].videoUrl && scenes[i].selectedImage) {
         await generateVideo(i);
       }
    }
  };

  const allReady = scenes.every(s => s.videoUrl);

  return (
    <div className="max-w-6xl mx-auto pb-64">
      <div className="text-center mb-16">
        <div className="inline-flex items-center space-x-2 px-4 py-2 bg-brand-secondary/10 text-brand-secondary rounded-full mb-6">
           <Film className="w-4 h-4" />
           <span className="text-[10px] font-black uppercase tracking-[0.2em]">Phase Seven / Motion Synthesis</span>
        </div>
        <h2 className="text-5xl font-salena text-zinc-900 tracking-tighter mb-4">Cinematic Motion</h2>
        <p className="text-zinc-400 font-medium text-lg max-w-2xl mx-auto italic">Applying temporal consistency and fluid motion to your static assets.</p>
        
        <div className="mt-8 flex justify-center space-x-4">
          <button 
            onClick={generateAll}
            disabled={Object.values(isGenerating).some(v => v)}
            className="btn-secondary px-10 py-5 flex items-center space-x-3 group"
          >
            <Sparkles className="w-5 h-5 group-hover:rotate-12 transition-transform" />
            <span>SYNTHESIZE ALL CLIPS</span>
          </button>
        </div>

        {error && (
          <div className="mt-6 p-4 bg-red-50 text-red-600 rounded-2xl text-xs font-black uppercase tracking-widest border border-red-100 max-w-md mx-auto flex items-center justify-center space-x-2">
             <AlertCircle className="w-4 h-4" />
             <span>{error}</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {scenes.map((scene, index) => (
          <motion.div
            key={scene.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="glass-pane !p-0 overflow-hidden flex flex-col group min-h-[450px] border-zinc-200"
          >
            {/* Video Container */}
            <div className="relative aspect-video bg-black overflow-hidden">
               {scene.videoUrl ? (
                 <video 
                   src={scene.videoUrl} 
                   autoPlay 
                   loop 
                   muted 
                   playsInline
                   className="w-full h-full object-cover"
                 />
               ) : scene.selectedImage ? (
                 <div className="relative w-full h-full">
                    <img 
                      src={scene.selectedImage} 
                      alt="Source" 
                      className="w-full h-full object-cover opacity-40 blur-sm"
                      referrerPolicy="no-referrer"
                    />
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                       {isGenerating[index] ? (
                         <div className="flex flex-col items-center">
                            <LoadingDonut />
                            <span className="mt-4 text-[9px] font-black uppercase tracking-[0.2em] text-white/60">Simulating Motion...</span>
                         </div>
                       ) : (
                         <div className="w-16 h-16 bg-white/10 rounded-full flex items-center justify-center backdrop-blur-md border border-white/20">
                            <Play className="w-6 h-6 text-white opacity-50" />
                         </div>
                       )}
                    </div>
                 </div>
               ) : (
                 <div className="w-full h-full flex items-center justify-center text-zinc-800">
                    <AlertCircle className="w-12 h-12 opacity-20" />
                 </div>
               )}

               <div className="absolute top-4 left-4 h-8 px-4 bg-black/60 backdrop-blur-md rounded-full flex items-center space-x-2 border border-white/10">
                  <div className={cn("w-2 h-2 rounded-full", scene.videoUrl ? "bg-brand-secondary" : "bg-zinc-600")} />
                  <span className="text-[9px] font-black text-white uppercase tracking-widest">Clip 0{scene.id}</span>
               </div>
            </div>

            {/* Controls Area */}
            <div className="p-8 flex-grow flex flex-col justify-between">
               <div className="space-y-4">
                 <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                       <Video className="w-4 h-4 text-brand-secondary" />
                       <span className="text-[10px] font-black text-zinc-400 uppercase tracking-widest">Motion Profile</span>
                    </div>
                    {scene.videoUrl && (
                      <span className="text-[10px] font-black text-green-500 uppercase tracking-widest flex items-center gap-1">
                        <Check className="w-3 h-3" /> Mastered
                      </span>
                    )}
                 </div>
                 <p className="text-zinc-600 text-sm font-medium leading-relaxed italic line-clamp-2">
                   "{scene.text}"
                 </p>
               </div>

               <div className="mt-8">
                 {!scene.videoUrl ? (
                   <button 
                      onClick={() => generateVideo(index)}
                      disabled={isGenerating[index] || !scene.selectedImage}
                      className="w-full py-4 bg-zinc-900 text-white rounded-2xl font-black text-xs uppercase tracking-widest hover:bg-brand-secondary transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
                   >
                     {isGenerating[index] ? <LoadingDonut /> : (
                       <>
                          <Sparkles className="w-4 h-4" />
                          <span>SYNTHESIZE MOTION</span>
                       </>
                     )}
                   </button>
                 ) : (
                   <button 
                      onClick={() => generateVideo(index)}
                      className="w-full py-4 bg-zinc-100 text-zinc-400 rounded-2xl font-black text-xs uppercase tracking-widest hover:bg-zinc-200 transition-all flex items-center justify-center space-x-2"
                   >
                     <RefreshCw className={cn("w-4 h-4", isGenerating[index] && "animate-spin")} />
                     <span>RE-GENERATE CLIP</span>
                   </button>
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
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-brand-secondary via-brand-primary to-brand-accent" />
          
          <div className="flex items-center space-x-6 px-4">
            <div className="w-16 h-16 bg-white/5 rounded-2xl flex items-center justify-center border border-white/10">
               <Video className="w-8 h-8 text-brand-secondary" />
            </div>
            <div>
              <h4 className="text-white font-black text-2xl tracking-tighter italic uppercase">All Clips Mastered</h4>
              <p className="text-zinc-500 text-[10px] font-black uppercase tracking-[0.4em]">Ready for final sequence assembly</p>
            </div>
          </div>

          <button 
            onClick={() => onNext(scenes)}
            className="px-12 py-5 bg-white text-zinc-900 rounded-[28px] font-black text-sm uppercase tracking-widest hover:bg-brand-secondary hover:text-white transition-all shadow-xl flex items-center space-x-3"
          >
            <span>PROCEED TO COMPILE</span>
            <ChevronRight className="w-5 h-5" />
          </button>
        </motion.div>
      )}
    </div>
  );
}
