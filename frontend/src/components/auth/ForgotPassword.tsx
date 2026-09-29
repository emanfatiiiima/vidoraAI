import React, { useState } from "react";
import { motion } from "motion/react";
import BearCharacter from "./BearCharacter";
import { Mail, ArrowLeft, Send } from "lucide-react";

interface ForgotPasswordProps {
  onNavigate: (page: 'login') => void;
}

export default function ForgotPassword({ onNavigate }: ForgotPasswordProps) {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSent(true);
  };

  return (
    <div className="min-h-screen bg-[#fafafa] flex items-center justify-center p-4">
      <motion.div 
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="bg-white p-10 rounded-[40px] shadow-2xl w-full max-w-md border-4 border-zinc-100"
      >
        <BearCharacter isCoveringEyes={false} />
        
        <h2 className="text-3xl font-bold text-center text-zinc-800 mb-2">Forgot Password</h2>
        <p className="text-zinc-500 text-center mb-8 italic">Don't worry, even creators forget sometimes.</p>

        {!sent ? (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-400 w-5 h-5" />
              <input
                type="email"
                placeholder="Email address"
                className="w-full pl-12 pr-4 py-4 bg-zinc-50 border-2 border-zinc-100 rounded-2xl focus:border-amber-400 focus:outline-none transition-colors"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.95 }}
              type="submit"
              className="w-full py-4 bg-zinc-900 hover:bg-black text-white font-black rounded-2xl shadow-xl flex items-center justify-center space-x-2 transition-all"
            >
              <span>Reset via Email</span>
              <Send className="w-5 h-5" />
            </motion.button>
          </form>
        ) : (
          <div className="text-center space-y-6">
            <div className="bg-green-50 text-green-700 p-4 rounded-2xl border border-green-100">
              Check your inbox! A reset link has been sent to <strong>{email}</strong>.
            </div>
          </div>
        )}

        <div className="mt-8 pt-6 border-t border-zinc-100 text-center">
          <button 
            onClick={() => onNavigate('login')}
            className="flex items-center justify-center space-x-2 text-zinc-500 hover:text-amber-600 font-medium mx-auto"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Login</span>
          </button>
        </div>
      </motion.div>
    </div>
  );
}
