import { useEffect, useState } from "react";

import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { useToast } from "../hooks/useToast";
import { api, extractErrorMessage } from "../services/api";
import type { SecurityAlertPage } from "../types";
import { SEVERITY_BADGE } from "../utils/severity";

export default function SecurityAlerts() {
  const { push } = useToast();
  const [data, setData] = useState<SecurityAlertPage | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    const params: Record<string, string> = {};
    if (statusFilter) params.status = statusFilter;
    api
      .get<SecurityAlertPage>("/alerts", { params })
      .then((res) => setData(res.data))
      .catch((err) => setError(extractErrorMessage(err)));
  };

  useEffect(load, [statusFilter]);

  const updateStatus = async (id: number, status: string) => {
    try {
      await api.put(`/alerts/${id}/status`, { status });
      push(`Alert #${id} marked ${status}`, "success");
      load();
    } catch (err) {
      push(extractErrorMessage(err), "error");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-100">Security Alerts</h2>
          <p className="text-sm text-slate-500">
            Generated from model predictions on classified traffic — describes learned-pattern matches, not confirmed attacks.
          </p>
        </div>
        <select className="select w-40" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">Any status</option>
          <option value="open">Open</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="resolved">Resolved</option>
        </select>
      </div>

      {error && <ErrorState message={error} />}
      {!data && !error && <LoadingState />}
      {data && data.items.length === 0 && (
        <EmptyState title="No alerts" description="Alerts are created automatically when PCAP analysis classifies traffic as non-benign." />
      )}

      {data && data.items.length > 0 && (
        <div className="overflow-x-auto panel-table">
          <table className="min-w-full text-left text-xs">
            <thead className="bg-slate-900/60 text-slate-500">
              <tr>
                <th className="px-3 py-2">Severity</th>
                <th className="px-3 py-2">Classification</th>
                <th className="px-3 py-2">Source</th>
                <th className="px-3 py-2">Destination</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((alert) => (
                <tr key={alert.id} className="table-row-hover border-t border-slate-800/70 text-slate-300">
                  <td className="px-3 py-2">
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-[11px] font-medium capitalize ${
                        SEVERITY_BADGE[alert.severity] ?? "border-slate-700 text-slate-400"
                      }`}
                    >
                      {alert.severity}
                    </span>
                  </td>
                  <td className="px-3 py-2 font-medium text-slate-200">{alert.classification}</td>
                  <td className="stat-value px-3 py-2 text-slate-400">{alert.source}</td>
                  <td className="stat-value px-3 py-2 text-slate-400">{alert.destination}</td>
                  <td className="px-3 py-2 capitalize text-slate-400">{alert.status}</td>
                  <td className="px-3 py-2">
                    <div className="flex gap-3 text-xs">
                      {alert.status !== "acknowledged" && (
                        <button onClick={() => updateStatus(alert.id, "acknowledged")} className="font-medium text-amber-400 transition-opacity hover:opacity-80">
                          Acknowledge
                        </button>
                      )}
                      {alert.status !== "resolved" && (
                        <button onClick={() => updateStatus(alert.id, "resolved")} className="font-medium text-signal-400 transition-opacity hover:opacity-80">
                          Resolve
                        </button>
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
