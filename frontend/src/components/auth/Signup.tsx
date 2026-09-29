import React, { useState } from "react";
import { motion } from "motion/react";
import BearCharacter from "./BearCharacter";
import { Mail, Lock, User, ArrowRight } from "lucide-react";

interface SignupProps {
  onNavigate: (page: 'login') => void;
}

export default function Signup({ onNavigate }: SignupProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [isCoveringEyes, setIsCoveringEyes] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.endsWith("@gmail.com")) {
      setError("Email must end with @gmail.com");
      return;
    }
    alert("Signup simulation successful! Please login.");
    onNavigate('login');
  };

  return (
    <div className="min-h-screen bg-[#fafafa] flex items-center justify-center p-4">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white p-10 rounded-[40px] shadow-2xl w-full max-w-md border-4 border-zinc-100"
      >
        <BearCharacter isCoveringEyes={isCoveringEyes} />
        
        <h2 className="text-3xl font-bold text-center text-zinc-800 mb-2">Create Account</h2>
        <p className="text-zinc-500 text-center mb-8 italic">Join the next generation of creators.</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <User className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Full Name"
              className="w-full pl-12 pr-4 py-4 bg-zinc-50 border-2 border-zinc-100 rounded-2xl focus:border-amber-400 focus:outline-none transition-colors"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div className="relative">
            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-400 w-5 h-5" />
            <input
              type="email"
              placeholder="Email (@gmail.com)"
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
              placeholder="Password (1234 or eman for demo)"
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
            className="w-full py-4 bg-zinc-900 hover:bg-black text-white font-black rounded-2xl shadow-xl flex items-center justify-center space-x-2 transition-all mt-4"
          >
            <span>Sign Up</span>
            <ArrowRight className="w-5 h-5" />
          </motion.button>
        </form>

        <div className="mt-8 pt-6 border-t border-zinc-100 text-center">
          <p className="text-sm text-zinc-500">
            Already have an account?{" "}
            <button 
              onClick={() => onNavigate('login')}
              className="text-amber-600 hover:text-amber-800 font-bold underline underline-offset-4"
            >
              Login
            </button>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
