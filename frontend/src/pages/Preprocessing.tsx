import { useEffect, useState } from "react";

import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { api, extractErrorMessage } from "../services/api";
import type { DatasetSummary, PreprocessingConfig, PreprocessingPreviewResponse } from "../types";

const DEFAULT_CONFIG: PreprocessingConfig = {
  feature_columns: null,
  missing_strategy: "median",
  scaling: "standard",
  categorical_encoding: "onehot",
  handle_imbalance: "none",
  test_size: 0.2,
  task_type: "multiclass",
  benign_labels: ["BENIGN", "Benign", "benign", "0", "Normal"],
  random_state: 42,
};

export default function Preprocessing() {
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [datasetId, setDatasetId] = useState<number | null>(null);
  const [config, setConfig] = useState<PreprocessingConfig>(DEFAULT_CONFIG);
  const [result, setResult] = useState<PreprocessingPreviewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<DatasetSummary[]>("/datasets").then((res) => {
      setDatasets(res.data);
      if (res.data.length > 0) setDatasetId(res.data[0].id);
    });
  }, []);

  const runPreview = async () => {
    if (datasetId === null) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.post<PreprocessingPreviewResponse>("/preprocessing/preview", {
        dataset_id: datasetId,
        config,
      });
      setResult(res.data);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (datasets.length === 0) {
    return (
      <EmptyState
        title="No datasets available"
        description="Upload or load a dataset in Dataset Explorer first, then come back here to configure preprocessing."
      />
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-100">Preprocessing Pipeline</h2>
        <p className="text-sm text-slate-500">
          Configure how raw traffic is cleaned and transformed. This preview fits on the full dataset for illustration only —
          real training always fits preprocessing on the training split alone.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <div className="space-y-4 panel">
          <Field label="Dataset">
            <select
              className="select"
              value={datasetId ?? ""}
              onChange={(e) => setDatasetId(Number(e.target.value))}
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.original_filename}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Task type">
            <select
              className="select"
              value={config.task_type}
              onChange={(e) => setConfig({ ...config, task_type: e.target.value as any })}
            >
              <option value="binary">Binary (Benign vs Malicious)</option>
              <option value="multiclass">Multiclass (per attack category)</option>
            </select>
          </Field>

          <Field label="Missing value strategy">
            <select
              className="select"
              value={config.missing_strategy}
              onChange={(e) => setConfig({ ...config, missing_strategy: e.target.value as any })}
            >
              <option value="median">Median</option>
              <option value="mean">Mean</option>
              <option value="most_frequent">Most frequent</option>
              <option value="drop_rows">Drop rows</option>
            </select>
          </Field>

          <Field label="Numeric scaling">
            <select
              className="select"
              value={config.scaling}
              onChange={(e) => setConfig({ ...config, scaling: e.target.value as any })}
            >
              <option value="standard">Standardization (z-score)</option>
              <option value="minmax">Min-Max</option>
              <option value="none">None</option>
            </select>
          </Field>

          <Field label="Categorical encoding">
            <select
              className="select"
              value={config.categorical_encoding}
              onChange={(e) => setConfig({ ...config, categorical_encoding: e.target.value as any })}
            >
              <option value="onehot">One-hot</option>
              <option value="label">Ordinal / label</option>
            </select>
          </Field>

          <Field label="Class imbalance handling">
            <select
              className="select"
              value={config.handle_imbalance}
              onChange={(e) => setConfig({ ...config, handle_imbalance: e.target.value as any })}
            >
              <option value="none">None</option>
              <option value="smote">SMOTE oversampling</option>
              <option value="class_weight">Class weights</option>
            </select>
          </Field>

          <Field label={`Test split: ${(config.test_size * 100).toFixed(0)}%`}>
            <input
              type="range"
              min={0.1}
              max={0.5}
              step={0.05}
              value={config.test_size}
              onChange={(e) => setConfig({ ...config, test_size: Number(e.target.value) })}
              className="w-full"
            />
          </Field>

          <button
            onClick={runPreview}
            disabled={loading}
            className="w-full btn-primary"
          >
            {loading ? "Running preview…" : "Preview before / after"}
          </button>
        </div>

        <div className="space-y-4">
          {error && <ErrorState message={error} />}
          {loading && <LoadingState label="Fitting preprocessing preview…" />}
          {!loading && !result && !error && (
            <EmptyState title="No preview yet" description="Configure the pipeline and click Preview before / after." />
          )}
          {result && (
            <>
              <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                <Stat label="Rows before" value={result.before_row_count} />
                <Stat label="Rows after" value={result.after_row_count} />
                <Stat label="Numeric features" value={result.numeric_feature_count} />
                <Stat label="Categorical features" value={result.categorical_feature_count} />
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <Distribution title="Class distribution — before" data={result.before_class_distribution} />
                <Distribution title="Class distribution — after" data={result.after_class_distribution} />
              </div>

              <div className="panel">
                <h3 className="mb-2 text-sm font-medium text-slate-300">Notes</h3>
                <ul className="list-inside list-disc space-y-1 text-xs text-slate-400">
                  {result.notes.map((note, idx) => (
                    <li key={idx}>{note}</li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-slate-400">{label}</span>
      {children}
    </label>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="panel-tight">
      <p className="text-[11px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-slate-100">{value}</p>
    </div>
  );
}

function Distribution({ title, data }: { title: string; data: Record<string, number> }) {
  const total = Object.values(data).reduce((a, b) => a + b, 0) || 1;
  return (
    <div className="panel">
      <h3 className="mb-2 text-sm font-medium text-slate-300">{title}</h3>
      <div className="space-y-1">
        {Object.entries(data).map(([label, count]) => (
          <div key={label} className="flex items-center gap-2 text-xs">
            <span className="w-24 truncate text-slate-400">{label}</span>
            <div className="h-1.5 flex-1 rounded-full bg-slate-800/70">
              <div className="h-1.5 rounded-full bg-signal-500" style={{ width: `${(count / total) * 100}%` }} />
            </div>
            <span className="w-14 text-right text-slate-500">{count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
