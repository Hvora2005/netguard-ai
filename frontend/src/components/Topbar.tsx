import { useEffect, useState } from "react";

import { api } from "../services/api";

export default function Topbar() {
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .get("/health")
      .then(() => !cancelled && setBackendOnline(true))
      .catch(() => !cancelled && setBackendOnline(false));
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <header className="flex items-center justify-between border-b border-slate-800/70 bg-[#080d18]/80 px-6 py-4 backdrop-blur">
      <div>
        <h1 className="text-lg font-semibold tracking-tight text-slate-100">Network threat analytics</h1>
        <p className="text-xs text-slate-500">Defensive traffic analysis &amp; ML classification</p>
      </div>
      <div className="flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900/60 px-3 py-1.5 text-xs">
        <span className="relative flex h-2 w-2">
          {backendOnline && (
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-signal-400 opacity-60" />
          )}
          <span
            className={`relative inline-flex h-2 w-2 rounded-full ${
              backendOnline === null ? "bg-slate-500" : backendOnline ? "bg-signal-400" : "bg-red-500"
            }`}
          />
        </span>
        <span className="text-slate-400">
          {backendOnline === null ? "Checking backend…" : backendOnline ? "Backend online" : "Backend unreachable"}
        </span>
      </div>
    </header>
  );
}
