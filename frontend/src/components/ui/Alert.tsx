export function Alert({ message, className = "" }: { message: string; className?: string }) {
  return <div className={`rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800 ${className}`}>{message}</div>;
}
