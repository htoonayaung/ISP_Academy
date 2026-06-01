import { ReactNode } from "react";
import { Button } from "./Button";

export function Modal({ title, children, onClose }: { title: string; children: ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4">
      <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-lg bg-white p-5 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">{title}</h2>
          <Button className="bg-slate-200 text-slate-900 hover:bg-slate-300" onClick={onClose}>Close</Button>
        </div>
        {children}
      </div>
    </div>
  );
}
