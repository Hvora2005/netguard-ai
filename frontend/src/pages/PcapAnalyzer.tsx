import { useEffect, useState } from "react";

import { EmptyState, ErrorState } from "../components/States";
import { useToast } from "../hooks/useToast";
import { api, extractErrorMessage } from "../services/api";
import type { MLModelSummary, PcapAnalyzeResponse } from "../types";

export default function PcapAnalyzer() {
  const { push } = useToast();
  const [models, setModels] = useState<MLModelSummary[]>([]);
  const [modelId, setModelId] = useState<number | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<PcapAnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<MLModelSummary[]>("/models").then((res) => {
      setModels(res.data);
      const active = res.data.find((m) => m.is_active) ?? res.data[0];
      if (active) setModelId(active.id);
    });
  }, []);

  const handleUpload = async (file: File) => {
    if (modelId === null) return;
    setAnalyzing(true);
    setError(null);
    setResult(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("model_id", String(modelId));
      const res = await api.post<PcapAnalyzeResponse>("/pcap/analyze", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(res.data);
      push(`Analyzed ${res.data.flow_count} flows`, "success");
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setAnalyzing(false);
    }
  };

  if (models.length === 0) {
    return <EmptyState title="No trained models yet" description="Train a model before analyzing PCAP traffic with it." />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-100">PCAP Analyzer</h2>
        <p className="text-sm text-slate-500">
          Upload a .pcap/.pcapng capture. Flows are grouped by unidirectional 5-tuple (source/destination IP+port and
          protocol), classified with the selected model, and written to Traffic Explorer and Security Alerts.
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-4 panel">
        <label className="block">
          <span className="mb-1 block text-xs font-medium text-slate-400">Model to classify with</span>
          <select className="select" value={modelId ?? ""} onChange={(e) => setModelId(Number(e.target.value))}>
            {models.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} {m.is_active ? "(active)" : ""}
              </option>
            ))}
          </select>
        </label>

        <label className="cursor-pointer btn-primary">
          {analyzing ? "Analyzing…" : "Upload .pcap / .pcapng"}
          <input
            type="file"
            accept=".pcap,.pcapng"
            className="hidden"
            disabled={analyzing}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleUpload(file);
              e.target.value = "";
            }}
          />
        </label>
      </div>

      {error && <ErrorState message={error} />}

      {result && (
        <div className="grid gap-4 md:grid-cols-3">
          <div className="panel">
            <p className="text-xs uppercase tracking-wide text-slate-500">Flows extracted</p>
            <p className="mt-1 text-2xl font-semibold text-slate-100">{result.flow_count}</p>
          </div>
          <div className="panel">
            <p className="text-xs uppercase tracking-wide text-slate-500">Alerts created</p>
            <p className="mt-1 text-2xl font-semibold text-slate-100">{result.alerts_created}</p>
          </div>
          <div className="panel">
            <p className="text-xs uppercase tracking-wide text-slate-500">Model used</p>
            <p className="mt-1 text-lg font-semibold text-slate-100">{result.model_used}</p>
          </div>
          <div className="md:col-span-3 panel">
            <h3 className="mb-2 text-sm font-medium text-slate-300">Classification breakdown</h3>
            <div className="flex flex-wrap gap-2">
              {Object.entries(result.classification_breakdown).map(([label, count]) => (
                <span key={label} className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-300">
                  {label}: {count}
                </span>
              ))}
            </div>
            <p className="mt-3 text-xs text-slate-500">
              View full details in Traffic Explorer and Security Alerts.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
