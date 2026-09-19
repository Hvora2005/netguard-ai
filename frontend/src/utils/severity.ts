export const SEVERITY_ORDER = ["none", "low", "medium", "high", "critical"] as const;

export const SEVERITY_TEXT: Record<string, string> = {
  none: "text-slate-500",
  low: "text-sky-400",
  medium: "text-amber-400",
  high: "text-orange-400",
  critical: "text-red-400",
};

export const SEVERITY_BADGE: Record<string, string> = {
  none: "border-slate-700 text-slate-400",
  low: "border-sky-800 bg-sky-500/10 text-sky-300",
  medium: "border-amber-800 bg-amber-500/10 text-amber-300",
  high: "border-orange-800 bg-orange-500/10 text-orange-300",
  critical: "border-red-800 bg-red-500/10 text-red-300",
};
