import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ErrorState, LoadingState } from "../components/States";
import { api, extractErrorMessage } from "../services/api";
import type { TrafficFlowDetail } from "../types";
import { SEVERITY_TEXT } from "../utils/severity";

export default function FlowInvestigation() {
  const { id } = useParams();
  const [flow, setFlow] = useState<TrafficFlowDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<TrafficFlowDetail>(`/traffic/${id}`)
      .then((res) => setFlow(res.data))
      .catch((err) => setError(extractErrorMessage(err)));
  }, [id]);

  if (error) return <ErrorState message={error} />;
  if (!flow) return <LoadingState />;

  const max = flow.explanation?.length ? Math.max(...flow.explanation.map((e) => Math.abs(e.contribution))) : 1;

  return (
    <div className="space-y-6">
      <div>
        <Link to="/traffic" className="text-xs text-slate-500 transition-colors hover:text-signal-400">
          ← Back to Traffic Explorer
        </Link>
        <h2 className="stat-value mt-2 text-xl font-semibold text-slate-100">
          Flow #{flow.id}: {flow.src_ip} → {flow.dst_ip}
        </h2>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Section title="Network information">
          <Row label="Source" value={`${flow.src_ip}${flow.src_port ? ":" + flow.src_port : ""}`} />
          <Row label="Destination" value={`${flow.dst_ip}${flow.dst_port ? ":" + flow.dst_port : ""}`} />
          <Row label="Protocol" value={flow.protocol} />
          <Row label="Captured from" value={flow.source_name} />
        </Section>

        <Section title="Statistics">
          <Row label="Duration" value={`${flow.duration_seconds.toFixed(4)}s`} />
          <Row label="Packets" value={flow.packet_count} />
          <Row label="Bytes" value={flow.byte_count} />
          <Row label="Packet rate" value={`${flow.packet_rate.toFixed(1)}/s`} />
          <Row label="Byte rate" value={`${flow.byte_rate.toFixed(1)}/s`} />
        </Section>

        <Section title="Classification">
          <Row label="Predicted class" value={flow.predicted_class ?? "—"} />
          <Row label="Confidence" value={flow.confidence !== null ? `${(flow.confidence * 100).toFixed(1)}%` : "—"} />
          <div className="flex justify-between py-0.5 text-xs">
            <span className="text-slate-500">Severity</span>
            <span className={`font-medium capitalize ${SEVERITY_TEXT[flow.severity] ?? "text-slate-300"}`}>{flow.severity}</span>
          </div>
          <p className="mt-3 border-t border-slate-800/70 pt-3 text-xs leading-relaxed text-slate-500">
            This reflects traffic matching a learned pattern for "{flow.predicted_class}", not a confirmed real-world attack.
          </p>
        </Section>

        <Section title="Explainability">
          {!flow.explanation ? (
            <p className="text-xs text-slate-500">No model was associated with this flow, or explanation is unavailable.</p>
          ) : (
            <>
              <p className="mb-2 text-[11px] text-slate-500">Method: {flow.explanation_method}</p>
              <div className="space-y-1">
                {flow.explanation.map((item) => (
                  <div key={item.feature} className="flex items-center gap-2 text-xs">
                    <span className="stat-value w-40 truncate text-slate-400">{item.feature.replace(/^(numeric|categorical)__/, "")}</span>
                    <div className="h-1.5 flex-1 rounded-full bg-slate-800/70">
                      <div
                        className={`h-1.5 rounded-full ${item.contribution >= 0 ? "bg-signal-500" : "bg-red-500"}`}
                        style={{ width: `${(Math.abs(item.contribution) / max) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </Section>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="panel">
      <h3 className="label-xs mb-3">{title}</h3>
      {children}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex justify-between py-0.5 text-xs">
      <span className="text-slate-500">{label}</span>
      <span className="stat-value text-slate-200">{value}</span>
    </div>
  );
}
