import { Spinner } from "./Spinner";

export function LoadingState({ message = "Loading..." }: { message?: string }) {
  return (
    <div className="flex min-h-32 items-center justify-center gap-3 rounded-md border border-slate-200 bg-white p-6 text-sm text-slate-600">
      <Spinner />
      <span>{message}</span>
    </div>
  );
}
