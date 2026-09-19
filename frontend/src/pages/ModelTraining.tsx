import { useEffect, useState } from "react";

import MetricsView from "../components/MetricsView";
import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { useToast } from "../hooks/useToast";
import { api, extractErrorMessage } from "../services/api";
import type { DatasetSummary, ExperimentDetail, PreprocessingConfig } from "../types";
import { MODEL_TYPES } from "../types";

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

export default function ModelTraining() {
  const { push } = useToast();
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [datasetId, setDatasetId] = useState<number | null>(null);
  const [modelType, setModelType] = useState<string>(MODEL_TYPES[0].value);
  const [modelName, setModelName] = useState("");
  const [config, setConfig] = useState<PreprocessingConfig>(DEFAULT_CONFIG);
  const [training, setTraining] = useState(false);
  const [result, setResult] = useState<ExperimentDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<DatasetSummary[]>("/datasets").then((res) => {
      setDatasets(res.data);
      if (res.data.length > 0) setDatasetId(res.data[0].id);
    });
  }, []);

  const handleTrain = async () => {
    if (datasetId === null) return;
    setTraining(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.post<ExperimentDetail>("/models/train", {
        dataset_id: datasetId,
        model_type: modelType,
        model_name: modelName || undefined,
        hyperparameters: {},
        preprocessing: config,
      });
      setResult(res.data);
      push(`Training complete — experiment #${res.data.id}`, "success");
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setTraining(false);
    }
  };

  if (datasets.length === 0) {
    return (
      <EmptyState
        title="No datasets available"
        description="Upload or load a dataset in Dataset Explorer first, and pick a target column, before training a model."
      />
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-100">Model Training</h2>
        <p className="text-sm text-slate-500">
          Preprocessing is fit only on the training split and reused consistently at evaluation and prediction time.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <div className="space-y-4 panel">
          <Field label="Dataset">
            <select className="select" value={datasetId ?? ""} onChange={(e) => setDatasetId(Number(e.target.value))}>
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.original_filename}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Model">
            <select className="select" value={modelType} onChange={(e) => setModelType(e.target.value)}>
              {MODEL_TYPES.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Model name (optional)">
            <input
              className="select"
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              placeholder={`${modelType}-run`}
            />
          </Field>

          <Field label="Task type">
            <select
              className="select"
              value={config.task_type}
              onChange={(e) => setConfig({ ...config, task_type: e.target.value as any })}
            >
              <option value="binary">Binary (Benign vs Malicious)</option>
              <option value="multiclass">Multiclass</option>
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
            onClick={handleTrain}
            disabled={training}
            className="w-full btn-primary"
          >
            {training ? "Training…" : "Train model"}
          </button>
        </div>

        <div className="space-y-4">
          {error && <ErrorState message={error} />}
          {training && <LoadingState label="Preprocessing, training, and evaluating…" />}
          {!training && !result && !error && (
            <EmptyState title="No experiment run yet" description="Configure the model and click Train model." />
          )}
          {result?.metrics && (
            <>
              <div className="panel text-sm text-slate-300">
                Experiment #{result.id} · {result.model_type} · {result.duration_seconds?.toFixed(2)}s
              </div>
              <MetricsView metrics={result.metrics} />
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
