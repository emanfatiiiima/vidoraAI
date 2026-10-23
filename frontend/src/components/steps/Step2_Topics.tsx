import React, { useEffect, useState } from "react";
import { motion } from "motion/react";
import { TrendingUp, Zap, ChevronRight, Edit3, Check, RotateCcw } from "lucide-react";
import LoadingDonut, { Spinner } from "../ui/LoadingDonut";
import StepHeader from "../ui/StepHeader";
import StepFooter from "../ui/StepFooter";
import Notice from "../ui/Notice";
import { cn } from "../../lib/utils";
import { describeAIError, isProviderError, type AIChoice } from "../../lib/aiSelection";
import { fetchBasicTopics, fetchTrendingTopics, fetchUniqueTopics, type AIProvider } from "../../services/api";

type TopicTab = "basic" | "unique" | "trending";

interface Step2Props {
  niche: string;
  duration: string;
  /** Topic AI picked in the popup before Step 1. */
  ai: AIChoice<AIProvider>;
  /** Reopens the AI popup (offered when the AI fails). */
  onChangeAI: () => void;
  onNext: (topic: string, cachedTopics: { basic: string[], unique: string[], trending: string[] }) => void;
  initialTopics?: { basic: string[], unique: string[], trending: string[] } | null;
  initialSelection?: string;
  key?: string;
}

export default function Step2_Topics({ niche, duration, ai, onChangeAI, onNext, initialTopics, initialSelection }: Step2Props) {
  const [basicTopics, setBasicTopics] = useState<string[]>(initialTopics?.basic || []);
  const [uniqueTopics, setUniqueTopics] = useState<string[]>(initialTopics?.unique || []);
  const [trendingTopics, setTrendingTopics] = useState<string[]>(initialTopics?.trending || []);
  const [selectedTopic, setSelectedTopic] = useState(initialSelection || "");
  const [discoveryMode, setDiscoveryMode] = useState<"ai" | "manual" | null>(initialTopics ? "ai" : null);
  const [activeTab, setActiveTab] = useState<TopicTab>("basic");
  const [isLoading, setIsLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // True when the error came from the AI, so offering "Change AI" makes sense.
  const [aiFailed, setAiFailed] = useState(false);

  const topicsByTab: Record<TopicTab, string[]> = { basic: basicTopics, unique: uniqueTopics, trending: trendingTopics };

  // All prompts, AI calls and trend research run on the backend (core/services/topics.py),
  // using only the topic AI the user picked.
  const loadTopics = async (tab: TopicTab) => {
    const fetchers: Record<TopicTab, () => Promise<string[]>> = {
      basic: () => fetchBasicTopics(niche, duration, ai.id),
      unique: () => fetchUniqueTopics(niche, ai.id),
      // The backend scrapes news + Google Trends, then asks the AI for 10 topics.
      trending: () => fetchTrendingTopics(niche, ai.id),
    };
    const setters: Record<TopicTab, (topics: string[]) => void> = {
      basic: setBasicTopics,
      unique: setUniqueTopics,
      trending: setTrendingTopics,
    };
    const setBusy = tab === "basic" ? setIsLoading : setIsGenerating;

    setBusy(true);
    setError(null);
    setAiFailed(false);
    try {
      setters[tab](await fetchers[tab]());
    } catch (e) {
      console.error(e);
      setError(describeAIError(e, ai, "generate topics"));
      setAiFailed(isProviderError(e));
    } finally {
      setBusy(false);
    }
  };

  // Load the open tab as soon as AI mode is on - and again if the user switched
  // to another AI after a failure (the tab is still empty then).
  useEffect(() => {
    if (discoveryMode === "ai" && topicsByTab[activeTab].length === 0) loadTopics(activeTab);
  }, [discoveryMode, ai.id]);

  const openTab = (tab: TopicTab) => {
    setActiveTab(tab);
    if (topicsByTab[tab].length === 0) loadTopics(tab);
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

      {error && (
        <Notice className="mb-6" onDismiss={() => setError(null)}>
          {error}{" "}
          {aiFailed && (
            <button onClick={onChangeAI} className="font-semibold underline underline-offset-2">Choose another AI</button>
          )}
        </Notice>
      )}

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
            <span className="chip" title="Change it from the AI button in the header">Using {ai.label}</span>
          </div>

          {isGenerating ? (
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
            <div className="py-12 text-center">
              <p className="text-sm text-zinc-500 mb-4">No ideas yet.</p>
              <button onClick={() => loadTopics(activeTab)} disabled={isBusy} className="btn-dark inline-flex items-center gap-2">
                <RotateCcw className="w-4 h-4" />
                <span>Try again</span>
              </button>
            </div>
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
