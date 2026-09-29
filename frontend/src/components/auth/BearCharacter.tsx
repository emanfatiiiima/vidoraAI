import React from "react";
import { motion } from "motion/react";

interface BearCharacterProps {
  isCoveringEyes?: boolean;
}

export default function BearCharacter({ isCoveringEyes = false }: BearCharacterProps) {
  return (
    <div className="relative w-32 h-32 mx-auto mb-8">
      {/* Ears */}
      <div className="absolute -top-2 -left-2 w-10 h-10 bg-amber-700 rounded-full border-4 border-amber-100" />
      <div className="absolute -top-2 -right-2 w-10 h-10 bg-amber-700 rounded-full border-4 border-amber-100" />
      
      {/* Face background */}
      <div className="absolute inset-0 bg-amber-700 rounded-full border-4 border-amber-100 shadow-lg overflow-hidden">
        {/* Inner face glow */}
        <div className="absolute inset-2 bg-amber-600/20 rounded-full blur-md" />
        
        {/* Eyes - disappear when covered */}
        <motion.div 
          animate={{ opacity: isCoveringEyes ? 0 : 1, scale: isCoveringEyes ? 0.5 : 1 }}
          transition={{ duration: 0.2 }}
          className="absolute top-10 left-8 w-3 h-3 bg-zinc-900 rounded-full" 
        />
        <motion.div 
          animate={{ opacity: isCoveringEyes ? 0 : 1, scale: isCoveringEyes ? 0.5 : 1 }}
          transition={{ duration: 0.2 }}
          className="absolute top-10 right-8 w-3 h-3 bg-zinc-900 rounded-full" 
        />

        {/* Nose & Mouth Area */}
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 w-14 h-10 bg-white rounded-full flex flex-col items-center justify-center shadow-inner">
          <div className="w-5 h-3 bg-zinc-900 rounded-full mb-0.5" />
          <div className="flex space-x-[-1px]">
            <div className="w-3 h-2 border-b-2 border-zinc-900 rounded-full" />
            <div className="w-3 h-2 border-b-2 border-zinc-900 rounded-full" />
          </div>
        </div>
      </div>

      {/* Paws (Arms) - Precise movement to eyes */}
      <motion.div
        animate={{
          y: isCoveringEyes ? -45 : 15,
          rotate: isCoveringEyes ? 25 : -45,
          x: isCoveringEyes ? 25 : 0
        }}
        transition={{ type: "spring", stiffness: 300, damping: 25 }}
        className="absolute left-[-10px] bottom-0 w-12 h-16 bg-amber-700 rounded-full border-4 border-amber-100 shadow-md z-20"
      />
      <motion.div
        animate={{
          y: isCoveringEyes ? -45 : 15,
          rotate: isCoveringEyes ? -25 : 45,
          x: isCoveringEyes ? -25 : 0
        }}
        transition={{ type: "spring", stiffness: 300, damping: 25 }}
        className="absolute right-[-10px] bottom-0 w-12 h-16 bg-amber-700 rounded-full border-4 border-amber-100 shadow-md z-20"
      />
    </div>
  );
}
