import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { api, formatINR, DashboardOverview } from "../api/client";
import StatCard from "../components/StatCard";

export default function Dashboard() {
  const [data, setData] = useState<DashboardOverview | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.overview().then(setData).catch((e) => setError(e.message));
  }, []);

  if (error) {
    return <div className="text-red-400 text-sm">Couldn't load dashboard: {error}</div>;
  }
  if (!data) {
    return <div className="text-slate-500 text-sm">Loading…</div>;
  }

  const chartData = [
    { name: "At Risk", amount: data.revenue_at_risk / 100 },
    { name: "Recovered", amount: data.revenue_recovered / 100 },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold text-white">Revenue Recovery Overview</h1>
        <p className="text-sm text-slate-500 mt-1">Live view of ReviveAI's agentic recovery pipeline.</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Revenue at Risk" value={formatINR(data.revenue_at_risk)} accent="risk" />
        <StatCard label="Revenue Recovered" value={formatINR(data.revenue_recovered)} accent="recovered" />
        <StatCard label="Recovery Rate" value={`${data.recovery_rate.toFixed(1)}%`} />
        <StatCard label="Active Recovery Cases" value={String(data.active_recovery_cases)} accent="pending" />
        <StatCard label="Failed Payments" value={String(data.failed_payments)} />
        <StatCard label="Agent Actions" value={String(data.agent_actions_count)} />
        <StatCard label="Agent Success Rate" value={`${data.agent_success_rate.toFixed(1)}%`} />
        <StatCard
          label="Avg Recovery Time"
          value={data.average_recovery_time_seconds ? `${Math.round(data.average_recovery_time_seconds)}s` : "—"}
        />
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
        <div className="text-sm font-medium text-slate-300 mb-3">Revenue at Risk vs Recovered</div>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chartData}>
            <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
            <YAxis stroke="#64748b" fontSize={12} />
            <Tooltip
              formatter={(v: number) => `₹${v.toLocaleString("en-IN")}`}
              contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 8 }}
            />
            <Bar dataKey="amount" fill="#6366f1" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
