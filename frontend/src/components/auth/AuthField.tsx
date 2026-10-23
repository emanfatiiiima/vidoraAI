import type { InputHTMLAttributes, ReactNode } from "react";

type AuthFieldProps = InputHTMLAttributes<HTMLInputElement> & {
  icon: ReactNode;
};

/** Text input with a leading icon, shared by the login / signup / reset screens. */
export default function AuthField({ icon, ...inputProps }: AuthFieldProps) {
  return (
    <div className="relative">
      <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-400 [&_svg]:w-4 [&_svg]:h-4">{icon}</span>
      <input {...inputProps} className="input-field pl-10" />
    </div>
  );
}
