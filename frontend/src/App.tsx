import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import Login from "./components/auth/Login";
import Signup from "./components/auth/Signup";
import ForgotPassword from "./components/auth/ForgotPassword";
import Timeline, { Step } from "./components/Timeline";
import BearCharacter from "./components/auth/BearCharacter";
import Step1_Inputs, { VideoInputs } from "./components/steps/Step1_Inputs";
import Step2_Topics from "./components/steps/Step2_Topics";
import Step3_Script from "./components/steps/Step3_Script";
import Step4_Audio from "./components/steps/Step4_Audio";
import Step5_Visuals from "./components/steps/Step5_Visuals";
import Step7_Videos from "./components/steps/Step7_Videos";
import Step8_Compile from "./components/steps/Step8_Compile";
import Step9_Download from "./components/steps/Step9_Download";
import { Sun, Moon, LogOut, Sparkles } from "lucide-react";

// Placeholder components for new steps
function StepPlaceholder({ title, onNext }: { title: string, onNext: () => void }) {
  return (
    <div className="glass-pane flex flex-col items-center justify-center p-20 py-32 text-center">
      <div className="w-24 h-24 bg-brand-primary/10 rounded-3xl flex items-center justify-center text-brand-primary mb-8 animate-pulse">
        <Sparkles className="w-12 h-12" />
      </div>
      <h2 className="text-4xl font-black mb-4 uppercase tracking-tighter text-zinc-900">{title} Pipeline</h2>
      <p className="text-zinc-500 mb-12 max-w-sm font-medium">This architectural module is currently under construction for the next production cycle.</p>
      <button 
        onClick={onNext} 
        className="btn-primary px-12 py-4 text-lg"
      >
        BYPASS TO NEXT PHASE
      </button>
    </div>
  );
}

export default function App() {
  const [currentPage, setCurrentPage] = useState<'login' | 'signup' | 'forgot' | 'home' | 'videogen'>('login');
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [user, setUser] = useState<{ email: string } | null>(null);
  
  // App State
  const [currentStep, setCurrentStep] = useState(1);
  const [maxStep, setMaxStep] = useState(1);
  const [inputs, setInputs] = useState<VideoInputs | null>(null);
  const [topics, setTopics] = useState<{ basic: string[], unique: string[], trending: string[] } | null>(null);
  const [selectedTopic, setSelectedTopic] = useState("");
  const [script, setScript] = useState("");
  const [summary, setSummary] = useState("");
  const [audioUrl, setAudioUrl] = useState("");
  const [scenes, setScenes] = useState<any[] | null>(null);
  const [finalVideoUrl, setFinalVideoUrl] = useState("");

  useEffect(() => {
    if (currentStep > maxStep) {
      setMaxStep(currentStep);
    }
  }, [currentStep]);

  const resetApp = () => {
    setCurrentStep(1);
    setMaxStep(1);
    setInputs(null);
    setTopics(null);
    setSelectedTopic("");
    setScript("");
    setSummary("");
    setAudioUrl("");
    setScenes(null);
    setFinalVideoUrl("");
    setCurrentPage('home');
  };

  const steps: Step[] = [
    { id: 1, label: 'Start', status: currentStep === 1 ? 'in-progress' : maxStep >= 1 ? 'completed' : 'pending' },
    { id: 2, label: 'Topic', status: currentStep === 2 ? 'in-progress' : maxStep >= 2 ? 'completed' : 'pending' },
    { id: 3, label: 'Script', status: currentStep === 3 ? 'in-progress' : maxStep >= 3 ? 'completed' : 'pending' },
    { id: 4, label: 'Audio', status: currentStep === 4 ? 'in-progress' : maxStep >= 4 ? 'completed' : 'pending' },
    { id: 5, label: 'Images', status: currentStep === 5 ? 'in-progress' : maxStep >= 5 ? 'completed' : 'pending' },
    { id: 6, label: 'Videos', status: currentStep === 6 ? 'in-progress' : maxStep >= 6 ? 'completed' : 'pending' },
    { id: 7, label: 'Render', status: currentStep === 7 ? 'in-progress' : maxStep >= 7 ? 'completed' : 'pending' },
    { id: 8, label: 'Download', status: currentStep === 8 ? 'in-progress' : maxStep >= 8 ? 'completed' : 'pending' },
  ];

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  const handleLogin = (email: string) => {
    setUser({ email });
    setCurrentPage('home');
  };

  const logout = () => {
    setUser(null);
    setCurrentPage('login');
  };

  if (currentPage === 'login') return <Login onLogin={handleLogin} onNavigate={setCurrentPage} />;
  if (currentPage === 'signup') return <Signup onNavigate={() => setCurrentPage('login')} />;
  if (currentPage === 'forgot') return <ForgotPassword onNavigate={() => setCurrentPage('login')} />;

  const BrandLogo = () => (
    <button onClick={resetApp} className="group flex items-center space-x-3 bg-white/50 backdrop-blur-md px-4 py-2 rounded-2xl hover:bg-white transition-all border border-zinc-200/50">
      <div className="w-8 h-8 bg-brand-primary rounded-xl flex items-center justify-center overflow-hidden shadow-lg shadow-brand-primary/20 transition-transform group-hover:rotate-12">
         <div className="scale-60 relative top-1">
            <BearCharacter isCoveringEyes={false} />
         </div>
      </div>
      <span className="font-black text-xl tracking-tighter text-zinc-900 uppercase">Vidora<span className="text-brand-primary">AI</span></span>
    </button>
  );

  return (
    <div className="min-h-screen bg-[#f8f9ff] text-zinc-900 font-plus">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 h-20 bg-white/70 backdrop-blur-xl border-b border-zinc-200/50 z-40 flex items-center justify-between px-8">
        <BrandLogo />

        <div className="flex items-center space-x-6">
          <button 
            onClick={toggleTheme}
            className="w-12 h-12 rounded-2xl bg-white shadow-sm border border-zinc-200 flex items-center justify-center text-zinc-600 hover:text-brand-primary hover:border-brand-primary/30 transition-all"
          >
            {theme === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
          </button>
          
          <div className="h-8 w-[1px] bg-zinc-200" />
          
          <div className="flex items-center space-x-4">
            <div className="text-right hidden sm:block">
              <p className="text-xs font-black text-zinc-900 uppercase tracking-widest">{user?.email.split('@')[0]}</p>
              <p className="text-[10px] text-zinc-400 font-bold uppercase tracking-wider">{user?.email}</p>
            </div>
            <button 
              onClick={logout}
              className="w-12 h-12 rounded-2xl bg-zinc-100 text-zinc-400 hover:bg-red-500 hover:text-white transition-all flex items-center justify-center"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="pt-32 px-4 pb-20 relative">
        <div className="max-w-7xl mx-auto">
          {currentPage === 'home' && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-10 pt-12">
              <motion.button
                whileHover={{ scale: 1.02, y: -5 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setCurrentPage('videogen')}
                className="group glass-pane text-left flex flex-col justify-between h-96 relative overflow-hidden"
              >
                <div className="absolute -right-10 -top-10 w-40 h-40 bg-black/5 rounded-full blur-3xl transition-all" />
                
                <div className="w-20 h-20 bg-black rounded-[28px] flex items-center justify-center text-white mb-8 shadow-2xl font-black text-3xl">
                  <Sparkles className="w-10 h-10" />
                </div>
                <div>
                  <div className="flex items-center space-x-2 mb-3">
                    <span className="px-3 py-1 bg-black/10 text-black text-[10px] font-black uppercase tracking-widest rounded-lg">Production Ready</span>
                  </div>
                  <h3 className="text-4xl font-black text-black mb-3 tracking-tighter uppercase italic">VideoGen</h3>
                  <p className="text-black/60 font-medium leading-relaxed">Create viral videos with a guided AI workflow. We handle the trends, the script, and the scenes.</p>
                </div>
              </motion.button>
              
              <div className="glass-pane-pink border-dashed border-[#8bb7df] flex flex-col justify-center items-center text-center">
                <div className="w-16 h-16 bg-[#c6e9c8] rounded-2xl flex items-center justify-center text-[#718804] mb-6">
                  <Sparkles className="w-8 h-8" />
                </div>
                <p className="font-black text-black uppercase tracking-[0.2em] text-xs">Audio Studio</p>
                <p className="text-black/40 text-sm font-bold mt-2 italic">Coming Phase 2</p>
              </div>

              <div className="glass-pane border-dashed border-[#8bb7df] flex flex-col justify-center items-center text-center opacity-70">
                <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center text-black mb-6">
                  <Sparkles className="w-8 h-8" />
                </div>
                <p className="font-black text-black uppercase tracking-[0.2em] text-xs">Analytics Engine</p>
                <p className="text-black/40 text-sm font-bold mt-2 italic">Coming Phase 3</p>
              </div>
            </div>
          )}

          {currentPage === 'videogen' && (
            <div className="space-y-16">
              {/* Timeline */}
              <section className="mb-8">
                <Timeline 
                  steps={steps} 
                  currentStep={currentStep} 
                  onStepClick={(id) => {
                    if (id <= currentStep || steps[id-1].status !== 'pending') {
                      setCurrentStep(id);
                    }
                  }} 
                />
              </section>

              {/* Current Step Content */}
              <div className="relative">
                <AnimatePresence mode="wait">
                  {currentStep === 1 && (
                    <Step1_Inputs 
                      key="step1"
                      initialData={inputs || undefined}
                      onNext={(data) => {
                        setInputs(data);
                        setCurrentStep(2);
                      }}
                    />
                  )}
                  {currentStep === 2 && inputs && (
                    <Step2_Topics 
                      key="step2"
                      niche={inputs.niche}
                      duration={`${inputs.duration} ${inputs.durationUnit}`}
                      initialTopics={topics}
                      initialSelection={selectedTopic}
                      onNext={(topic, cachedTopics) => {
                        setSelectedTopic(topic);
                        setTopics(cachedTopics);
                        setCurrentStep(3);
                      }}
                    />
                  )}
                  {currentStep === 3 && inputs && (
                    <Step3_Script 
                      key="step3"
                      topic={selectedTopic}
                      niche={inputs.niche}
                      style={inputs.style}
                      duration={`${inputs.duration} ${inputs.durationUnit}`}
                      initialScript={script}
                      onNext={(s, sum) => {
                        setScript(s);
                        setSummary(sum);
                        setCurrentStep(4);
                      }}
                    />
                  )}
                  {currentStep === 4 && (
                    <Step4_Audio 
                      key="step4"
                      script={script}
                      initialAudio={audioUrl}
                      onNext={(url) => {
                        setAudioUrl(url);
                        setCurrentStep(5);
                      }}
                    />
                  )}
                  {currentStep === 5 && inputs && (
                    <Step5_Visuals 
                      key="step5"
                      script={script}
                      sceneCount={inputs.sceneCount}
                      style={inputs.style}
                      onNext={(updated) => {
                        setScenes(updated);
                        setCurrentStep(6);
                      }}
                    />
                  )}
                  {currentStep === 6 && scenes && (
                    <Step7_Videos
                      scenes={scenes}
                      onNext={(updated) => {
                        setScenes(updated);
                        setCurrentStep(7);
                      }}
                    />
                  )}
                  {currentStep === 7 && scenes && (
                    <Step8_Compile 
                      scenes={scenes}
                      audioUrl={audioUrl}
                      onNext={(url) => {
                        setFinalVideoUrl(url);
                        setCurrentStep(8);
                      }}
                    />
                  )}
                  {currentStep === 8 && (
                    <Step9_Download 
                      videoUrl={finalVideoUrl}
                      onReset={resetApp}
                      project={inputs ? {
                        niche: inputs.niche,
                        style: inputs.style,
                        duration: `${inputs.duration} ${inputs.durationUnit}`,
                        aspectRatio: inputs.aspectRatio,
                        sceneCount: inputs.sceneCount,
                        topic: selectedTopic,
                        script,
                        summary,
                        audioUrl,
                        finalVideoUrl,
                        scenes: scenes || [],
                      } : null}
                    />
                  )}
                </AnimatePresence>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Background Decor */}
      <div className="fixed -z-10 top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        {/* Animated Blobs */}
        <motion.div 
          animate={{ 
            scale: [1, 1.2, 1],
            rotate: [0, 90, 0],
            x: [0, 50, 0],
            y: [0, -30, 0]
          }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
          className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-brand-primary/5 blur-[120px] rounded-full" 
        />
        <motion.div 
          animate={{ 
            scale: [1.2, 1, 1.2],
            rotate: [0, -90, 0],
            x: [0, -50, 0],
            y: [0, 30, 0]
          }}
          transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
          className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-brand-secondary/5 blur-[120px] rounded-full" 
        />
        <motion.div 
          animate={{ 
            scale: [1, 1.3, 1],
            x: [0, 30, 0],
            y: [0, 50, 0]
          }}
          transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
          className="absolute top-[20%] right-[-5%] w-[30%] h-[30%] bg-brand-berry/5 blur-[100px] rounded-full" 
        />

        {/* Cute Floating Icons */}
        <div className="absolute inset-0">
          <FloatingIcon icon={<Sparkles className="w-12 h-12" />} top="15%" left="10%" delay={0} />
          <FloatingIcon icon={<div className="w-16 h-16 bg-brand-primary/5 rounded-full" />} top="40%" left="85%" delay={2} />
          <FloatingIcon icon={<div className="w-24 h-24 bg-brand-berry/5 rounded-3xl rotate-12" />} top="70%" left="15%" delay={4} />
          <FloatingIcon icon={<Sparkles className="w-8 h-8" />} top="85%" left="80%" delay={1} />
          <FloatingIcon icon={<div className="w-12 h-12 bg-brand-secondary/5 rounded-xl -rotate-12" />} top="10%" left="60%" delay={3} />
        </div>

        {/* Global Noise Texture */}
        <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/dust.png')] opacity-[0.03] contrast-150" />
      </div>
    </div>
  );
}

function FloatingIcon({ icon, top, left, delay = 0 }: { icon: React.ReactNode, top: string, left: string, delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ 
        opacity: [0.3, 0.6, 0.3],
        y: [0, -20, 0],
        rotate: [0, 10, -10, 0]
      }}
      transition={{ 
        duration: 8, 
        repeat: Infinity, 
        delay,
        ease: "easeInOut" 
      }}
      style={{ top, left }}
      className="absolute text-brand-primary/10"
    >
      {icon}
    </motion.div>
  );
}
