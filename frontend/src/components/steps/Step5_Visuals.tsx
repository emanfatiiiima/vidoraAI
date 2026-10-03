import React, { useState, useEffect } from "react";
import { motion } from "motion/react";
import { Image as ImageIcon, Sparkles, Wand2, RefreshCw, ChevronRight, Check, Film } from "lucide-react";
import LoadingDonut, { Spinner } from "../ui/LoadingDonut";
import StepHeader from "../ui/StepHeader";
import StepFooter from "../ui/StepFooter";
import Notice from "../ui/Notice";
import { cn } from "../../lib/utils";
import { generateImage as requestImage, generateScenePrompt, splitScriptIntoScenes, type ImageProvider } from "../../services/api";

const IMAGE_AI_OPTIONS: { id: ImageProvider; label: string }[] = [
  { id: "openai", label: "ChatGPT" },
  { id: "leonardo", label: "Leonardo" },
  { id: "gemini", label: "Gemini" },
];

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
  // The image AI the user picked. UI only for now; wiring to the backend comes later.
  const [imageProvider, setImageProvider] = useState<ImageProvider>("openai");

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
      setError("Couldn't split the script into scenes. Please go back and try again.");
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
      setError("Image generation is busy right now. Please try again in a moment.");
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
      <div className="flex items-center justify-center py-24">
        <LoadingDonut label="Splitting your script into scenes..." />
      </div>
    );
  }

  const readyCount = scenes.filter(s => s.selectedImage).length;
  const isBusy = Object.values(isGenerating).some(v => v);

  return (
    <div className="max-w-5xl mx-auto">
      <StepHeader
        icon={<ImageIcon />}
        eyebrow="Step 5 · Images"
        title="Scene images"
        description="Review the AI prompt for each scene, then generate its image."
        actions={
          <>
            <button onClick={generateAllImages} disabled={isBusy} className="btn-primary">
              {isBusy ? <Spinner /> : <Sparkles className="w-4 h-4" />}
              <span>{isBusy ? "Generating..." : "Generate all images"}</span>
            </button>
            <div className="inline-flex items-center gap-1 p-1 bg-white/70 rounded-xl border border-black/5" role="group" aria-label="Image AI">
              {IMAGE_AI_OPTIONS.map(option => (
                <button
                  key={option.id}
                  onClick={() => setImageProvider(option.id)}
                  disabled={isBusy}
                  aria-pressed={imageProvider === option.id}
                  title={`Generate images with ${option.label}`}
                  className={cn(
                    "px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors disabled:cursor-not-allowed",
                    imageProvider === option.id ? "bg-zinc-900 text-white" : "text-zinc-600 hover:text-zinc-900"
                  )}
                >
                  {option.label}
                </button>
              ))}
            </div>
            <span className="self-center text-sm text-zinc-500">{readyCount} of {scenes.length} ready</span>
          </>
        }
      />

      {error && <Notice className="mb-6" onDismiss={() => setError(null)}>{error}</Notice>}

      <div className="space-y-5">
        {scenes.map((scene, index) => (
          <motion.div
            key={scene.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="glass-pane !p-0 overflow-hidden grid grid-cols-1 lg:grid-cols-5"
          >
            {/* Script + prompt */}
            <div className="lg:col-span-3 p-5 md:p-6 flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-zinc-900">Scene {scene.id}</span>
                <span className="chip">{style}</span>
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center gap-1.5 field-label">
                  <Film className="w-3.5 h-3.5" /> Script
                </div>
                <p className="px-3.5 py-2.5 bg-white/80 rounded-xl text-sm text-zinc-700 leading-relaxed border border-black/5">
                  {scene.text}
                </p>
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 field-label">
                    <Wand2 className="w-3.5 h-3.5" /> Image prompt
                  </div>
                  <button
                    onClick={() => generatePromptSequentially(index, scenes)}
                    className="text-xs font-semibold text-brand-primary hover:bg-white/60 px-2 py-1 rounded-md transition flex items-center gap-1"
                  >
                    <RefreshCw className={cn("w-3 h-3", scene.status === 'generating' && "animate-spin")} />
                    Rewrite
                  </button>
                </div>
                <textarea
                  className="w-full px-3.5 py-2.5 bg-zinc-900 rounded-xl text-xs font-mono text-[var(--color-done-green)] border border-transparent focus:border-brand-primary/40 outline-none transition h-24 leading-relaxed resize-none"
                  value={scene.prompt}
                  placeholder={scene.status === 'generating' ? "Writing prompt..." : ""}
                  onChange={(e) => {
                    const updated = [...scenes];
                    updated[index].prompt = e.target.value;
                    setScenes(updated);
                  }}
                />
              </div>

              <button
                onClick={() => generateImage(index)}
                disabled={isGenerating[index] || !scene.prompt}
                className={cn("self-start", scene.selectedImage ? "btn-ghost" : "btn-dark")}
              >
                {isGenerating[index] ? <Spinner /> : scene.selectedImage ? <RefreshCw className="w-4 h-4" /> : <Sparkles className="w-4 h-4" />}
                <span>{isGenerating[index] ? "Generating..." : scene.selectedImage ? "Regenerate image" : "Generate image"}</span>
              </button>
            </div>

            {/* Image */}
            <div className="lg:col-span-2 relative bg-zinc-900 min-h-56">
              {scene.selectedImage ? (
                <motion.img
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  src={scene.selectedImage}
                  alt={`Scene ${scene.id}`}
                  className="absolute inset-0 w-full h-full object-cover"
                  referrerPolicy="no-referrer"
                />
              ) : (
                <div className="absolute inset-0 flex flex-col items-center justify-center text-zinc-500 text-center px-6">
                  {isGenerating[index] ? (
                    <>
                      <Spinner className="w-6 h-6 mb-2 text-zinc-400" />
                      <span className="text-xs">Rendering image...</span>
                    </>
                  ) : (
                    <>
                      <ImageIcon className="w-8 h-8 opacity-30 mb-2" />
                      <span className="text-xs">No image yet</span>
                    </>
                  )}
                </div>
              )}

              {scene.selectedImage && (
                <div className="absolute top-3 right-3 flex items-center gap-1 px-2 py-1 bg-black/50 backdrop-blur rounded-md text-xs font-medium text-emerald-300">
                  <Check className="w-3 h-3" /> Ready
                </div>
              )}
            </div>
          </motion.div>
        ))}
      </div>

      {allReady && (
        <StepFooter
          icon={<ImageIcon />}
          title="All images ready"
          description="Your visual storyboard is complete."
          action={
            <button onClick={() => onNext(scenes)} className="btn-primary">
              <span>Continue to videos</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          }
        />
      )}
    </div>
  );
}
