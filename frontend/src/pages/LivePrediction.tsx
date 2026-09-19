import { useEffect, useState } from "react";

import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { api, extractErrorMessage } from "../services/api";
import type { MLModelSummary, ModelFeatureSchema, PredictionResponse } from "../types";

export default function LivePrediction() {
  const [models, setModels] = useState<MLModelSummary[]>([]);
  const [modelId, setModelId] = useState<number | null>(null);
  const [schema, setSchema] = useState<ModelFeatureSchema | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<MLModelSummary[]>("/models").then((res) => {
      setModels(res.data);
      const active = res.data.find((m) => m.is_active) ?? res.data[0];
      if (active) setModelId(active.id);
    });
  }, []);

  useEffect(() => {
    if (modelId === null) return;
    setSchema(null);
    setResult(null);
    api
      .get<ModelFeatureSchema>(`/models/${modelId}/feature-schema`)
      .then((res) => {
        setSchema(res.data);
        setValues({});
      })
      .catch((err) => setError(extractErrorMessage(err)));
  }, [modelId]);

  const handlePredict = async () => {
    if (modelId === null || !schema) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const features: Record<string, string | number> = {};
      for (const field of schema.fields) {
        const raw = values[field.name];
        if (raw === undefined || raw === "") continue;
        features[field.name] = field.is_numeric ? Number(raw) : raw;
      }
      const res = await api.post<PredictionResponse>("/predict", { model_id: modelId, features });
      setResult(res.data);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (models.length === 0) {
    return (
      <EmptyState
        title="No trained models yet"
        description="Train a model in Model Training first, then come back here to run live predictions against it."
      />
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-100">Live Prediction</h2>
        <p className="text-sm text-slate-500">
          Enter flow-level features manually. Confidence is the model's own predicted probability — nothing here is
          invented by the frontend.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
        <div className="space-y-4 panel">
          <label className="block">
            <span className="mb-1 block text-xs font-medium text-slate-400">Model</span>
            <select className="select" value={modelId ?? ""} onChange={(e) => setModelId(Number(e.target.value))}>
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} {m.is_active ? "(active)" : ""}
                </option>
              ))}
            </select>
          </label>

          {!schema ? (
            <LoadingState label="Loading feature schema…" />
          ) : (
            <>
              {schema.fields.map((field) => (
                <label key={field.name} className="block">
                  <span className="mb-1 block text-xs font-medium text-slate-400">{field.name}</span>
                  <input
                    className="select"
                    type={field.is_numeric ? "number" : "text"}
                    value={values[field.name] ?? ""}
                    onChange={(e) => setValues({ ...values, [field.name]: e.target.value })}
                    placeholder={field.is_numeric ? "0" : "e.g. TCP"}
                  />
                </label>
              ))}
              <button
                onClick={handlePredict}
                disabled={loading}
                className="w-full btn-primary"
              >
                {loading ? "Predicting…" : "Predict"}
              </button>
            </>
          )}
        </div>

        <div className="space-y-4">
          {error && <ErrorState message={error} />}
          {!result && !error && !loading && (
            <EmptyState title="No prediction yet" description="Fill in the flow features and click Predict." />
          )}
          {result && (
            <>
              <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-6 text-center">
                <p className="text-xs uppercase tracking-wide text-slate-500">Prediction</p>
                <p className={`mt-1 text-3xl font-bold ${result.predicted_class.toLowerCase() === "benign" ? "text-signal-400" : "text-red-400"}`}>
                  {result.predicted_class}
                </p>
                {result.confidence !== null && (
                  <p className="mt-1 text-sm text-slate-400">Confidence: {(result.confidence * 100).toFixed(1)}%</p>
                )}
              </div>

              {result.probabilities && (
                <div className="panel">
                  <h3 className="mb-2 text-sm font-medium text-slate-300">Class probabilities</h3>
                  <div className="space-y-1">
                    {Object.entries(result.probabilities)
                      .sort((a, b) => b[1] - a[1])
                      .map(([label, p]) => (
                        <div key={label} className="flex items-center gap-2 text-xs">
                          <span className="w-24 truncate text-slate-400">{label}</span>
                          <div className="h-1.5 flex-1 rounded-full bg-slate-800/70">
                            <div className="h-1.5 rounded-full bg-signal-500" style={{ width: `${p * 100}%` }} />
                          </div>
                          <span className="w-14 text-right text-slate-500">{(p * 100).toFixed(1)}%</span>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {result.explanation && (
                <div className="panel">
                  <h3 className="mb-1 text-sm font-medium text-slate-300">Contributing features</h3>
                  <p className="mb-2 text-[11px] text-slate-500">
                    Method: {result.explanation_method}. This describes model behavior, not a causal real-world explanation.
                  </p>
                  <div className="space-y-1">
                    {result.explanation.map((item) => {
                      const max = Math.max(...result.explanation!.map((e) => Math.abs(e.contribution)));
                      const width = max > 0 ? (Math.abs(item.contribution) / max) * 100 : 0;
                      return (
                        <div key={item.feature} className="flex items-center gap-2 text-xs">
                          <span className="w-40 truncate text-slate-400">{item.feature.replace(/^(numeric|categorical)__/, "")}</span>
                          <div className="h-1.5 flex-1 rounded-full bg-slate-800/70">
                            <div
                              className={`h-2 rounded ${item.contribution >= 0 ? "bg-signal-500" : "bg-red-500"}`}
                              style={{ width: `${width}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
