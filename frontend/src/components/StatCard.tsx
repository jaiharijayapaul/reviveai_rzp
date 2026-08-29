interface Props {
  label: string;
  value: string;
  accent?: "risk" | "recovered" | "pending" | "default";
  sub?: string;
}

const accentClass: Record<string, string> = {
  risk: "text-risk",
  recovered: "text-recovered",
  pending: "text-pending",
  default: "text-slate-100",
};

export default function StatCard({ label, value, accent = "default", sub }: Props) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-1.5 text-2xl font-semibold ${accentClass[accent]}`}>{value}</div>
      {sub && <div className="mt-1 text-xs text-slate-500">{sub}</div>}
    </div>
  );
}
