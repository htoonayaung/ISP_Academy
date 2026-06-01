import { InputHTMLAttributes } from "react";

export function Input({ className = "", ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={`h-9 w-full rounded-md border border-slate-300 px-3 text-sm outline-none focus:border-teal-600 ${className}`} {...props} />;
}
