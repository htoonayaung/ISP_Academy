import { ReactNode } from "react";

export function Table({ children }: { children: ReactNode }) {
  return <div className="overflow-x-auto rounded-md border border-slate-200"><table className="min-w-full divide-y divide-slate-200 text-sm">{children}</table></div>;
}

export function Th({ children }: { children: ReactNode }) {
  return <th className="bg-slate-50 px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-600">{children}</th>;
}

export function Td({ children }: { children: ReactNode }) {
  return <td className="px-3 py-2 align-top text-slate-800">{children}</td>;
}
