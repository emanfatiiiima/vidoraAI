import { motion } from "motion/react";

export default function LoadingDonut() {
  return (
    <div className="flex flex-col items-center justify-center space-y-4">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
        className="relative w-24 h-24 rounded-full border-[12px] border-transparent border-t-pink-400 border-r-yellow-400 border-b-cyan-400 border-l-purple-400 shadow-xl"
      >
        <div className="absolute inset-0 m-2 rounded-full bg-white opacity-20" />
      </motion.div>
      <motion.p
        animate={{ scale: [1, 1.1, 1] }}
        transition={{ repeat: Infinity, duration: 1.5 }}
        className="text-white font-bold text-lg drop-shadow-md"
      >
        Sprinkling some magic...
      </motion.p>
    </div>
  );
}
