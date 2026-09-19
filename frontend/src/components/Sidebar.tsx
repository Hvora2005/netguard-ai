import {
  Activity,
  AlertTriangle,
  Beaker,
  FileSearch,
  FileText,
  FlaskConical,
  LayoutDashboard,
  type LucideIcon,
  Network,
  Radar,
  Settings,
  ShieldHalf,
  SlidersHorizontal,
  Table2,
} from "lucide-react";
import { NavLink } from "react-router-dom";

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    label: "Overview",
    items: [{ to: "/", label: "Dashboard", icon: LayoutDashboard }],
  },
  {
    label: "Data & models",
    items: [
      { to: "/datasets", label: "Dataset Explorer", icon: Table2 },
      { to: "/preprocessing", label: "Preprocessing", icon: SlidersHorizontal },
      { to: "/training", label: "Model Training", icon: FlaskConical },
      { to: "/comparison", label: "Model Comparison", icon: Beaker },
      { to: "/experiments", label: "Experiments", icon: FlaskConical },
    ],
  },
  {
    label: "Inference",
    items: [
      { to: "/predict", label: "Live Prediction", icon: Activity },
      { to: "/explainability", label: "Explainability", icon: FileSearch },
    ],
  },
  {
    label: "Traffic & security",
    items: [
      { to: "/pcap", label: "PCAP Analyzer", icon: Network },
      { to: "/traffic", label: "Traffic Explorer", icon: Radar },
      { to: "/alerts", label: "Security Alerts", icon: AlertTriangle },
    ],
  },
  {
    label: "Output",
    items: [
      { to: "/reports", label: "Reports", icon: FileText },
      { to: "/settings", label: "Settings", icon: Settings },
    ],
  },
];

export default function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-slate-800/70 bg-[#060a13] md:flex">
      <div className="flex items-center gap-2.5 border-b border-slate-800/70 px-5 py-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-signal-500/10 ring-1 ring-inset ring-signal-500/30">
          <ShieldHalf className="text-signal-400" size={17} />
        </div>
        <div>
          <p className="text-sm font-semibold tracking-tight text-slate-100">NetGuard AI</p>
          <p className="text-[11px] text-slate-500">Threat detection platform</p>
        </div>
      </div>
      <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-5">
        {NAV_GROUPS.map((group) => (
          <div key={group.label}>
            <p className="mb-1.5 px-3 text-[10px] font-semibold uppercase tracking-wider text-slate-600">{group.label}</p>
            <div className="space-y-0.5">
              {group.items.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === "/"}
                  className={({ isActive }) =>
                    `nav-link ${
                      isActive
                        ? "bg-signal-500/10 text-signal-300"
                        : "text-slate-400 hover:bg-slate-900 hover:text-slate-100"
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      {isActive && <span className="absolute left-0 top-1/2 h-4 w-0.5 -translate-y-1/2 rounded-full bg-signal-400" />}
                      <Icon size={16} strokeWidth={2} />
                      {label}
                    </>
                  )}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>
    </aside>
  );
}
