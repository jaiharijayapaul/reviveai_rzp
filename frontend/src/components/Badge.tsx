const colors: Record<string, string> = {
  LOW: "bg-emerald-500/15 text-emerald-400",
  MEDIUM: "bg-amber-500/15 text-amber-400",
  HIGH: "bg-red-500/15 text-red-400",
  APPROVED: "bg-emerald-500/15 text-emerald-400",
  BLOCKED: "bg-red-500/15 text-red-400",
  MODIFIED: "bg-amber-500/15 text-amber-400",
  SUCCESS: "bg-emerald-500/15 text-emerald-400 animate-pulse",
  FAILED: "bg-red-500/15 text-red-400",
  PENDING: "bg-slate-500/15 text-slate-400",
  IN_PROGRESS: "bg-brand-500/15 text-brand-400 animate-pulse",
};

export default function Badge({ label }: { label: string }) {
  const cls = colors[label] ?? "bg-slate-500/15 text-slate-400";
  return <span className={`px-2 py-0.5 rounded-md text-xs font-medium ${cls}`}>{label}</span>;
}
