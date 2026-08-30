import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid, AreaChart, Area } from "recharts";
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
    return (
      <div className="space-y-8 animate-pulse">
        <div>
          <div className="h-6 w-64 bg-slate-800 rounded-md mb-2"></div>
          <div className="h-4 w-96 bg-slate-800 rounded-md"></div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-24 bg-slate-800 rounded-xl"></div>
          ))}
        </div>
      </div>
    );
  }

  const barData = [
    { name: "At Risk", amount: data.revenue_at_risk / 100, fill: "url(#riskGradient)" },
    { name: "Recovered", amount: data.revenue_recovered / 100, fill: "url(#recoveredGradient)" },
  ];

  // Mock historical data for the LineChart
  const lineData = [
    { day: "Mon", rate: Math.max(0, data.recovery_rate - 15) },
    { day: "Tue", rate: Math.max(0, data.recovery_rate - 5) },
    { day: "Wed", rate: Math.max(0, data.recovery_rate - 10) },
    { day: "Thu", rate: Math.max(0, data.recovery_rate + 5) },
    { day: "Fri", rate: Math.max(0, data.recovery_rate - 2) },
    { day: "Sat", rate: Math.max(0, data.recovery_rate + 8) },
    { day: "Sun", rate: data.recovery_rate },
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
        <div className="rounded-xl border border-brand-500/30 bg-brand-900/10 p-5 shadow-[0_0_15px_rgba(16,185,129,0.15)] relative overflow-hidden">
          <div className="absolute -right-4 -top-4 w-24 h-24 bg-brand-500/20 rounded-full blur-2xl"></div>
          <div className="text-sm font-medium text-brand-400 mb-1">ROI Impact (Net Lift)</div>
          <div className="text-2xl font-bold text-slate-50 tracking-tight">
            +{formatINR(data.revenue_recovered)}
          </div>
          <div className="text-xs text-brand-500/70 mt-2 font-medium">Powered by Dynamic Offers</div>
        </div>
        <StatCard label="Recovery Rate" value={`${data.recovery_rate.toFixed(1)}%`} />
        
        <div className="rounded-xl border border-red-500/30 bg-red-900/10 p-5 shadow-[0_0_15px_rgba(239,68,68,0.15)] relative overflow-hidden">
          <div className="absolute -right-4 -top-4 w-24 h-24 bg-red-500/20 rounded-full blur-2xl"></div>
          <div className="text-sm font-medium text-red-400 mb-1">Fraud Prevented</div>
          <div className="text-2xl font-bold text-slate-50 tracking-tight">
            {formatINR(data.fraud_prevented)}
          </div>
          <div className="text-xs text-red-500/70 mt-2 font-medium">Risk Shield Active</div>
        </div>

        <StatCard label="Active Recovery Cases" value={String(data.active_recovery_cases)} accent="pending" />
        <StatCard label="Failed Payments" value={String(data.failed_payments)} />
        <StatCard label="Agent Actions" value={String(data.agent_actions_count)} />
        <StatCard label="Agent Success Rate" value={`${data.agent_success_rate.toFixed(1)}%`} />
        <StatCard
          label="Avg Recovery Time"
          value={data.average_recovery_time_seconds ? `${Math.round(data.average_recovery_time_seconds)}s` : "—"}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 shadow-sm">
          <div className="text-sm font-medium text-slate-300 mb-6">Revenue at Risk vs Recovered</div>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={barData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#f43f5e" stopOpacity={0.8}/>
                  <stop offset="100%" stopColor="#f43f5e" stopOpacity={0.3}/>
                </linearGradient>
                <linearGradient id="recoveredGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10b981" stopOpacity={0.8}/>
                  <stop offset="100%" stopColor="#10b981" stopOpacity={0.3}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
              <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} dy={10} />
              <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(v) => `₹${v/1000}k`} />
              <Tooltip
                cursor={{ fill: '#1e293b', opacity: 0.4 }}
                formatter={(v: number) => `₹${v.toLocaleString("en-IN")}`}
                contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 8, color: '#f8fafc' }}
                itemStyle={{ color: '#e2e8f0' }}
              />
              <Bar dataKey="amount" radius={[6, 6, 0, 0]} barSize={40} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 shadow-sm">
          <div className="text-sm font-medium text-slate-300 mb-6">Recovery Rate Trend</div>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={lineData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="rateGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
              <XAxis dataKey="day" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} dy={10} />
              <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(v) => `${v}%`} />
              <Tooltip
                contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 8, color: '#f8fafc' }}
                itemStyle={{ color: '#6366f1' }}
                formatter={(v: number) => `${v.toFixed(1)}%`}
              />
              <Area type="monotone" dataKey="rate" stroke="#6366f1" strokeWidth={3} fillOpacity={1} fill="url(#rateGradient)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
