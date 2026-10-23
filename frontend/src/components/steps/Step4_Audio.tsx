import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { Mic, Play, Pause, Wand2, Volume2, Check, ArrowRight } from "lucide-react";
import { Spinner } from "../ui/LoadingDonut";
import StepHeader from "../ui/StepHeader";
import Notice from "../ui/Notice";
import { cn } from "../../lib/utils";
import { describeAIError, type AIChoice } from "../../lib/aiSelection";
import { fetchVoices, generateSpeech, type Voice, type VoiceProvider } from "../../services/api";

interface Step4Props {
  /** The voice-over AI picked in the popup. */
  ai: AIChoice<VoiceProvider>;
  /** Reopens the AI popup. */
  onChangeAI: () => void;
  script: string;
  onNext: (audioUrl: string) => void;
  initialAudio?: string | null;
  key?: string;
}

/** Creates an audio element that resets the play button when playback ends. */
function createAudio(url: string, onEnded: () => void): HTMLAudioElement {
  const audio = new Audio(url);
  audio.onended = onEnded;
  return audio;
}

export default function Step4_Audio({ ai, onChangeAI, script, onNext, initialAudio }: Step4Props) {
  const [voices, setVoices] = useState<Voice[]>([]);
  const [voice, setVoice] = useState("");
  const [speed, setSpeed] = useState(0); // -1.0 to 1.0
  const [pitch, setPitch] = useState(1.0); // 0.5 to 1.5
  const [isGenerating, setIsGenerating] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(initialAudio || null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(
    initialAudio ? createAudio(initialAudio, () => setIsPlaying(false)) : null
  );

  // Only UnrealSpeech supports pitch; local engines only change the speed.
  const supportsPitch = ai.id === "unrealspeech";

  // Stop playback when leaving this step.
  useEffect(() => () => audioElement?.pause(), [audioElement]);

  // Each voice-over AI has its own voices.
  useEffect(() => {
    let cancelled = false;
    fetchVoices(ai.id)
      .then(list => {
        if (cancelled) return;
        setVoices(list);
        setVoice(list[0]?.id ?? "");
      })
      .catch(e => {
        console.error("Voices error:", e);
        if (!cancelled) setError(`Couldn't load the voices of ${ai.label}.`);
      });
    return () => { cancelled = true; };
  }, [ai.id]);

  const generateAudio = async () => {
    audioElement?.pause();
    setIsPlaying(false);
    setIsGenerating(true);
    setAudioUrl(null);
    setError(null);
    try {
      // TTS runs on the backend (core/services/audio.py), locally or in the cloud.
      const url = await generateSpeech({ text: script, voice, speed, pitch, provider: ai.id });
      setAudioUrl(url);
      setAudioElement(createAudio(url, () => setIsPlaying(false)));
    } catch (e) {
      console.error("Audio Gen Error:", e);
      setError(describeAIError(e, ai, "generate the narration"));
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
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-5xl mx-auto"
    >
      <StepHeader
        icon={<Volume2 />}
        eyebrow="Step 4 · Audio"
        title="Narration"
        description="Choose a voice and fine-tune it to match the tone of your video."
        tone="accent"
      />

      {error && (
        <Notice className="mb-6" onDismiss={() => setError(null)}>
          {error}{" "}
          <button onClick={onChangeAI} className="underline font-semibold">Choose another AI</button>
        </Notice>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Voice selection */}
        <div className="space-y-2">
          <label className="field-label mb-3">Voice · {ai.label}</label>
          <div className="grid grid-cols-1 gap-2">
            {voices.length === 0 && <Spinner className="w-5 h-5 text-zinc-400" />}
            {voices.map((v) => {
              const isSelected = voice === v.id;
              return (
                <button
                  key={v.id}
                  onClick={() => setVoice(v.id)}
                  className={cn(
                    "px-3 py-2.5 rounded-xl border text-left flex items-center gap-3 transition-colors",
                    isSelected
                      ? "bg-brand-primary/5 border-brand-primary"
                      : "bg-white border-zinc-200 hover:border-zinc-300"
                  )}
                >
                  <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center shrink-0", isSelected ? "bg-brand-primary text-white" : "bg-zinc-100 text-zinc-400")}>
                    <Mic className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-zinc-900">{v.name}</p>
                    <p className="text-xs text-zinc-500">{v.desc} · {v.type}</p>
                  </div>
                  {isSelected && <Check className="w-4 h-4 text-brand-primary" />}
                </button>
              );
            })}
          </div>
        </div>

        {/* Parameters */}
        <div className="glass-pane space-y-7 h-fit">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="field-label">Speed</label>
              <span className="text-xs font-semibold text-brand-primary">{speed.toFixed(1)}</span>
            </div>
            <input
              type="range"
              min="-1"
              max="1"
              step="0.1"
              value={speed}
              onChange={(e) => setSpeed(parseFloat(e.target.value))}
              className="w-full accent-[var(--color-brand-primary)]"
            />
            <div className="flex justify-between text-xs text-zinc-500">
              <span>Slow</span>
              <span>Normal</span>
              <span>Fast</span>
            </div>
          </div>

          {supportsPitch && <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="field-label">Pitch</label>
              <span className="text-xs font-semibold text-teal-700">{pitch.toFixed(1)}</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="1.5"
              step="0.1"
              value={pitch}
              onChange={(e) => setPitch(parseFloat(e.target.value))}
              className="w-full accent-[var(--color-brand-secondary)]"
            />
            <div className="flex justify-between text-xs text-zinc-500">
              <span>Deep</span>
              <span>Neutral</span>
              <span>High</span>
            </div>
          </div>}

          <button onClick={generateAudio} disabled={isGenerating || !voice} className="btn-primary w-full">
            {isGenerating ? <Spinner /> : <Wand2 className="w-4 h-4" />}
            <span>{isGenerating ? "Generating..." : audioUrl ? "Regenerate audio" : "Generate audio"}</span>
          </button>
        </div>

        {/* Preview */}
        <div className="rounded-3xl bg-zinc-900 flex flex-col items-center justify-center text-center p-8 min-h-80">
          {audioUrl ? (
            <div className="flex flex-col items-center gap-6 w-full">
              <div>
                <p className="text-white font-semibold text-lg">Voice ready</p>
                <p className="text-zinc-400 text-sm">
                  {voices.find(v => v.id === voice)?.name ?? voice} · speed {speed.toFixed(1)}{supportsPitch && ` · pitch ${pitch.toFixed(1)}`}
                </p>
              </div>

              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={togglePlayback}
                aria-label={isPlaying ? "Pause" : "Play"}
                className="w-16 h-16 bg-white text-zinc-900 rounded-full flex items-center justify-center shadow-lg"
              >
                {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6 ml-0.5" />}
              </motion.button>

              <button onClick={() => onNext(audioUrl)} className="btn-primary w-full">
                <span>Continue to images</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="text-zinc-500">
              {isGenerating ? <Spinner className="w-8 h-8 mx-auto mb-3 text-zinc-400" /> : <Volume2 className="w-10 h-10 mx-auto mb-3 opacity-40" />}
              <p className="text-sm">{isGenerating ? `Generating narration with ${ai.label}...` : "Your narration preview will appear here"}</p>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
