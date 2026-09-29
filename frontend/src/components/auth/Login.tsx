import React, { useState } from "react";
import { motion } from "motion/react";
import BearCharacter from "./BearCharacter";
import LoadingDonut from "../ui/LoadingDonut";
import { Mail, Lock, ArrowRight } from "lucide-react";

interface LoginProps {
  onLogin: (email: string) => void;
  onNavigate: (page: 'signup' | 'forgot') => void;
}

export default function Login({ onLogin, onNavigate }: LoginProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isCoveringEyes, setIsCoveringEyes] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    
    if (!email.endsWith("@gmail.com")) {
      setError("Email must end with @gmail.com");
      return;
    }
    
    if (password !== "1234" && password !== "eman") {
      setError("Invalid password. Try '1234' or 'eman'");
      return;
    }

    setIsLoading(true);
    // Simulate loading
    await new Promise(resolve => setTimeout(resolve, 2000));
    setIsLoading(false);
    onLogin(email);
  };

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-zinc-900 flex items-center justify-center z-50">
        <LoadingDonut />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white flex items-center justify-center p-4">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-pane w-full max-w-md"
      >
        <BearCharacter isCoveringEyes={isCoveringEyes} />
        
        <h2 className="text-3xl font-bold text-center text-zinc-800 mb-2">Welcome Back!</h2>
        <p className="text-zinc-500 text-center mb-8 italic">Ready to craft some viral content?</p>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="relative">
            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-400 w-5 h-5" />
            <input
              type="email"
              placeholder="Email (must be @gmail.com)"
              className="w-full pl-12 pr-4 py-4 bg-zinc-50 border-2 border-zinc-100 rounded-2xl focus:border-amber-400 focus:outline-none transition-colors"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="relative">
            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-400 w-5 h-5" />
            <input
              type="password"
              placeholder="Password"
              className="w-full pl-12 pr-4 py-4 bg-zinc-50 border-2 border-zinc-100 rounded-2xl focus:border-amber-400 focus:outline-none transition-colors"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onFocus={() => setIsCoveringEyes(true)}
              onBlur={() => setIsCoveringEyes(false)}
              required
            />
          </div>

          {error && <p className="text-red-500 text-center text-sm font-medium">{error}</p>}

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.95 }}
            type="submit"
            className="w-full py-4 bg-zinc-900 hover:bg-black text-white font-black rounded-2xl shadow-xl flex items-center justify-center space-x-2 transition-all"
          >
            <span>Log In</span>
            <ArrowRight className="w-5 h-5" />
          </motion.button>
        </form>

        <div className="mt-8 pt-6 border-t border-zinc-100 flex flex-col space-y-4 text-center">
          <button 
            onClick={() => onNavigate('forgot')}
            className="text-sm text-amber-600 hover:text-amber-800 font-medium"
          >
            Forgot Password?
          </button>
          <p className="text-sm text-zinc-500">
            Don't have an account?{" "}
            <button 
              onClick={() => onNavigate('signup')}
              className="text-amber-600 hover:text-amber-800 font-bold"
            >
              Sign Up
            </button>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
