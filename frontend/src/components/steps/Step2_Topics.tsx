import React, { useState, useEffect } from "react";
import { motion } from "motion/react";
import { TrendingUp, Zap, ChevronRight, RefreshCw, Edit3 } from "lucide-react";
import LoadingDonut from "../ui/LoadingDonut";
import { cn } from "../../lib/utils";
import { ApiError, fetchBasicTopics, fetchTrendingTopics, fetchUniqueTopics, isRateLimitError } from "../../services/api";

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
  const [activeTab, setActiveTab] = useState<"basic" | "unique" | "trending">("basic");
  const [isLoading, setIsLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (discoveryMode === 'ai' && basicTopics.length === 0) {
      generateBasic();
    }
  }, [discoveryMode]);

  // All prompts, AI calls and trend research run on the backend (core/services/topics.py).
  const generateBasic = async () => {
    if (basicTopics.length > 0) return; // Prevent re-call
    setIsLoading(true);
    setError(null);
    try {
      setBasicTopics(await fetchBasicTopics(niche, duration));
    } catch (e) {
      console.error(e);
      if (isRateLimitError(e)) {
        setError("AI Quota limit reached. Please wait a moment before trying again.");
      } else if (e instanceof ApiError && e.code === "invalid_ai_response") {
        setError("AI returned invalid topic format. Try refreshing.");
      } else {
        setError("Failed to generate topics. Please check your connection.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const generateUnique = async () => {
    setActiveTab("unique");
    if (uniqueTopics.length > 0) return; // Prevent re-call

    setIsGenerating(true);
    setError(null);
    try {
      setUniqueTopics(await fetchUniqueTopics(niche));
    } catch (e) {
      console.error(e);
      if (isRateLimitError(e)) {
        setError("AI Quota limit reached. Please wait a moment.");
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const generateTrending = async () => {
    setActiveTab("trending");
    if (trendingTopics.length > 0) return; // Prevent re-call

    setIsGenerating(true);
    setError(null);
    try {
      // The backend scrapes news + Google Trends, then asks the AI for 10 topics.
      setTrendingTopics(await fetchTrendingTopics(niche));
    } catch (e) {
      console.error(e);
      if (isRateLimitError(e)) {
        setError("AI Quota limit reached. Please wait a moment.");
      }
    } finally {
      setIsGenerating(false);
    }
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

  if (!discoveryMode) {
    return (
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-4xl mx-auto space-y-12 pb-32 pt-20"
      >
        <div className="text-center">
           <h2 className="text-5xl font-salena text-zinc-900 mb-6 tracking-tighter uppercase font-medium">Topic Discovery</h2>
           <p className="text-zinc-400 font-medium text-lg leading-relaxed max-w-2xl mx-auto italic">How would you like to define your production narrative?</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
           <button 
             onClick={() => setDiscoveryMode("ai")}
             className="glass-pane !p-12 hover:border-brand-primary/40 transition-all group text-center flex flex-col items-center"
           >
              <div className="w-20 h-20 bg-brand-primary/10 rounded-3xl flex items-center justify-center mb-6 border border-brand-primary/20 group-hover:scale-110 transition-transform">
                <Zap className="w-10 h-10 text-brand-primary" />
              </div>
              <h3 className="text-2xl font-black text-zinc-900 mb-4 italic">AI Engine</h3>
              <p className="text-zinc-400 font-medium text-sm leading-relaxed">Let AI scan trends and niches to generate viral narrative anchors for you.</p>
           </button>

           <button 
             onClick={() => setDiscoveryMode("manual")}
             className="glass-pane !p-12 hover:border-brand-accent/40 transition-all group text-center flex flex-col items-center"
           >
              <div className="w-20 h-20 bg-brand-accent/10 rounded-3xl flex items-center justify-center mb-6 border border-brand-accent/20 group-hover:scale-110 transition-transform">
                <Edit3 className="w-10 h-10 text-brand-accent" />
              </div>
              <h3 className="text-2xl font-black text-zinc-900 mb-4 italic">Manual Entry</h3>
              <p className="text-zinc-400 font-medium text-sm leading-relaxed">Have a vision already? Type your own custom script or topic idea directly.</p>
           </button>
        </div>
      </motion.div>
    );
  }

  if (isLoading && basicTopics.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-20 py-32">
        <LoadingDonut />
        <p className="mt-10 text-zinc-400 animate-pulse font-black uppercase tracking-[0.3em] text-xs">Architecting Strategies...</p>
      </div>
    );
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-16 pb-32"
    >
      <div className="text-center">
        <div className="inline-flex items-center space-x-2 px-4 py-2 bg-brand-primary/10 text-brand-primary rounded-full mb-6">
          <TrendingUp className="w-4 h-4" />
          <span className="text-[10px] font-black uppercase tracking-[0.2em]">Phase Two / Discovery</span>
        </div>
        <h2 className="text-5xl font-salena text-zinc-900 mb-6 tracking-tighter uppercase font-medium">Discovery Engine</h2>
        <p className="text-zinc-400 font-medium text-lg max-w-2xl mx-auto italic">Select your path. Basic for staples, Unique for creativity, or Trending for market pulse.</p>
        
        {error && (
          <motion.div 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 p-4 bg-red-50 border border-red-200 text-red-600 rounded-2xl text-xs font-bold uppercase tracking-wider max-w-md mx-auto"
          >
            {error}
          </motion.div>
        )}
      </div>

      {/* Custom Input Section */}
      <div className="max-w-4xl mx-auto px-4">
        <form onSubmit={handleCustomTopicSubmit} className="relative group">
          <input 
             type="text"
             value={customTopic}
             onChange={(e) => {
               setCustomTopic(e.target.value);
               if (e.target.value.trim()) setSelectedTopic(e.target.value.trim());
             }}
             placeholder="Or enter your own narrative here..."
             className="w-full p-8 pr-40 bg-white rounded-[40px] border-4 border-[#8bb7df]/20 text-xl font-medium focus:border-brand-primary/40 focus:outline-none transition-all shadow-xl selection:bg-brand-primary/20 placeholder:text-zinc-300 italic"
          />
          <button 
            type="submit"
            className="absolute right-4 top-4 bottom-4 px-10 bg-zinc-900 text-white rounded-[32px] font-black text-xs uppercase tracking-widest hover:bg-brand-primary transition-all disabled:opacity-50"
            disabled={!customTopic.trim()}
          >
            USE CUSTOM
          </button>
        </form>
      </div>

      {/* AI Discovery Section */}
      {discoveryMode === "ai" && (
        <>
          {/* Tabs / Switches */}
          <div className="flex flex-wrap justify-center gap-4">
            <button 
              onClick={() => setActiveTab("basic")}
              className={cn(
                "px-10 py-4 rounded-2xl font-black text-xs uppercase tracking-widest transition-all border-2",
                activeTab === "basic" ? "bg-brand-primary text-white border-brand-primary" : "bg-white text-zinc-400 border-[#8bb7df] hover:border-brand-primary shadow-sm"
              )}
            >
              Basic Topics (10)
            </button>
            <button 
              onClick={generateUnique}
              disabled={isGenerating}
              className={cn(
                "px-10 py-4 rounded-2xl font-black text-xs uppercase tracking-widest transition-all border-2",
                activeTab === "unique" ? "bg-brand-berry text-white border-brand-berry" : "bg-white text-zinc-400 border-[#8bb7df] hover:border-brand-berry shadow-sm"
              )}
            >
              {isGenerating && activeTab === "unique" ? <RefreshCw className="w-4 h-4 animate-spin" /> : "Get Unique Ideas"}
            </button>
            <button 
              onClick={generateTrending}
              disabled={isGenerating}
              className={cn(
                "px-10 py-4 rounded-2xl font-black text-xs uppercase tracking-widest transition-all border-2",
                activeTab === "trending" ? "bg-brand-secondary text-white border-brand-secondary" : "bg-white text-zinc-400 border-[#8bb7df] hover:border-brand-secondary shadow-sm"
              )}
            >
              {isGenerating && activeTab === "trending" ? <RefreshCw className="w-4 h-4 animate-spin" /> : <div className="flex items-center space-x-2"><Zap className="w-4 h-4" /><span>Live Trends Scraping</span></div>}
            </button>
          </div>

          <div className="max-w-4xl mx-auto px-4">
            <div className="glass-pane-pink !p-12 min-h-[400px] flex flex-col">
              <div className="flex items-center space-x-3 mb-12">
                <div className={cn("w-3 h-3 rounded-full animate-pulse", activeTab === 'basic' ? 'bg-brand-primary' : activeTab === 'unique' ? 'bg-brand-berry' : 'bg-brand-secondary')} />
                <h3 className="text-xl font-black text-zinc-900 uppercase tracking-widest italic">
                  {activeTab === 'basic' ? 'Baseline Concepts' : activeTab === 'unique' ? 'Avant-Garde Ideas' : 'Market Evolution'}
                </h3>
              </div>

              {isGenerating ? (
                <div className="flex-grow flex items-center justify-center">
                  <LoadingDonut />
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Array.isArray(activeTab === 'basic' ? basicTopics : activeTab === 'unique' ? uniqueTopics : trendingTopics) && 
                   (activeTab === 'basic' ? basicTopics : activeTab === 'unique' ? uniqueTopics : trendingTopics).map((t, i) => (
                    <motion.button
                      key={i}
                      whileHover={{ scale: 1.02, x: 5 }}
                      onClick={() => handleTopicSelect(t)}
                      className={cn(
                        "w-full text-left p-6 rounded-[32px] font-bold text-base transition-all border-2",
                        selectedTopic === t 
                          ? "bg-zinc-900 text-white border-zinc-900 shadow-xl" 
                          : "bg-zinc-50/50 text-zinc-500 border-transparent hover:border-[#8bb7df] hover:bg-white"
                      )}
                    >
                      <div className="flex items-start">
                        <span className="opacity-20 font-black mr-4 mt-1 text-xs">{String(i+1).padStart(2, '0')}</span>
                        <span>{t}</span>
                      </div>
                    </motion.button>
                  ))}
                </div>
              )}
              
              {(activeTab === 'unique' && uniqueTopics.length === 0 && !isGenerating) && (
                <div className="flex-grow flex items-center justify-center text-zinc-300 italic font-medium">Click "Get Unique Ideas" to initiate catalyst</div>
              )}
              {(activeTab === 'trending' && trendingTopics.length === 0 && !isGenerating) && (
                <div className="flex-grow flex items-center justify-center text-zinc-300 italic font-medium">Click "Live Trends Scraping" to sync with live data</div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Manual Selection / Custom */}
      {selectedTopic && (
        <motion.div 
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          className="fixed bottom-12 left-1/2 -translate-x-1/2 z-50 glass-pane !bg-white/90 !p-8 flex flex-col md:flex-row items-center gap-10 shadow-2xl ring-2 ring-[#8bb7df]"
        >
          <div className="px-4">
            <span className="text-[10px] font-black text-brand-primary tracking-[0.2em] block uppercase mb-2">Selected Narrative</span>
            <span className="text-zinc-900 font-bold text-xl truncate max-w-[500px] block italic leading-tight">"{selectedTopic}"</span>
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => onNext(selectedTopic, { basic: basicTopics, unique: uniqueTopics, trending: trendingTopics })}
            className="btn-primary group flex items-center gap-4 px-14 py-6"
          >
            <span className="text-lg">PROCEED TO PRODUCTION</span>
            <ChevronRight className="w-6 h-6 group-hover:translate-x-2 transition-transform" />
          </motion.button>
        </motion.div>
      )}
    </motion.div>
  );
}
