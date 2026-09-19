import { useEffect, useState } from "react";

import StatCard from "../components/StatCard";
import { ErrorState, LoadingState } from "../components/States";
import { api, extractErrorMessage } from "../services/api";
import type { DatasetSummary, ExperimentSummary, SecurityAlertPage, TrafficFlowPage } from "../types";

export default function Dashboard() {
  const [datasets, setDatasets] = useState<DatasetSummary[] | null>(null);
  const [experiments, setExperiments] = useState<ExperimentSummary[] | null>(null);
  const [traffic, setTraffic] = useState<TrafficFlowPage | null>(null);
  const [alerts, setAlerts] = useState<SecurityAlertPage | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.get<DatasetSummary[]>("/datasets"),
      api.get<ExperimentSummary[]>("/experiments"),
      api.get<TrafficFlowPage>("/traffic", { params: { page_size: 200 } }),
      api.get<SecurityAlertPage>("/alerts", { params: { page_size: 10 } }),
    ])
      .then(([d, e, t, a]) => {
        setDatasets(d.data);
        setExperiments(e.data);
        setTraffic(t.data);
        setAlerts(a.data);
      })
      .catch((err) => setError(extractErrorMessage(err)));
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!datasets || !experiments || !traffic || !alerts) return <LoadingState label="Loading dashboard…" />;

  const completed = experiments.filter((e) => e.status === "completed");
  const totalRows = datasets.reduce((sum, d) => sum + d.n_rows, 0);

  const totalPackets = traffic.items.reduce((sum, f) => sum + f.packet_count, 0);
  const totalBytes = traffic.items.reduce((sum, f) => sum + f.byte_count, 0);
  const benignCount = traffic.items.filter((f) => (f.predicted_class ?? "").toLowerCase() === "benign").length;
  const maliciousCount = traffic.total - benignCount;

  const attackDistribution: Record<string, number> = {};
  const protocolDistribution: Record<string, number> = {};
  for (const flow of traffic.items) {
    const label = flow.predicted_class ?? "unclassified";
    attackDistribution[label] = (attackDistribution[label] ?? 0) + 1;
    protocolDistribution[flow.protocol] = (protocolDistribution[flow.protocol] ?? 0) + 1;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-100">Overview</h2>
        <p className="text-sm text-slate-500">
          Live counts from your local NetGuard AI instance — nothing here is simulated.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Total flows" value={traffic.total} />
        <StatCard label="Total packets (sampled)" value={totalPackets.toLocaleString()} />
        <StatCard label="Total bytes (sampled)" value={totalBytes.toLocaleString()} />
        <StatCard label="Active alerts" value={alerts.total} />
        <StatCard label="Benign flows" value={benignCount} />
        <StatCard label="Malicious flows" value={maliciousCount} />
        <StatCard label="Training experiments" value={experiments.length} />
        <StatCard label="Completed models" value={completed.length} />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Distribution title="Attack distribution (classified flows)" data={attackDistribution} />
        <Distribution title="Protocol distribution" data={protocolDistribution} />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="panel">
          <h3 className="mb-3 text-sm font-medium text-slate-300">Recent datasets</h3>
          {datasets.length === 0 ? (
            <p className="text-xs text-slate-500">
              No datasets uploaded yet. Head to Dataset Explorer to upload a CSV or load the demo dataset.
            </p>
          ) : (
            <ul className="space-y-2 text-sm">
              {datasets.slice(0, 5).map((d) => (
                <li key={d.id} className="flex items-center justify-between text-slate-300">
                  <span>
                    {d.original_filename}
                    {d.is_demo && <span className="ml-2 rounded bg-amber-500/10 px-1.5 py-0.5 text-[10px] text-amber-400">DEMO</span>}
                  </span>
                  <span className="text-xs text-slate-500">{d.n_rows.toLocaleString()} rows</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="panel">
          <h3 className="mb-3 text-sm font-medium text-slate-300">Recent alerts</h3>
          {alerts.items.length === 0 ? (
            <p className="text-xs text-slate-500">No alerts yet. Analyze a PCAP capture to generate some.</p>
          ) : (
            <ul className="space-y-2 text-sm">
              {alerts.items.slice(0, 5).map((a) => (
                <li key={a.id} className="flex items-center justify-between text-slate-300">
                  <span>
                    {a.classification} · {a.source} → {a.destination}
                  </span>
                  <span className="text-xs text-amber-400">{a.severity}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="panel">
        <h3 className="mb-3 text-sm font-medium text-slate-300">Recent experiments</h3>
        {experiments.length === 0 ? (
          <p className="text-xs text-slate-500">No models trained yet. Head to Model Training to run one.</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {experiments.slice(0, 5).map((e) => (
              <li key={e.id} className="flex items-center justify-between text-slate-300">
                <span>
                  #{e.id} · {e.model_type}
                </span>
                <span
                  className={`text-xs ${
                    e.status === "completed"
                      ? "text-signal-400"
                      : e.status === "failed"
                        ? "text-red-400"
                        : "text-amber-400"
                  }`}
                >
                  {e.status}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function Distribution({ title, data }: { title: string; data: Record<string, number> }) {
  const entries = Object.entries(data);
  const total = entries.reduce((sum, [, v]) => sum + v, 0) || 1;

  return (
    <div className="panel">
      <h3 className="mb-2 text-sm font-medium text-slate-300">{title}</h3>
      {entries.length === 0 ? (
        <p className="text-xs text-slate-500">No classified traffic yet — analyze a PCAP to populate this chart.</p>
      ) : (
        <div className="space-y-1">
          {entries.map(([label, count]) => (
            <div key={label} className="flex items-center gap-2 text-xs">
              <span className="w-24 truncate text-slate-400">{label}</span>
              <div className="h-1.5 flex-1 rounded-full bg-slate-800/70">
                <div className="h-1.5 rounded-full bg-signal-500" style={{ width: `${(count / total) * 100}%` }} />
              </div>
              <span className="w-10 text-right text-slate-500">{count}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
