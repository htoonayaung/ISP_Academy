import { statusTone } from "../../lib/format";

const tones = {
  green: "bg-emerald-100 text-emerald-800",
  red: "bg-rose-100 text-rose-800",
  yellow: "bg-amber-100 text-amber-800",
  gray: "bg-slate-100 text-slate-700",
  blue: "bg-sky-100 text-sky-800"
};

export function Badge({ value }: { value: string }) {
  return <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${tones[statusTone(value)]}`}>{value}</span>;
}
