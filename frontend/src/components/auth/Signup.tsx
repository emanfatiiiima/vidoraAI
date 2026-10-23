import React, { useState } from "react";
import { motion } from "motion/react";
import BearCharacter from "./BearCharacter";
import AuthField from "./AuthField";
import Notice from "../ui/Notice";
import { Mail, Lock, User, ArrowRight, ArrowLeft } from "lucide-react";

interface SignupProps {
  onNavigate: (page: 'login') => void;
}

export default function Signup({ onNavigate }: SignupProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [isCoveringEyes, setIsCoveringEyes] = useState(false);
  const [error, setError] = useState("");
  const [isCreated, setIsCreated] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.endsWith("@gmail.com")) {
      setError("Email must end with @gmail.com");
      return;
    }
    // Sign-up is simulated: show a confirmation inline instead of a popup.
    setError("");
    setIsCreated(true);
  };

  return (
    <div className="min-h-screen bg-[#f8f9ff] flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-pane w-full max-w-sm"
      >
        <BearCharacter isCoveringEyes={isCoveringEyes} />

        <h2 className="text-2xl font-bold text-center text-zinc-900 mb-1">Create account</h2>
        <p className="text-zinc-600 text-center text-sm mb-6">Join the next generation of creators.</p>

        {isCreated ? (
          <div className="space-y-4">
            <Notice tone="success">
              Account created for <strong>{email}</strong>. You can now log in.
            </Notice>
            <button onClick={() => onNavigate('login')} className="btn-dark w-full !py-3">
              <span>Continue to login</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-3">
            <AuthField
              icon={<User />}
              type="text"
              placeholder="Full name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
            <AuthField
              icon={<Mail />}
              type="email"
              placeholder="Email (@gmail.com)"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <AuthField
              icon={<Lock />}
              type="password"
              placeholder="Password (1234 or eman for demo)"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onFocus={() => setIsCoveringEyes(true)}
              onBlur={() => setIsCoveringEyes(false)}
              required
            />

            {error && <Notice>{error}</Notice>}

            <button type="submit" className="btn-dark w-full !py-3">
              <span>Sign up</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>
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
