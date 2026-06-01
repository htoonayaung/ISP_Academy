import { TextareaHTMLAttributes } from "react";

export function Textarea({ className = "", ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={`min-h-24 w-full rounded-md border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-600 ${className}`} {...props} />;
}
