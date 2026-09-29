import React, { useState } from "react";
import { motion } from "motion/react";
import { Download, Youtube, Share, Sparkles, Check, Play, Film, Award, Loader2 } from "lucide-react";
import { saveAs } from "file-saver";
import { cn } from "../../lib/utils";
import { downloadProjectPackage, type ProjectExport } from "../../services/api";

interface Step9Props {
  videoUrl: string;
  onReset: () => void;
  /** All data from previous steps, packaged into the downloadable ZIP. */
  project: ProjectExport | null;
}

export default function Step9_Download({ videoUrl, onReset, project }: Step9Props) {
  const [isPackaging, setIsPackaging] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  // The backend collects every asset into one ZIP (core/services/project_export.py).
  const handleDownload = async () => {
    if (!project || isPackaging) return;
    setIsPackaging(true);
    setDownloadError(null);
    try {
      const blob = await downloadProjectPackage(project);
      const name = project.topic.replace(/[^A-Za-z0-9]+/g, "_").replace(/^_|_$/g, "").slice(0, 50);
      saveAs(blob, `${name || "vidora_project"}.zip`);
    } catch (e) {
      console.error("Download Error:", e);
      setDownloadError("Packaging failed. Please try again.");
    } finally {
      setIsPackaging(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto py-12">
      <div className="text-center mb-16">
        <motion.div 
           initial={{ scale: 0.5, opacity: 0 }}
           animate={{ scale: 1, opacity: 1 }}
           className="w-20 h-20 bg-green-500 text-white rounded-full flex items-center justify-center mx-auto mb-8 shadow-2xl shadow-green-200"
        >
           <Award className="w-10 h-10" />
        </motion.div>
        <h2 className="text-6xl font-salena text-zinc-900 tracking-tighter mb-4">Cinematic Masterpiece Ready</h2>
        <p className="text-zinc-400 font-medium text-xl max-w-2xl mx-auto italic">Your visual narrative has been mastered and is ready for the world.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-12 items-start">
        {/* Video Preview */}
        <div className="lg:col-span-2 space-y-8">
           <div className="glass-pane !p-6 bg-zinc-900 shadow-2xl rounded-[40px] overflow-hidden border-8 border-white">
              <div className="relative aspect-video rounded-[24px] overflow-hidden shadow-inner group">
                 <video 
                   src={videoUrl} 
                   controls 
                   autoPlay 
                   loop 
                   className="w-full h-full object-cover"
                 />
                 
                 <div className="absolute top-6 left-6 h-10 px-6 bg-white/10 backdrop-blur-xl rounded-full flex items-center space-x-3 border border-white/20">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                    <span className="text-xs font-black text-white uppercase tracking-[0.2em]">Master Output v1.0 / 4K</span>
                 </div>
              </div>
           </div>
           
           <div className="flex items-center justify-between p-8 bg-white border border-zinc-200 rounded-[32px] shadow-sm">
              <div className="flex items-center space-x-4">
                 <div className="w-12 h-12 bg-zinc-50 rounded-2xl flex items-center justify-center border border-zinc-100">
                    <Film className="w-6 h-6 text-zinc-400" />
                 </div>
                 <div>
                    <h4 className="font-black text-zinc-900 uppercase tracking-widest text-xs">Technical Profile</h4>
                    <p className="text-zinc-400 text-[10px] font-bold uppercase tracking-widest mt-1">4K UHD | 60FPS | H.265 | Cinematic Log</p>
                 </div>
              </div>
              <div className="text-right">
                 <span className="text-brand-berry font-black text-xs uppercase tracking-widest italic bg-brand-berry/10 px-4 py-2 rounded-full">Neural Quality</span>
              </div>
           </div>
        </div>

        {/* Actions */}
        <div className="space-y-6">
           <div className="glass-pane-berry p-8">
              <h3 className="text-xl font-black text-white uppercase tracking-widest mb-6 italic">Distribute</h3>
              
              <div className="space-y-4">
                 <button 
                    onClick={handleDownload}
                    disabled={!project || isPackaging}
                    className="w-full py-5 bg-white text-zinc-900 rounded-2xl font-black text-xs uppercase tracking-widest hover:scale-105 transition-all flex items-center justify-center space-x-3 shadow-xl disabled:opacity-60 disabled:hover:scale-100"
                 >
                    {isPackaging ? <Loader2 className="w-5 h-5 animate-spin" /> : <Download className="w-5 h-5" />}
                    <span>{isPackaging ? "Packaging..." : "Download Master"}</span>
                 </button>
                 {downloadError && (
                    <p className="text-[10px] font-black text-white uppercase tracking-widest text-center">{downloadError}</p>
                 )}

                 <button 
                    className="w-full py-5 bg-black text-white rounded-2xl font-black text-xs uppercase tracking-widest opacity-50 cursor-not-allowed border border-white/10 flex items-center justify-center space-x-3 group"
                    title="Coming Soon: YouTube Direct Pipeline"
                 >
                    <Youtube className="w-5 h-5 text-red-500" />
                    <span>Upload to YouTube</span>
                    <span className="text-[8px] bg-red-500/20 text-red-400 px-2 py-1 rounded-md ml-2">LOCKED</span>
                 </button>

                 <button 
                    className="w-full py-5 bg-transparent text-white/60 border border-white/20 rounded-2xl font-black text-xs uppercase tracking-widest hover:bg-white/5 transition-all flex items-center justify-center space-x-3"
                 >
                    <Share className="w-5 h-5" />
                    <span>Generate Share Link</span>
                 </button>
              </div>
           </div>

           <div className="glass-pane p-8 border-dashed border-zinc-300">
              <h3 className="text-lg font-black text-zinc-900 uppercase tracking-widest mb-4 italic">Next Cycle</h3>
              <p className="text-zinc-400 text-xs font-medium leading-relaxed mb-6">
                 Initiate a fresh neural synthesis to explore alternative visual strategies and narratives.
              </p>
              <button 
                onClick={onReset}
                className="w-full py-4 bg-zinc-900 text-white rounded-2xl font-black text-xs uppercase tracking-widest hover:bg-brand-primary transition-all flex items-center justify-center space-x-2"
              >
                 <Sparkles className="w-4 h-4" />
                 <span>CREATE NEW VIDEO</span>
              </button>
           </div>
        </div>
      </div>
    </div>
  );
}
