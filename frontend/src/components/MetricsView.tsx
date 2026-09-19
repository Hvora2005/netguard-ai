import type { ExperimentMetrics } from "../types";

export default function MetricsView({ metrics }: { metrics: ExperimentMetrics }) {
  const maxCell = Math.max(...metrics.confusion_matrix.flat());

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat label="Accuracy" value={`${(metrics.accuracy * 100).toFixed(2)}%`} />
        <Stat label="Macro F1" value={metrics.macro_f1.toFixed(3)} />
        <Stat label="Weighted F1" value={metrics.weighted_f1.toFixed(3)} />
        <Stat label="ROC-AUC" value={metrics.roc_auc !== null ? metrics.roc_auc.toFixed(3) : "N/A"} />
      </div>

      <div className="overflow-x-auto panel">
        <h3 className="label-xs mb-3">Per-class metrics</h3>
        <table className="min-w-full text-left text-xs">
          <thead>
            <tr className="text-slate-500">
              <th className="px-2 py-1.5">Class</th>
              <th className="px-2 py-1.5">Precision</th>
              <th className="px-2 py-1.5">Recall</th>
              <th className="px-2 py-1.5">F1</th>
              <th className="px-2 py-1.5">Support</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(metrics.per_class).map(([label, m]) => (
              <tr key={label} className="table-row-hover border-t border-slate-800/70 text-slate-300">
                <td className="px-2 py-1.5 font-medium text-slate-200">{label}</td>
                <td className="stat-value px-2 py-1.5">{m.precision.toFixed(3)}</td>
                <td className="stat-value px-2 py-1.5">{m.recall.toFixed(3)}</td>
                <td className="stat-value px-2 py-1.5">{m.f1.toFixed(3)}</td>
                <td className="stat-value px-2 py-1.5 text-slate-500">{m.support}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="overflow-x-auto panel">
        <h3 className="label-xs mb-3">Confusion matrix</h3>
        <table className="text-center text-xs">
          <thead>
            <tr>
              <th className="px-2 py-1.5" />
              {metrics.class_labels.map((label) => (
                <th key={label} className="px-2 py-1.5 font-medium text-slate-500">
                  {label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {metrics.confusion_matrix.map((row, i) => (
              <tr key={i}>
                <td className="px-2 py-1.5 text-left font-medium text-slate-500">{metrics.class_labels[i]}</td>
                {row.map((value, j) => {
                  const intensity = maxCell > 0 ? value / maxCell : 0;
                  return (
                    <td
                      key={j}
                      className={`stat-value px-2 py-1.5 ${i === j ? "text-signal-200" : "text-slate-400"}`}
                      style={{
                        backgroundColor:
                          value === 0
                            ? "transparent"
                            : i === j
                              ? `rgba(63, 206, 160, ${0.08 + intensity * 0.32})`
                              : `rgba(248, 113, 113, ${0.05 + intensity * 0.25})`,
                      }}
                    >
                      {value}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="panel-tight">
      <p className="label-xs">{label}</p>
      <p className="stat-value mt-1 text-lg font-semibold text-slate-100">{value}</p>
    </div>
  );
}
