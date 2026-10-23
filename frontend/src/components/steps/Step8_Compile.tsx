import { useState } from "react";
import { motion } from "motion/react";
import { Cpu, Layers, Music, Check, Play, Film } from "lucide-react";
import LoadingDonut from "../ui/LoadingDonut";
import StepHeader from "../ui/StepHeader";
import Notice from "../ui/Notice";
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

// Visual progress stages shown while the backend renders the video.
const RENDER_STAGES = [
  { p: 10, s: "Checking clips..." },
  { p: 30, s: "Stitching scenes together..." },
  { p: 50, s: "Adding narration..." },
  { p: 75, s: "Applying colour grading..." },
  { p: 90, s: "Encoding final video..." },
];

export default function Step8_Compile({ scenes, audioUrl, onNext }: Step8Props) {
  const [isCompiling, setIsCompiling] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("");
  const [finalUrl, setFinalUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const startCompilation = async () => {
    setIsCompiling(true);
    setError(null);
    setProgress(0);
    setStatus("Starting renderer...");

    for (const stage of RENDER_STAGES) {
      await new Promise(r => setTimeout(r, 1000));
      setProgress(stage.p);
      setStatus(stage.s);
    }

    try {
      setFinalUrl(await compileVideo(scenes, audioUrl));
      setProgress(100);
      setStatus("Your video is ready");
    } catch (e) {
      console.error("Compile Error:", e);
      setError("Rendering failed. Please try again.");
      setIsCompiling(false);
    }
  };

  const features = [
    { icon: <Layers className="w-4 h-4" />, label: `${scenes.length} clips` },
    { icon: <Music className="w-4 h-4" />, label: "Narration" },
    { icon: <Film className="w-4 h-4" />, label: "MP4 export" },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-2xl mx-auto"
    >
      <StepHeader
        icon={<Cpu />}
        eyebrow="Step 7 · Render"
        title="Render final video"
        description="Combine your clips and narration into one video."
        tone="berry"
      />

      {error && <Notice className="mb-6" onDismiss={() => setError(null)}>{error}</Notice>}

      <div className="glass-pane">
        {!isCompiling && !finalUrl ? (
          <div className="text-center space-y-6">
            <div className="flex justify-center gap-2 flex-wrap">
              {features.map(f => (
                <span key={f.label} className="chip !bg-white/80 !py-1.5 !px-3">{f.icon}{f.label}</span>
              ))}
            </div>
            <button onClick={startCompilation} className="btn-primary btn-lg">
              <Cpu className="w-4 h-4" />
              <span>Start rendering</span>
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex flex-col items-center text-center">
              {progress < 100 ? (
                <LoadingDonut />
              ) : (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="w-14 h-14 bg-emerald-500 text-white rounded-full flex items-center justify-center shadow-md"
                >
                  <Check className="w-7 h-7" />
                </motion.div>
              )}
              <p className="mt-4 font-semibold text-zinc-900">{status}</p>
              <p className="text-sm text-zinc-600">{progress}% complete</p>
            </div>

            <div className="h-2 bg-white/70 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                className="h-full bg-gradient-to-r from-brand-berry via-brand-primary to-brand-secondary rounded-full"
              />
            </div>

            {finalUrl && (
              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex justify-center">
                <button onClick={() => onNext(finalUrl)} className="btn-primary">
                  <Play className="w-4 h-4" />
                  <span>Preview & download</span>
                </button>
              </motion.div>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}
