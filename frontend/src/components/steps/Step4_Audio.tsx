import { useState } from "react";
import { motion } from "motion/react";
import { Mic, Download, Play, Pause, Wand2, Volume2, Settings2, Sliders, Check, ArrowRight, ChevronRight } from "lucide-react";
import LoadingDonut from "../ui/LoadingDonut";
import { cn } from "../../lib/utils";
import { ApiError, generateSpeech } from "../../services/api";

interface Step4Props {
  script: string;
  onNext: (audioUrl: string) => void;
  initialAudio?: string | null;
  key?: string;
}

export default function Step4_Audio({ script, onNext, initialAudio }: Step4Props) {
  const [voice, setVoice] = useState("Sierra"); 
  const [speed, setSpeed] = useState(0); // -1.0 to 1.0
  const [pitch, setPitch] = useState(1.0); // 0.5 to 1.5
  const [isGenerating, setIsGenerating] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(initialAudio || null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isConfirmed, setIsConfirmed] = useState(!!initialAudio);
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(initialAudio ? new Audio(initialAudio) : null);

  const voices = [
    { id: "Sierra", name: "Sierra", desc: "Professional & Balanced", type: "Female" },
    { id: "Mateo", name: "Mateo", desc: "Deep & Authoritative", type: "Male" },
    { id: "Scarlett", name: "Scarlett", desc: "Expressive & Warm", type: "Female" },
    { id: "Dan", name: "Dan", desc: "Friendly & Casual", type: "Male" },
    { id: "Liv", name: "Liv", desc: "Young & Energetic", type: "Female" },
    { id: "Will", name: "Will", desc: "News Anchor Style", type: "Male" },
  ];

  const generateAudio = async () => {
    setIsGenerating(true);
    setAudioUrl(null);
    setIsConfirmed(false);
    try {
      // TTS runs on the backend (core/services/audio.py).
      const url = await generateSpeech({ text: script, voice, speed, pitch });

      setAudioUrl(url);
      const audio = new Audio(url);
      audio.onended = () => setIsPlaying(false);
      setAudioElement(audio);
    } catch (error) {
      console.error("Audio Gen Error:", error);
      const serverError = describeError(error);
      alert(`Audio synthesis failed: ${serverError}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const togglePlayback = () => {
    if (!audioElement) return;
    if (isPlaying) {
      audioElement.pause();
    } else {
      audioElement.play();
    }
    setIsPlaying(!isPlaying);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="max-w-6xl mx-auto space-y-16 pb-32"
    >
      <div className="text-center">
        <div className="inline-flex items-center space-x-2 px-4 py-2 bg-brand-accent/10 text-brand-accent rounded-full mb-6">
          <Volume2 className="w-4 h-4" />
          <span className="text-[10px] font-black uppercase tracking-[0.2em]">Phase Four</span>
        </div>
        <h2 className="text-5xl font-salena text-zinc-900 mb-6 tracking-tighter">Vocal Delivery</h2>
        <p className="text-zinc-400 font-medium text-lg leading-relaxed max-w-2xl mx-auto">Synthetic narration that feels human. Refine the voice parameters to match your production tone.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
        {/* Voice Selection */}
        <div className="lg:col-span-1 space-y-6">
          <label className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.2em] px-2 block">Choose Script Voice</label>
          <div className="grid grid-cols-1 gap-3 max-h-[600px] overflow-y-auto pr-2 no-scrollbar">
            {voices.map((v) => (
              <button 
                key={v.id}
                onClick={() => setVoice(v.id)}
                className={cn(
                  "p-5 rounded-3xl font-black border-2 transition-all text-left flex items-center justify-between group",
                  voice === v.id 
                    ? "bg-brand-primary/5 border-brand-primary text-brand-primary" 
                    : "bg-white border-zinc-100 text-zinc-400 hover:border-zinc-200"
                )}
              >
                <div className="flex items-center space-x-4">
                  <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center transition-all", voice === v.id ? "bg-brand-primary text-white" : "bg-zinc-100 text-zinc-400")}>
                    <Mic className="w-5 h-5" />
                  </div>
                  <div>
                    <p className={cn("font-black tracking-tight text-sm", voice === v.id ? "text-zinc-900" : "text-zinc-400")}>{v.name}</p>
                    <p className="text-[9px] font-bold opacity-60 uppercase tracking-tighter">{v.desc}</p>
                  </div>
                </div>
                {voice === v.id && <Check className="w-4 h-4 text-brand-primary" />}
              </button>
            ))}
          </div>
        </div>

        {/* Parameters */}
        <div className="lg:col-span-1 space-y-10">
           <div className="glass-pane !p-8 space-y-10">
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <label className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.2em]">Voice Speed</label>
                  <span className="text-[10px] font-black text-brand-primary">{speed.toFixed(1)}x</span>
                </div>
                <input 
                   type="range"
                   min="-1"
                   max="1"
                   step="0.1"
                   value={speed}
                   onChange={(e) => setSpeed(parseFloat(e.target.value))}
                   className="w-full accent-brand-primary"
                />
                <div className="flex justify-between text-[8px] font-black text-zinc-300 uppercase tracking-widest">
                  <span>Slow</span>
                  <span>Normal</span>
                  <span>Fast</span>
                </div>
              </div>

              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <label className="text-[10px] font-black text-zinc-400 uppercase tracking-[0.2em]">Pitch Shift</label>
                  <span className="text-[10px] font-black text-brand-secondary">{pitch.toFixed(1)}</span>
                </div>
                <input 
                   type="range"
                   min="0.5"
                   max="1.5"
                   step="0.1"
                   value={pitch}
                   onChange={(e) => setPitch(parseFloat(e.target.value))}
                   className="w-full accent-brand-secondary"
                />
                <div className="flex justify-between text-[8px] font-black text-zinc-300 uppercase tracking-widest">
                  <span>Deep</span>
                  <span>Neutral</span>
                  <span>High</span>
                </div>
              </div>

              <button
                onClick={generateAudio}
                disabled={isGenerating}
                className="w-full btn-primary py-5 flex items-center justify-center space-x-3"
              >
                {isGenerating ? <LoadingDonut /> : (
                  <>
                    <Wand2 className="w-5 h-5" />
                    <span>GENERATE SYNTHESIS</span>
                  </>
                )}
              </button>
           </div>
        </div>

        {/* Preview */}
        <div className="lg:col-span-1">
          <div className="relative group h-full">
            <div className="absolute inset-0 bg-brand-primary/20 blur-[60px] rounded-full opacity-20" />
            <div className="relative glass-pane !bg-zinc-900 h-full flex flex-col justify-center items-center overflow-hidden border-zinc-800 border-4 min-h-[400px]">
              {audioUrl ? (
                <div className="relative z-10 flex flex-col items-center space-y-10 w-full px-8 text-center">
                  <div className="space-y-2">
                     <h4 className="text-white font-black text-3xl tracking-tighter italic">VOICE READY</h4>
                     <p className="text-brand-primary text-[10px] font-black uppercase tracking-[0.3em]">{voice} MASTERED</p>
                  </div>

                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={togglePlayback}
                    className="w-24 h-24 bg-white text-zinc-900 rounded-full flex items-center justify-center shadow-2xl"
                  >
                    {isPlaying ? <Pause className="w-10 h-10" /> : <Play className="w-10 h-10 ml-1" />}
                  </motion.button>

                  <div className="w-full space-y-3">
                    {!isConfirmed && (
                      <button 
                        onClick={() => setIsConfirmed(true)}
                        className="w-full py-4 bg-brand-primary text-white rounded-2xl font-black tracking-widest text-[10px] uppercase transition-all shadow-lg shadow-brand-primary/20"
                      >
                        CONFIRM VOCALS
                      </button>
                    )}
                    {isConfirmed && (
                      <motion.button
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        onClick={() => onNext(audioUrl)}
                        className="w-full py-5 bg-white text-zinc-900 font-black rounded-2xl shadow-2xl flex items-center justify-center gap-3 text-sm"
                      >
                         <span>PROCEED</span>
                         <ArrowRight className="w-4 h-4" />
                      </motion.button>
                    )}
                  </div>
                </div>
              ) : (
                <div className="relative z-10 text-center opacity-30 px-10">
                  <Volume2 className="w-16 h-16 text-white mx-auto mb-6" />
                  <p className="text-white text-xs font-black uppercase tracking-[0.2em]">Awaiting Synthesis</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

/** Human-readable message for an audio error (prefers upstream provider details). */
function describeError(error: unknown): string {
  if (error instanceof ApiError && error.details) {
    return typeof error.details === "string" ? error.details : JSON.stringify(error.details);
  }
  return error instanceof Error ? error.message : String(error);
}
