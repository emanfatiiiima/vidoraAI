import React, { useState } from "react";
import { motion } from "motion/react";
import { TrendingUp, Zap, ChevronRight, Edit3, Check, Sparkles, RotateCcw } from "lucide-react";
import LoadingDonut, { Spinner } from "../ui/LoadingDonut";
import StepHeader from "../ui/StepHeader";
import StepFooter from "../ui/StepFooter";
import Notice from "../ui/Notice";
import { cn } from "../../lib/utils";
import { ApiError, fetchBasicTopics, fetchTrendingTopics, fetchUniqueTopics, isRateLimitError, type AIProvider } from "../../services/api";

type TopicTab = "basic" | "unique" | "trending";

const AI_OPTIONS: { id: AIProvider; label: string }[] = [
  { id: "gemini", label: "Gemini" },
  { id: "openai", label: "ChatGPT" },
  { id: "groq", label: "Groq" },
];

interface Step2Props {
  niche: string;
  duration: string;
  onNext: (topic: string, cachedTopics: { basic: string[], unique: string[], trending: string[] }) => void;
  initialTopics?: { basic: string[], unique: string[], trending: string[] } | null;
  initialSelection?: string;
  key?: string;
}

export default function Step2_Topics({ niche, duration, onNext, initialTopics, initialSelection }: Step2Props) {
  const [basicTopics, setBasicTopics] = useState<string[]>(initialTopics?.basic || []);
  const [uniqueTopics, setUniqueTopics] = useState<string[]>(initialTopics?.unique || []);
  const [trendingTopics, setTrendingTopics] = useState<string[]>(initialTopics?.trending || []);
  const [selectedTopic, setSelectedTopic] = useState(initialSelection || "");
  const [discoveryMode, setDiscoveryMode] = useState<"ai" | "manual" | null>(initialTopics ? "ai" : null);
  const [activeTab, setActiveTab] = useState<TopicTab>("basic");
  const [isLoading, setIsLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // The AI the user picked. Calls go to that AI only; if it fails it is disabled and the user picks again.
  const [provider, setProvider] = useState<AIProvider | null>(null);
  const [failedProviders, setFailedProviders] = useState<AIProvider[]>([]);

  const topicsByTab: Record<TopicTab, string[]> = { basic: basicTopics, unique: uniqueTopics, trending: trendingTopics };
  const allProvidersFailed = AI_OPTIONS.every(o => failedProviders.includes(o.id));

  // All prompts, AI calls and trend research run on the backend (core/services/topics.py).
  const loadTopics = async (tab: TopicTab, ai: AIProvider) => {
    const fetchers: Record<TopicTab, () => Promise<string[]>> = {
      basic: () => fetchBasicTopics(niche, duration, ai),
      unique: () => fetchUniqueTopics(niche, ai),
      // The backend scrapes news + Google Trends, then asks the AI for 10 topics.
      trending: () => fetchTrendingTopics(niche, ai),
    };
    const setters: Record<TopicTab, (topics: string[]) => void> = {
      basic: setBasicTopics,
      unique: setUniqueTopics,
      trending: setTrendingTopics,
    };
    const setBusy = tab === "basic" ? setIsLoading : setIsGenerating;

    setBusy(true);
    setError(null);
    try {
      setters[tab](await fetchers[tab]());
    } catch (e) {
      console.error(e);
      if (e instanceof ApiError && e.code === "network_error") {
        setError("Failed to reach the server. Please check your connection.");
      } else {
        const name = AI_OPTIONS.find(o => o.id === ai)!.label;
        const reason = e instanceof ApiError && e.code === "invalid_ai_response"
          ? "returned an invalid response"
          : e instanceof ApiError && e.code === "provider_not_configured"
            ? "is not configured on the server"
            : isRateLimitError(e) ? "hit its quota limit" : "couldn't generate topics";
        setFailedProviders(prev => (prev.includes(ai) ? prev : [...prev, ai]));
        setProvider(null);
        setError(`${name} ${reason}. Please choose another AI.`);
      }
    } finally {
      setBusy(false);
    }
  };

  const selectProvider = (ai: AIProvider) => {
    setProvider(ai);
    if (topicsByTab[activeTab].length === 0) loadTopics(activeTab, ai);
  };

  const openTab = (tab: TopicTab) => {
    setActiveTab(tab);
    if (topicsByTab[tab].length === 0 && provider) loadTopics(tab, provider);
  };

  const resetProviders = () => {
    setFailedProviders([]);
    setError(null);
  };

  const [customTopic, setCustomTopic] = useState("");

  const handleTopicSelect = (topic: string) => {
    setSelectedTopic(topic);
    setCustomTopic("");
  };

  const handleCustomTopicSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (customTopic.trim()) {
      setSelectedTopic(customTopic.trim());
    }
  };

  const tabs = [
    { id: "basic" as const, label: "Basic", active: "bg-brand-primary text-white" },
    { id: "unique" as const, label: "Unique ideas", active: "bg-brand-berry text-white" },
    { id: "trending" as const, label: "Live trends", active: "bg-brand-secondary text-white" },
  ];
  const activeTopics = topicsByTab[activeTab];
  const isBusy = isLoading || isGenerating;

  if (!discoveryMode) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-3xl mx-auto"
      >
        <StepHeader
          icon={<TrendingUp />}
          eyebrow="Step 2 · Topic"
          title="Topic discovery"
          description="How would you like to choose your video topic?"
        />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <button
            onClick={() => setDiscoveryMode("ai")}
            className="glass-pane text-left group hover:shadow-lg hover:-translate-y-0.5 transition-all"
          >
            <div className="w-11 h-11 bg-white/70 rounded-xl flex items-center justify-center mb-4 text-brand-primary">
              <Zap className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-salena font-bold text-zinc-900 mb-1">AI suggestions</h3>
            <p className="text-zinc-600 text-sm leading-relaxed">Let AI scan your niche and live trends to suggest viral topics.</p>
          </button>

          <button
            onClick={() => setDiscoveryMode("manual")}
            className="glass-pane-pink text-left group hover:shadow-lg hover:-translate-y-0.5 transition-all"
          >
            <div className="w-11 h-11 bg-white/70 rounded-xl flex items-center justify-center mb-4 text-amber-700">
              <Edit3 className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-salena font-bold text-zinc-900 mb-1">Write my own</h3>
            <p className="text-zinc-600 text-sm leading-relaxed">Already have an idea? Type your own topic directly.</p>
          </button>
        </div>
      </motion.div>
    );
  }

  if (isLoading && basicTopics.length === 0) {
    return (
      <div className="flex items-center justify-center py-24">
        <LoadingDonut label="Finding topic ideas..." />
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-3xl mx-auto"
    >
      <StepHeader
        icon={<TrendingUp />}
        eyebrow="Step 2 · Topic"
        title={discoveryMode === "ai" ? "Pick a topic" : "Your topic"}
        description={discoveryMode === "ai"
          ? "Choose one of the suggestions below or write your own."
          : "Type the topic you want your video to be about."}
      />

      {error && <Notice className="mb-6" onDismiss={() => setError(null)}>{error}</Notice>}

      {/* Custom topic */}
      <form onSubmit={handleCustomTopicSubmit} className="flex gap-2 mb-8">
        <input
          type="text"
          value={customTopic}
          onChange={(e) => {
            setCustomTopic(e.target.value);
            if (e.target.value.trim()) setSelectedTopic(e.target.value.trim());
          }}
          placeholder="Write your own topic..."
          className="input-field !py-3"
        />
        <button type="submit" className="btn-dark shrink-0" disabled={!customTopic.trim()}>
          Use this
        </button>
      </form>

      {/* AI suggestions */}
      {discoveryMode === "ai" && (
        <div className="glass-pane-pink !p-4 md:!p-5">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            <div className="inline-flex p-1 bg-white/70 rounded-xl border border-black/5">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => openTab(tab.id)}
                  disabled={isBusy}
                  className={cn(
                    "px-3.5 py-1.5 rounded-lg text-sm font-semibold transition-colors inline-flex items-center gap-1.5",
                    activeTab === tab.id ? tab.active : "text-zinc-600 hover:text-zinc-900"
                  )}
                >
                  {tab.id === "trending" && <Zap className="w-3.5 h-3.5" />}
                  {tab.label}
                  {isGenerating && activeTab === tab.id && <Spinner className="w-3.5 h-3.5" />}
                </button>
              ))}
            </div>
            {(provider || activeTopics.length > 0) && (
              <div className="inline-flex items-center gap-1 p-1 bg-white/70 rounded-xl border border-black/5" role="group" aria-label="AI model">
                {AI_OPTIONS.map(option => {
                  const failed = failedProviders.includes(option.id);
                  // Once an AI is chosen the choice is locked; it only reopens if that AI fails.
                  const locked = provider !== null && provider !== option.id;
                  return (
                    <button
                      key={option.id}
                      onClick={() => selectProvider(option.id)}
                      disabled={failed || locked || isBusy}
                      aria-pressed={provider === option.id}
                      title={failed
                        ? `${option.label} failed - choose another AI`
                        : locked ? "Topics are being generated with another AI" : `Generate with ${option.label}`}
                      className={cn(
                        "px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors disabled:cursor-not-allowed",
                        provider === option.id ? "bg-zinc-900 text-white" : "text-zinc-600 hover:text-zinc-900",
                        locked && "opacity-40 hover:text-zinc-600",
                        failed && "line-through opacity-40 hover:text-zinc-600"
                      )}
                    >
                      {option.label}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {!provider && activeTopics.length === 0 && !isBusy ? (
            <div className="py-8 text-center">
              {allProvidersFailed ? (
                <>
                  <p className="text-sm text-zinc-600 mb-4">All AI options failed. Write your own topic above, or try the AIs again.</p>
                  <button onClick={resetProviders} className="btn-dark inline-flex items-center gap-2">
                    <RotateCcw className="w-4 h-4" />
                    <span>Try again</span>
                  </button>
                </>
              ) : (
                <>
                  <p className="text-sm font-semibold text-zinc-900 mb-1">Choose an AI to generate ideas</p>
                  <p className="text-xs text-zinc-600 mb-5">Topics are generated only by the AI you pick.</p>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 max-w-xl mx-auto">
                    {AI_OPTIONS.map(option => {
                      const failed = failedProviders.includes(option.id);
                      return (
                        <button
                          key={option.id}
                          onClick={() => selectProvider(option.id)}
                          disabled={failed}
                          className={cn(
                            "px-4 py-3 rounded-xl text-sm font-semibold border transition-all inline-flex items-center justify-center gap-2",
                            failed
                              ? "bg-white/40 text-zinc-400 border-transparent cursor-not-allowed"
                              : "bg-white/80 text-zinc-800 border-transparent hover:border-[var(--color-box-border)] hover:bg-white hover:shadow-sm"
                          )}
                        >
                          <Sparkles className="w-4 h-4" />
                          <span>{option.label}</span>
                          {failed && <span className="text-[10px] font-medium uppercase tracking-wide">Unavailable</span>}
                        </button>
                      );
                    })}
                  </div>
                </>
              )}
            </div>
          ) : isGenerating ? (
            <div className="py-16 flex justify-center">
              <LoadingDonut label={activeTab === "trending" ? "Reading live trends..." : "Generating ideas..."} />
            </div>
          ) : activeTopics.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {activeTopics.map((t, i) => {
                const isSelected = selectedTopic === t;
                return (
                  <button
                    key={i}
                    onClick={() => handleTopicSelect(t)}
                    className={cn(
                      "w-full text-left px-4 py-3 rounded-xl text-sm font-medium transition-all border flex items-start gap-3",
                      isSelected
                        ? "bg-zinc-900 text-white border-zinc-900 shadow-md"
                        : "bg-white/80 text-zinc-700 border-transparent hover:border-[var(--color-box-border)] hover:bg-white"
                    )}
                  >
                    <span className={cn("text-xs font-semibold mt-0.5 tabular-nums", isSelected ? "text-white/50" : "text-zinc-400")}>
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <span className="flex-1">{t}</span>
                    {isSelected && <Check className="w-4 h-4 mt-0.5 shrink-0" />}
                  </button>
                );
              })}
            </div>
          ) : (
            <p className="py-12 text-center text-sm text-zinc-500">
              No ideas yet. Click an AI above to generate them.
            </p>
          )}
        </div>
      )}

      {/* Continue */}
      {selectedTopic && (
        <StepFooter
          icon={<Check />}
          title={selectedTopic}
          description="Selected topic"
          action={
            <button
              onClick={() => onNext(selectedTopic, { basic: basicTopics, unique: uniqueTopics, trending: trendingTopics })}
              className="btn-primary"
            >
              <span>Continue to script</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          }
        />
      )}
    </motion.div>
  );
}
