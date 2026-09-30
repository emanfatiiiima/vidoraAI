import React, { useState } from "react";
import { motion } from "motion/react";
import BearCharacter from "./BearCharacter";
import AuthField from "./AuthField";
import Notice from "../ui/Notice";
import { Spinner } from "../ui/LoadingDonut";
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
    // Simulated sign-in delay (authentication is mocked).
    await new Promise(resolve => setTimeout(resolve, 800));
    setIsLoading(false);
    onLogin(email);
  };

  return (
    <div className="min-h-screen bg-[#f8f9ff] flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-pane w-full max-w-sm"
      >
        <BearCharacter isCoveringEyes={isCoveringEyes} />

        <h2 className="text-2xl font-bold text-center text-zinc-900 mb-1">Welcome back!</h2>
        <p className="text-zinc-600 text-center text-sm mb-6">Ready to craft some viral content?</p>

        <form onSubmit={handleSubmit} className="space-y-3">
          <AuthField
            icon={<Mail />}
            type="email"
            placeholder="Email (must be @gmail.com)"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <AuthField
            icon={<Lock />}
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onFocus={() => setIsCoveringEyes(true)}
            onBlur={() => setIsCoveringEyes(false)}
            required
          />

          {error && <Notice>{error}</Notice>}

          <button type="submit" disabled={isLoading} className="btn-dark w-full !py-3">
            {isLoading ? <Spinner /> : null}
            <span>{isLoading ? "Signing in..." : "Log in"}</span>
            {!isLoading && <ArrowRight className="w-4 h-4" />}
          </button>
        </form>

        <div className="mt-6 pt-5 border-t border-black/10 flex flex-col gap-2 text-center text-sm">
          <button onClick={() => onNavigate('forgot')} className="text-amber-800 hover:text-amber-950 font-medium">
            Forgot password?
          </button>
          <p className="text-zinc-600">
            Don't have an account?{" "}
            <button onClick={() => onNavigate('signup')} className="text-amber-800 hover:text-amber-950 font-semibold">
              Sign up
            </button>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
