import { useEffect, useState } from "react";

import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { useToast } from "../hooks/useToast";
import { api, extractErrorMessage } from "../services/api";
import type { ExperimentDetail, ExperimentSummary, MLModelSummary } from "../types";

export default function ModelComparison() {
  const { push } = useToast();
  const [rows, setRows] = useState<ExperimentDetail[] | null>(null);
  const [models, setModels] = useState<MLModelSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refreshModels = () => {
    api.get<MLModelSummary[]>("/models").then((res) => setModels(res.data));
  };

  useEffect(() => {
    api
      .get<ExperimentSummary[]>("/experiments")
      .then(async (res) => {
        const completed = res.data.filter((e) => e.status === "completed");
        const details = await Promise.all(completed.map((e) => api.get<ExperimentDetail>(`/experiments/${e.id}`)));
        setRows(details.map((r) => r.data));
      })
      .catch((err) => setError(extractErrorMessage(err)));
    refreshModels();
  }, []);

  const handleActivate = async (id: number) => {
    try {
      await api.put(`/models/${id}/activate`);
      push("Model set as active", "success");
      refreshModels();
    } catch (err) {
      push(extractErrorMessage(err), "error");
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await api.delete(`/models/${id}`);
      push("Model deleted", "success");
      refreshModels();
    } catch (err) {
      push(extractErrorMessage(err), "error");
    }
  };

  if (error) return <ErrorState message={error} />;
  if (!rows) return <LoadingState />;
  if (rows.length === 0) {
    return (
      <EmptyState
        title="No completed experiments yet"
        description="Train at least one model in Model Training to compare results here."
      />
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-100">Model Comparison</h2>
        <p className="text-sm text-slate-500">
          No single metric determines the "best" model — the right choice depends on which metric matters for your use case
          (e.g. recall matters more than precision when missing an attack is costlier than a false alarm) and on class
          distribution.
        </p>
      </div>

      <div className="overflow-x-auto panel-table">
        <table className="min-w-full text-left text-xs">
          <thead className="bg-slate-900/60 text-slate-500">
            <tr>
              <th className="px-3 py-2">Experiment</th>
              <th className="px-3 py-2">Model</th>
              <th className="px-3 py-2">Accuracy</th>
              <th className="px-3 py-2">Macro F1</th>
              <th className="px-3 py-2">Weighted F1</th>
              <th className="px-3 py-2">ROC-AUC</th>
              <th className="px-3 py-2">PR-AUC</th>
              <th className="px-3 py-2">Training time</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-t border-slate-800 text-slate-300">
                <td className="px-3 py-2">#{r.id}</td>
                <td className="px-3 py-2">{r.model_type}</td>
                <td className="px-3 py-2">{r.metrics ? `${(r.metrics.accuracy * 100).toFixed(2)}%` : "—"}</td>
                <td className="px-3 py-2">{r.metrics?.macro_f1.toFixed(3) ?? "—"}</td>
                <td className="px-3 py-2">{r.metrics?.weighted_f1.toFixed(3) ?? "—"}</td>
                <td className="px-3 py-2">{r.metrics?.roc_auc?.toFixed(3) ?? "N/A"}</td>
                <td className="px-3 py-2">{r.metrics?.pr_auc?.toFixed(3) ?? "N/A"}</td>
                <td className="px-3 py-2">{r.duration_seconds?.toFixed(2)}s</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div>
        <h3 className="mb-2 text-sm font-medium text-slate-300">Saved models</h3>
        {!models ? (
          <LoadingState />
        ) : models.length === 0 ? (
          <EmptyState title="No saved models" description="Completed training runs are saved here automatically." />
        ) : (
          <div className="overflow-x-auto panel-table">
            <table className="min-w-full text-left text-xs">
              <thead className="bg-slate-900/60 text-slate-500">
                <tr>
                  <th className="px-3 py-2">Name</th>
                  <th className="px-3 py-2">Type</th>
                  <th className="px-3 py-2">Task</th>
                  <th className="px-3 py-2">Active</th>
                  <th className="px-3 py-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {models.map((m) => (
                  <tr key={m.id} className="border-t border-slate-800 text-slate-300">
                    <td className="px-3 py-2">{m.name}</td>
                    <td className="px-3 py-2">{m.model_type}</td>
                    <td className="px-3 py-2">{m.task_type}</td>
                    <td className="px-3 py-2">{m.is_active ? <span className="text-signal-400">Active</span> : "—"}</td>
                    <td className="px-3 py-2">
                      <div className="flex gap-2">
                        {!m.is_active && (
                          <button onClick={() => handleActivate(m.id)} className="text-signal-400 hover:underline">
                            Set active
                          </button>
                        )}
                        <button onClick={() => handleDelete(m.id)} className="text-red-400 hover:underline">
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
