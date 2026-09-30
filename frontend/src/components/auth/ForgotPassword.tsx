import React, { useState } from "react";
import { motion } from "motion/react";
import BearCharacter from "./BearCharacter";
import AuthField from "./AuthField";
import Notice from "../ui/Notice";
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
    <div className="min-h-screen bg-[#f8f9ff] flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-pane w-full max-w-sm"
      >
        <BearCharacter isCoveringEyes={false} />

        <h2 className="text-2xl font-bold text-center text-zinc-900 mb-1">Forgot password</h2>
        <p className="text-zinc-600 text-center text-sm mb-6">Don't worry, even creators forget sometimes.</p>

        {!sent ? (
          <form onSubmit={handleSubmit} className="space-y-3">
            <AuthField
              icon={<Mail />}
              type="email"
              placeholder="Email address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <button type="submit" className="btn-dark w-full !py-3">
              <span>Send reset link</span>
              <Send className="w-4 h-4" />
            </button>
          </form>
        ) : (
          <Notice tone="success">
            Check your inbox! A reset link has been sent to <strong>{email}</strong>.
          </Notice>
        )}

        <div className="mt-6 pt-5 border-t border-black/10 text-center text-sm">
          <button onClick={() => onNavigate('login')} className="inline-flex items-center gap-1.5 text-amber-800 hover:text-amber-950 font-medium">
            <ArrowLeft className="w-4 h-4" />
            <span>Back to login</span>
          </button>
        </div>
      </motion.div>
    </div>
  );
}
