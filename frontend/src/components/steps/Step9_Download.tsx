import React, { useState } from "react";
import { motion } from "motion/react";
import { Download, Youtube, Share, Sparkles, Film, Award, FileSpreadsheet, Image as ImageIcon, Music } from "lucide-react";
import { saveAs } from "file-saver";
import { Spinner } from "../ui/LoadingDonut";
import StepHeader from "../ui/StepHeader";
import Notice from "../ui/Notice";
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
      setDownloadError("Couldn't create the ZIP. Please try again.");
    } finally {
      setIsPackaging(false);
    }
  };

  const packageContents = [
    { icon: <FileSpreadsheet className="w-4 h-4" />, label: "Project details (Excel) & script" },
    { icon: <ImageIcon className="w-4 h-4" />, label: "Scene images" },
    { icon: <Film className="w-4 h-4" />, label: "Scene clips & final video" },
    { icon: <Music className="w-4 h-4" />, label: "Narration audio" },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-5xl mx-auto"
    >
      <StepHeader
        icon={<Award />}
        eyebrow="Step 8 · Download"
        title="Your video is ready"
        description="Preview the final cut and download everything in one ZIP."
        tone="secondary"
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Video preview */}
        <div className="lg:col-span-2 rounded-3xl bg-zinc-900 p-2 shadow-lg">
          <div className="relative aspect-video rounded-2xl overflow-hidden">
            <video src={videoUrl} controls autoPlay loop className="w-full h-full object-cover" />
            <div className="absolute top-3 left-3 px-2.5 py-1 bg-black/50 backdrop-blur rounded-md flex items-center gap-1.5 text-xs font-medium text-white pointer-events-none">
              <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full" />
              Final video
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="space-y-4">
          <div className="glass-pane space-y-4">
            <div>
              <h3 className="text-lg font-salena font-bold text-zinc-900">Download package</h3>
              <p className="text-sm text-zinc-600 mt-0.5">One ZIP file with everything:</p>
            </div>
            <ul className="space-y-2">
              {packageContents.map(item => (
                <li key={item.label} className="flex items-center gap-2.5 text-sm text-zinc-700">
                  <span className="w-7 h-7 rounded-lg bg-white/70 flex items-center justify-center text-zinc-600">{item.icon}</span>
                  {item.label}
                </li>
              ))}
            </ul>

            <button onClick={handleDownload} disabled={!project || isPackaging} className="btn-dark w-full">
              {isPackaging ? <Spinner /> : <Download className="w-4 h-4" />}
              <span>{isPackaging ? "Preparing ZIP..." : "Download ZIP"}</span>
            </button>
            {isPackaging && <p className="text-xs text-zinc-600 text-center">This can take up to a minute.</p>}
            {downloadError && <Notice onDismiss={() => setDownloadError(null)}>{downloadError}</Notice>}
          </div>

          <div className="surface p-4 space-y-2">
            <button disabled className="btn-ghost w-full justify-between" title="Coming soon">
              <span className="flex items-center gap-2"><Youtube className="w-4 h-4 text-red-500" /> Upload to YouTube</span>
              <span className="text-[11px] font-semibold text-zinc-400">Soon</span>
            </button>
            <button disabled className="btn-ghost w-full justify-between" title="Coming soon">
              <span className="flex items-center gap-2"><Share className="w-4 h-4" /> Share link</span>
              <span className="text-[11px] font-semibold text-zinc-400">Soon</span>
            </button>
          </div>

          <button onClick={onReset} className="btn-ghost w-full">
            <Sparkles className="w-4 h-4" />
            <span>Create a new video</span>
          </button>
        </div>
      </div>
    </motion.div>
  );
}
