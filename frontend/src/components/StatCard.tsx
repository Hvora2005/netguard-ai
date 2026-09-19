interface StatCardProps {
  label: string;
  value: string | number;
  hint?: string;
}

export default function StatCard({ label, value, hint }: StatCardProps) {
  return (
    <div className="panel group transition-all duration-200 hover:-translate-y-0.5 hover:border-slate-700 hover:shadow-panel-hover">
      <p className="label-xs">{label}</p>
      <p className="stat-value mt-2 text-2xl font-semibold tracking-tight text-slate-100">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}
