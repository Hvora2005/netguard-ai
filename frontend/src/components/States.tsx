import { AlertCircle, Radar, ScanSearch } from "lucide-react";

export function LoadingState({ label = "Loading" }: { label?: string }) {
  return (
    <div className="panel flex items-center justify-center gap-3 p-10 text-sm text-slate-400">
      <Radar className="animate-spin text-signal-400" size={16} style={{ animationDuration: "1.6s" }} />
      {label}
    </div>
  );
}

export function EmptyState({ title, description }: { title: string; description?: string }) {
  return (
    <div className="panel flex flex-col items-center gap-2 border-dashed bg-slate-900/20 p-10 text-center">
      <ScanSearch className="text-slate-600" size={26} strokeWidth={1.5} />
      <p className="text-sm font-medium text-slate-300">{title}</p>
      {description && <p className="max-w-md text-xs leading-relaxed text-slate-500">{description}</p>}
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-2.5 rounded-xl border border-red-900/40 bg-red-950/20 p-4 text-sm text-red-300">
      <AlertCircle size={16} className="mt-0.5 shrink-0" />
      {message}
    </div>
  );
}
