import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { api, extractErrorMessage } from "../services/api";
import type { TrafficFlowPage } from "../types";
import { SEVERITY_TEXT } from "../utils/severity";

export default function TrafficExplorer() {
  const navigate = useNavigate();
  const [data, setData] = useState<TrafficFlowPage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({ protocol: "", severity: "", src_ip: "", dst_ip: "" });
  const [page, setPage] = useState(1);

  useEffect(() => {
    setData(null);
    const params: Record<string, string | number> = { page, page_size: 20 };
    Object.entries(filters).forEach(([k, v]) => {
      if (v) params[k] = v;
    });
    api
      .get<TrafficFlowPage>("/traffic", { params })
      .then((res) => setData(res.data))
      .catch((err) => setError(extractErrorMessage(err)));
  }, [filters, page]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-100">Traffic Explorer</h2>
        <p className="text-sm text-slate-500">Classified flows from uploaded PCAP captures. Click a row to investigate it.</p>
      </div>

      <div className="flex flex-wrap gap-3 panel">
        <input
          className="select w-40"
          placeholder="Protocol (TCP/UDP)"
          value={filters.protocol}
          onChange={(e) => {
            setPage(1);
            setFilters({ ...filters, protocol: e.target.value });
          }}
        />
        <select
          className="select w-40"
          value={filters.severity}
          onChange={(e) => {
            setPage(1);
            setFilters({ ...filters, severity: e.target.value });
          }}
        >
          <option value="">Any severity</option>
          <option value="none">None</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
        <input
          className="select w-40"
          placeholder="Source IP"
          value={filters.src_ip}
          onChange={(e) => {
            setPage(1);
            setFilters({ ...filters, src_ip: e.target.value });
          }}
        />
        <input
          className="select w-40"
          placeholder="Destination IP"
          value={filters.dst_ip}
          onChange={(e) => {
            setPage(1);
            setFilters({ ...filters, dst_ip: e.target.value });
          }}
        />
      </div>

      {error && <ErrorState message={error} />}
      {!data && !error && <LoadingState />}
      {data && data.items.length === 0 && (
        <EmptyState title="No traffic flows yet" description="Upload a PCAP file in PCAP Analyzer to populate this view." />
      )}

      {data && data.items.length > 0 && (
        <>
          <div className="overflow-x-auto panel-table">
            <table className="min-w-full text-left text-xs">
              <thead className="bg-slate-900/60 text-slate-500">
                <tr>
                  <th className="px-3 py-2">Source</th>
                  <th className="px-3 py-2">Destination</th>
                  <th className="px-3 py-2">Protocol</th>
                  <th className="px-3 py-2">Packets</th>
                  <th className="px-3 py-2">Bytes</th>
                  <th className="px-3 py-2">Prediction</th>
                  <th className="px-3 py-2">Confidence</th>
                  <th className="px-3 py-2">Severity</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((flow) => (
                  <tr
                    key={flow.id}
                    onClick={() => navigate(`/traffic/${flow.id}`)}
                    className="table-row-hover cursor-pointer border-t border-slate-800/70 text-slate-300"
                  >
                    <td className="px-3 py-2">
                      {flow.src_ip}
                      {flow.src_port ? `:${flow.src_port}` : ""}
                    </td>
                    <td className="px-3 py-2">
                      {flow.dst_ip}
                      {flow.dst_port ? `:${flow.dst_port}` : ""}
                    </td>
                    <td className="px-3 py-2">{flow.protocol}</td>
                    <td className="px-3 py-2">{flow.packet_count}</td>
                    <td className="px-3 py-2">{flow.byte_count}</td>
                    <td className="px-3 py-2">{flow.predicted_class ?? "—"}</td>
                    <td className="px-3 py-2">{flow.confidence !== null ? `${(flow.confidence * 100).toFixed(0)}%` : "—"}</td>
                    <td className={`px-3 py-2 font-medium capitalize ${SEVERITY_TEXT[flow.severity] ?? ""}`}>{flow.severity}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>
              Page {data.page} · {data.total} total flows
            </span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="btn-ghost px-3 py-1 text-xs disabled:opacity-40"
              >
                Previous
              </button>
              <button
                disabled={page * data.page_size >= data.total}
                onClick={() => setPage((p) => p + 1)}
                className="btn-ghost px-3 py-1 text-xs disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
