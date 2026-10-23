import React, { useState } from "react";
import { motion } from "motion/react";
import { Video, Sparkles, Play, RefreshCw, ChevronRight, Check, AlertCircle, Film } from "lucide-react";
import { Spinner } from "../ui/LoadingDonut";
import StepHeader from "../ui/StepHeader";
import StepFooter from "../ui/StepFooter";
import Notice from "../ui/Notice";
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
      setError("Couldn't generate the clip. Please try again.");
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
  const readyCount = scenes.filter(s => s.videoUrl).length;
  const isBusy = Object.values(isGenerating).some(v => v);

  return (
    <div className="max-w-5xl mx-auto">
      <StepHeader
        icon={<Film />}
        eyebrow="Step 6 · Videos"
        title="Scene clips"
        description="Turn each scene image into a short animated clip."
        tone="secondary"
        actions={
          <>
            <button onClick={generateAll} disabled={isBusy} className="btn-secondary">
              {isBusy ? <Spinner /> : <Sparkles className="w-4 h-4" />}
              <span>{isBusy ? "Generating..." : "Generate all clips"}</span>
            </button>
            <span className="self-center text-sm text-zinc-500">{readyCount} of {scenes.length} ready</span>
          </>
        }
      />

      {error && <Notice className="mb-6" onDismiss={() => setError(null)}>{error}</Notice>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {scenes.map((scene, index) => (
          <motion.div
            key={scene.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="surface overflow-hidden flex flex-col"
          >
            {/* Video / source image */}
            <div className="relative aspect-video bg-zinc-900 overflow-hidden">
              {scene.videoUrl ? (
                <video
                  src={scene.videoUrl}
                  poster={scene.selectedImage || undefined}
                  autoPlay
                  loop
                  muted
                  playsInline
                  className="w-full h-full object-cover"
                />
              ) : scene.selectedImage ? (
                <>
                  <img
                    src={scene.selectedImage}
                    alt={`Scene ${scene.id}`}
                    className="w-full h-full object-cover opacity-50"
                    referrerPolicy="no-referrer"
                  />
                  <div className="absolute inset-0 flex flex-col items-center justify-center text-white">
                    {isGenerating[index] ? (
                      <>
                        <Spinner className="w-6 h-6 mb-2" />
                        <span className="text-xs">Animating...</span>
                      </>
                    ) : (
                      <div className="w-11 h-11 bg-white/15 rounded-full flex items-center justify-center backdrop-blur border border-white/20">
                        <Play className="w-4 h-4 ml-0.5" />
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="w-full h-full flex items-center justify-center text-zinc-600">
                  <AlertCircle className="w-8 h-8 opacity-40" />
                </div>
              )}

              <div className="absolute top-3 left-3 px-2 py-1 bg-black/50 backdrop-blur rounded-md flex items-center gap-1.5 text-xs font-medium text-white">
                <span className={cn("w-1.5 h-1.5 rounded-full", scene.videoUrl ? "bg-brand-secondary" : "bg-zinc-400")} />
                Clip {scene.id}
              </div>
            </div>

            {/* Details */}
            <div className="p-4 flex-grow flex flex-col gap-3">
              <p className="text-sm text-zinc-600 leading-relaxed line-clamp-2">{scene.text}</p>
              <div className="mt-auto flex items-center justify-between gap-3">
                {scene.videoUrl ? (
                  <span className="text-xs font-semibold text-emerald-600 flex items-center gap-1">
                    <Check className="w-3.5 h-3.5" /> Ready
                  </span>
                ) : <span />}
                <button
                  onClick={() => generateVideo(index)}
                  disabled={isGenerating[index] || !scene.selectedImage}
                  className={cn("btn-sm", scene.videoUrl ? "btn-ghost" : "btn-dark")}
                >
                  {isGenerating[index] ? <Spinner className="w-3.5 h-3.5" /> : scene.videoUrl ? <RefreshCw className="w-3.5 h-3.5" /> : <Sparkles className="w-3.5 h-3.5" />}
                  <span>{scene.videoUrl ? "Regenerate" : "Generate clip"}</span>
                </button>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {allReady && (
        <StepFooter
          icon={<Video />}
          title="All clips ready"
          description="Next, we'll combine the clips with your narration."
          action={
            <button onClick={() => onNext(scenes)} className="btn-primary">
              <span>Continue to render</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          }
        />
      )}
    </div>
  );
}
