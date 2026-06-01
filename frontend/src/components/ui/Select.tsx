import { SelectHTMLAttributes } from "react";

export function Select({ className = "", ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={`h-9 w-full rounded-md border border-slate-300 px-3 text-sm outline-none focus:border-teal-600 ${className}`} {...props} />;
}
