import { CheckCircle2, AlertTriangle, XCircle } from "lucide-react";

const CONFIG = {
  good: {
    Icon: CheckCircle2,
    label: "Good Retrieval",
    classes: "bg-neon-emerald/10 text-neon-emerald border-neon-emerald/25",
    glow: "neon-glow-emerald",
  },
  partial: {
    Icon: AlertTriangle,
    label: "Partial Match",
    classes: "bg-neon-amber/10 text-neon-amber border-neon-amber/25",
    glow: "neon-glow-amber",
  },
  bad: {
    Icon: XCircle,
    label: "Poor Retrieval",
    classes: "bg-neon-rose/10 text-neon-rose border-neon-rose/25",
    glow: "neon-glow-rose",
  },
};

export default function GradeBadge({ quality }) {
  const cfg = CONFIG[quality] || CONFIG.bad;
  const { Icon, label, classes, glow } = cfg;

  return (
    <div
      className={`
        inline-flex items-center gap-2 px-4 py-2 rounded-xl border
        text-sm font-medium transition-all duration-300
        ${classes} ${glow}
        animate-slide-up
      `}
    >
      <Icon className="w-4 h-4" />
      <span>{label}</span>
    </div>
  );
}
