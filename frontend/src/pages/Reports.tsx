import { useEffect, useState } from "react";

import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { useToast } from "../hooks/useToast";
import { api, extractErrorMessage } from "../services/api";
import type { ExperimentSummary, ReportSummary } from "../types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string) ?? "http://localhost:8000/api";

export default function Reports() {
  const { push } = useToast();
  const [experiments, setExperiments] = useState<ExperimentSummary[]>([]);
  const [experimentId, setExperimentId] = useState<number | null>(null);
  const [reports, setReports] = useState<ReportSummary[] | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadReports = () => {
    api.get<ReportSummary[]>("/reports").then((res) => setReports(res.data));
  };

  useEffect(() => {
    api.get<ExperimentSummary[]>("/experiments").then((res) => {
      const completed = res.data.filter((e) => e.status === "completed");
      setExperiments(completed);
      if (completed.length > 0) setExperimentId(completed[0].id);
    });
    loadReports();
  }, []);

  const handleGenerate = async () => {
    if (experimentId === null) return;
    setGenerating(true);
    setError(null);
    try {
      await api.post("/reports/generate", { experiment_id: experimentId, formats: ["html", "csv", "pdf"] });
      push("Report generated", "success");
      loadReports();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setGenerating(false);
    }
  };

  if (experiments.length === 0) {
    return (
      <EmptyState title="No completed experiments yet" description="Train a model in Model Training first — reports are generated from completed experiments." />
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-100">Reports</h2>
        <p className="text-sm text-slate-500">
          Generate a report combining dataset info, preprocessing config, metrics, feature importance, traffic stats, and
          alerts for a completed experiment.
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-4 panel">
        <label className="block">
          <span className="mb-1 block text-xs font-medium text-slate-400">Experiment</span>
          <select className="select" value={experimentId ?? ""} onChange={(e) => setExperimentId(Number(e.target.value))}>
            {experiments.map((e) => (
              <option key={e.id} value={e.id}>
                #{e.id} · {e.model_type}
              </option>
            ))}
          </select>
        </label>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="btn-primary"
        >
          {generating ? "Generating…" : "Generate report"}
        </button>
      </div>

      {error && <ErrorState message={error} />}

      {!reports ? (
        <LoadingState />
      ) : reports.length === 0 ? (
        <EmptyState title="No reports yet" description="Generate one above." />
      ) : (
        <div className="overflow-x-auto panel-table">
          <table className="min-w-full text-left text-xs">
            <thead className="bg-slate-900/60 text-slate-500">
              <tr>
                <th className="px-3 py-2">Report</th>
                <th className="px-3 py-2">Experiment</th>
                <th className="px-3 py-2">Downloads</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((r) => (
                <tr key={r.id} className="border-t border-slate-800 text-slate-300">
                  <td className="px-3 py-2">#{r.id}</td>
                  <td className="px-3 py-2">#{r.experiment_id}</td>
                  <td className="px-3 py-2">
                    <div className="flex gap-3">
                      {r.html_path && (
                        <a className="text-signal-400 hover:underline" href={`${API_BASE}/reports/${r.id}/download?format=html`} target="_blank" rel="noreferrer">
                          HTML
                        </a>
                      )}
                      {r.csv_path && (
                        <a className="text-signal-400 hover:underline" href={`${API_BASE}/reports/${r.id}/download?format=csv`} target="_blank" rel="noreferrer">
                          CSV
                        </a>
                      )}
                      {r.pdf_path && (
                        <a className="text-signal-400 hover:underline" href={`${API_BASE}/reports/${r.id}/download?format=pdf`} target="_blank" rel="noreferrer">
                          PDF
                        </a>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
