import { useEffect, useState } from "react";

import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { useToast } from "../hooks/useToast";
import { api, extractErrorMessage } from "../services/api";
import type { DatasetDetail, DatasetPreview, DatasetSummary } from "../types";

export default function DatasetExplorer() {
  const { push } = useToast();
  const [datasets, setDatasets] = useState<DatasetSummary[] | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<DatasetDetail | null>(null);
  const [preview, setPreview] = useState<DatasetPreview | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshList = () => {
    api
      .get<DatasetSummary[]>("/datasets")
      .then((res) => {
        setDatasets(res.data);
        if (!selectedId && res.data.length > 0) setSelectedId(res.data[0].id);
      })
      .catch((err) => setError(extractErrorMessage(err)));
  };

  useEffect(refreshList, []);

  useEffect(() => {
    if (selectedId === null) return;
    setDetail(null);
    setPreview(null);
    api.get<DatasetDetail>(`/datasets/${selectedId}`).then((res) => setDetail(res.data));
    api.get<DatasetPreview>(`/datasets/${selectedId}/preview`).then((res) => setPreview(res.data));
  }, [selectedId]);

  const handleUpload = async (file: File) => {
    setUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await api.post<DatasetDetail>("/datasets/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      push(`Uploaded ${res.data.original_filename}`, "success");
      refreshList();
      setSelectedId(res.data.id);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setUploading(false);
    }
  };

  const handleLoadDemo = async () => {
    setUploading(true);
    setError(null);
    try {
      const res = await api.post<DatasetDetail>("/datasets/demo");
      push("Demo dataset loaded", "success");
      refreshList();
      setSelectedId(res.data.id);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setUploading(false);
    }
  };

  const handleSetTarget = async (column: string) => {
    if (selectedId === null) return;
    try {
      const res = await api.put<DatasetDetail>(`/datasets/${selectedId}/target-column`, { target_column: column });
      setDetail(res.data);
      push(`Target column set to ${column}`, "success");
    } catch (err) {
      push(extractErrorMessage(err), "error");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-100">Dataset Explorer</h2>
          <p className="text-sm text-slate-500">Upload CIC-IDS-style CSV traffic captures or load the synthetic demo set.</p>
        </div>
        <div className="flex gap-2">
          <label className="cursor-pointer btn-primary">
            {uploading ? "Uploading…" : "Upload CSV"}
            <input
              type="file"
              accept=".csv"
              className="hidden"
              disabled={uploading}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleUpload(file);
                e.target.value = "";
              }}
            />
          </label>
          <button
            onClick={handleLoadDemo}
            disabled={uploading}
            className="btn-ghost"
          >
            Load demo (synthetic)
          </button>
        </div>
      </div>

      {error && <ErrorState message={error} />}

      {datasets === null ? (
        <LoadingState />
      ) : datasets.length === 0 ? (
        <EmptyState
          title="No datasets yet"
          description="Upload a CSV network-traffic dataset, or load the synthetic demo dataset to try the platform immediately."
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
          <div className="space-y-2">
            {datasets.map((d) => (
              <button
                key={d.id}
                onClick={() => setSelectedId(d.id)}
                className={`w-full rounded-md border px-3 py-2 text-left text-sm ${
                  selectedId === d.id
                    ? "border-signal-600 bg-signal-500/10 text-signal-300"
                    : "border-slate-800 bg-slate-900/40 text-slate-300 hover:bg-slate-900"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="truncate">{d.original_filename}</span>
                  {d.is_demo && <span className="ml-2 shrink-0 rounded bg-amber-500/10 px-1.5 py-0.5 text-[10px] text-amber-400">DEMO</span>}
                </div>
                <div className="text-xs text-slate-500">{d.n_rows.toLocaleString()} rows · {d.n_columns} cols</div>
              </button>
            ))}
          </div>

          <div className="space-y-4">
            {!detail ? (
              <LoadingState label="Loading dataset details…" />
            ) : (
              <>
                <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                  <Stat label="Rows" value={detail.n_rows.toLocaleString()} />
                  <Stat label="Columns" value={detail.n_columns} />
                  <Stat label="Size" value={`${(detail.size_bytes / 1024).toFixed(1)} KB`} />
                  <Stat label="Duplicate rows" value={detail.duplicate_rows} />
                </div>

                <div className="panel">
                  <h3 className="mb-2 text-sm font-medium text-slate-300">Target column</h3>
                  <div className="flex flex-wrap gap-2">
                    {detail.columns_meta?.map((c) => (
                      <button
                        key={c.name}
                        onClick={() => handleSetTarget(c.name)}
                        className={`rounded border px-2 py-1 text-xs ${
                          detail.target_column === c.name
                            ? "border-signal-600 bg-signal-500/10 text-signal-300"
                            : "border-slate-700 text-slate-400 hover:bg-slate-800"
                        }`}
                      >
                        {c.name}
                      </button>
                    ))}
                  </div>
                  {!detail.target_column && (
                    <p className="mt-2 text-xs text-amber-400">
                      No target column selected — pick one above before running preprocessing or training.
                    </p>
                  )}
                </div>

                {detail.class_distribution && (
                  <div className="panel">
                    <h3 className="mb-2 text-sm font-medium text-slate-300">Class distribution ({detail.target_column})</h3>
                    <div className="space-y-1">
                      {Object.entries(detail.class_distribution).map(([label, count]) => (
                        <div key={label} className="flex items-center gap-2 text-xs">
                          <span className="w-32 truncate text-slate-400">{label}</span>
                          <div className="h-1.5 flex-1 rounded-full bg-slate-800/70">
                            <div
                              className="h-1.5 rounded-full bg-signal-500"
                              style={{ width: `${(count / detail.n_rows) * 100}%` }}
                            />
                          </div>
                          <span className="w-16 text-right text-slate-500">{count.toLocaleString()}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {preview && (
                  <div className="overflow-x-auto panel">
                    <h3 className="mb-2 text-sm font-medium text-slate-300">Data preview (first {preview.rows.length} rows)</h3>
                    <table className="min-w-full text-left text-xs">
                      <thead>
                        <tr>
                          {preview.columns.map((c) => (
                            <th key={c} className="whitespace-nowrap px-2 py-1 font-medium text-slate-400">
                              {c}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {preview.rows.slice(0, 10).map((row, idx) => (
                          <tr key={idx} className="border-t border-slate-800">
                            {preview.columns.map((c) => (
                              <td key={c} className="whitespace-nowrap px-2 py-1 text-slate-300">
                                {String(row[c] ?? "")}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
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
