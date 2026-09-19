import { useEffect, useState } from "react";

import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { api, extractErrorMessage } from "../services/api";
import type { GlobalExplanationResponse, MLModelSummary } from "../types";

const METHOD_LABELS: Record<string, string> = {
  shap: "SHAP (TreeExplainer)",
  model_feature_importance: "Model feature importance",
  model_coefficients: "Model coefficients (mean |coef|)",
  unavailable: "Not available for this model type",
};

export default function Explainability() {
  const [models, setModels] = useState<MLModelSummary[]>([]);
  const [modelId, setModelId] = useState<number | null>(null);
  const [result, setResult] = useState<GlobalExplanationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get<MLModelSummary[]>("/models").then((res) => {
      setModels(res.data);
      if (res.data.length > 0) setModelId(res.data[0].id);
    });
  }, []);

  useEffect(() => {
    if (modelId === null) return;
    setLoading(true);
    setError(null);
    api
      .get<GlobalExplanationResponse>(`/models/${modelId}/explain/global`)
      .then((res) => setResult(res.data))
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [modelId]);

  if (models.length === 0) {
    return <EmptyState title="No trained models yet" description="Train a model first to see its global feature importance." />;
  }

  const importances = result?.importances ?? [];
  const max = importances.length ? Math.max(...importances.map((i) => Math.abs(i.importance))) : 1;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-100">Explainability</h2>
        <p className="text-sm text-slate-500">
          Global feature importance — which features generally drive this model's decisions across all predictions.
          Not a causal explanation, and not specific to any single flow.
        </p>
      </div>

      <label className="block max-w-sm">
        <span className="mb-1 block text-xs font-medium text-slate-400">Model</span>
        <select className="select" value={modelId ?? ""} onChange={(e) => setModelId(Number(e.target.value))}>
          {models.map((m) => (
            <option key={m.id} value={m.id}>
              {m.name}
            </option>
          ))}
        </select>
      </label>

      {error && <ErrorState message={error} />}
      {loading && <LoadingState label="Computing global explanation…" />}

      {result && (
        <div className="panel">
          <p className="mb-3 text-xs text-slate-500">Method: {METHOD_LABELS[result.method] ?? result.method}</p>
          {importances.length === 0 ? (
            <EmptyState
              title="Not available"
              description="This model type doesn't expose feature importance or coefficients (e.g. KNN, non-linear SVM, or MLP without SHAP installed)."
            />
          ) : (
            <div className="space-y-2">
              {importances.map((item) => (
                <div key={item.feature} className="flex items-center gap-2 text-xs">
                  <span className="w-48 truncate text-slate-400">{item.feature.replace(/^(numeric|categorical)__/, "")}</span>
                  <div className="h-2 flex-1 rounded-full bg-slate-800/70">
                    <div
                      className="h-2 rounded-full bg-signal-500"
                      style={{ width: `${(Math.abs(item.importance) / max) * 100}%` }}
                    />
                  </div>
                  <span className="w-16 text-right text-slate-500">{item.importance.toFixed(4)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
