import { EmptyState } from "../components/States";

export default function ComingSoon({ title, phase }: { title: string; phase: string }) {
  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-slate-100">{title}</h2>
      <EmptyState
        title="Not built yet"
        description={`${title} is planned for ${phase} of the roadmap and isn't implemented yet. Nothing shown here is simulated — this page is intentionally empty until the real feature lands.`}
      />
    </div>
  );
}
