import { useEffect, useState } from "react";
import { api, formatINR, RecoveryCase } from "../api/client";
import Badge from "../components/Badge";

export default function Transactions() {
  const [cases, setCases] = useState<RecoveryCase[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.cases().then(setCases).catch((e) => setError(e.message));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white">Recovery Cases</h1>
        <p className="text-sm text-slate-500 mt-1">Every failed payment ReviveAI has analyzed.</p>
      </div>

      {error && <div className="text-red-400 text-sm">{error}</div>}

      <div className="rounded-xl border border-slate-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-900/70 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-3">Case</th>
              <th className="text-left px-4 py-3">Amount</th>
              <th className="text-left px-4 py-3">Recovery Prob.</th>
              <th className="text-left px-4 py-3">Risk</th>
              <th className="text-left px-4 py-3">Action</th>
              <th className="text-left px-4 py-3">Status</th>
              <th className="text-left px-4 py-3">Demo</th>
            </tr>
          </thead>
          <tbody>
            {cases.map((c) => (
              <tr key={c.id} className="border-t border-slate-800 hover:bg-slate-900/40">
                <td className="px-4 py-3 font-mono text-xs text-slate-400">{c.id.slice(0, 8)}</td>
                <td className="px-4 py-3">{formatINR(c.amount_at_risk)}</td>
                <td className="px-4 py-3">
                  {c.recovery_probability != null ? `${(c.recovery_probability * 100).toFixed(0)}%` : "—"}
                </td>
                <td className="px-4 py-3">{c.risk_level && <Badge label={c.risk_level} />}</td>
                <td className="px-4 py-3 text-slate-300">{c.approved_action ?? "—"}</td>
                <td className="px-4 py-3"><Badge label={c.status} /></td>
                <td className="px-4 py-3">{c.is_demo ? <span className="text-xs text-slate-500">DEMO</span> : ""}</td>
              </tr>
            ))}
            {cases.length === 0 && !error && (
              <tr><td className="px-4 py-6 text-slate-500 text-center" colSpan={7}>No recovery cases yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
