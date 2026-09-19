import { useEffect, useState } from "react";

import MetricsView from "../components/MetricsView";
import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { api, extractErrorMessage } from "../services/api";
import type { ExperimentDetail, ExperimentSummary } from "../types";

export default function Experiments() {
  const [experiments, setExperiments] = useState<ExperimentSummary[] | null>(null);
  const [selected, setSelected] = useState<ExperimentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<ExperimentSummary[]>("/experiments")
      .then((res) => setExperiments(res.data))
      .catch((err) => setError(extractErrorMessage(err)));
  }, []);

  const openExperiment = (id: number) => {
    api.get<ExperimentDetail>(`/experiments/${id}`).then((res) => setSelected(res.data));
  };

  if (error) return <ErrorState message={error} />;
  if (!experiments) return <LoadingState />;
  if (experiments.length === 0) {
    return <EmptyState title="No experiments yet" description="Train a model from Model Training to see it tracked here." />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-100">Experiments</h2>
        <p className="text-sm text-slate-500">Every training run is recorded with its configuration and metrics.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
        <div className="overflow-hidden panel-table">
          <table className="min-w-full text-left text-xs">
            <thead className="bg-slate-900/60 text-slate-500">
              <tr>
                <th className="px-3 py-2">ID</th>
                <th className="px-3 py-2">Model</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Duration</th>
              </tr>
            </thead>
            <tbody>
              {experiments.map((e) => (
                <tr
                  key={e.id}
                  onClick={() => openExperiment(e.id)}
                  className={`cursor-pointer border-t border-slate-800 hover:bg-slate-900 ${
                    selected?.id === e.id ? "bg-slate-900" : ""
                  }`}
                >
                  <td className="px-3 py-2 text-slate-300">#{e.id}</td>
                  <td className="px-3 py-2 text-slate-300">{e.model_type}</td>
                  <td
                    className={`px-3 py-2 ${
                      e.status === "completed"
                        ? "text-signal-400"
                        : e.status === "failed"
                          ? "text-red-400"
                          : "text-amber-400"
                    }`}
                  >
                    {e.status}
                  </td>
                  <td className="px-3 py-2 text-slate-400">{e.duration_seconds?.toFixed(2) ?? "—"}s</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div>
          {!selected && <EmptyState title="Select an experiment" description="Click a row to view its full configuration and metrics." />}
          {selected && (
            <div className="space-y-4">
              <div className="panel text-xs text-slate-400">
                <p>
                  <span className="text-slate-500">Dataset ID:</span> {selected.dataset_id} ·{" "}
                  <span className="text-slate-500">Task:</span> {selected.task_type}
                </p>
                {selected.error_message && <p className="mt-2 text-red-400">{selected.error_message}</p>}
              </div>
              {selected.metrics && <MetricsView metrics={selected.metrics} />}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
