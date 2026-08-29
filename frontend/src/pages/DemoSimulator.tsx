import { useState } from "react";
import { api, formatINR } from "../api/client";
import Badge from "../components/Badge";

const SCENARIOS = [
  { id: "TEMPORARY_FAILURE", label: "Temporary Failure", desc: "₹999 · returning customer · transient error" },
  { id: "CHECKOUT_ABANDONMENT", label: "Checkout Abandonment", desc: "₹4,999 · abandoned 2 min ago" },
  { id: "REPEATED_FAILURE", label: "Repeated Payment Failure", desc: "₹2,499 · multiple prior failures" },
  { id: "HIGH_VALUE_RISKY", label: "High-Value Risky Transaction", desc: "₹75,000 · suspicious pattern" },
];

export default function DemoSimulator() {
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run(scenario: string) {
    setLoadingId(scenario);
    setError(null);
    setResult(null);
    try {
      const res = await api.simulate(scenario);
      setResult(res);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoadingId(null);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white">Demo Simulator</h1>
        <p className="text-sm text-slate-500 mt-1">
          Runs the real ReviveAI pipeline end-to-end: ML prediction → AI agent → policy engine → action → result.
          Results shown here are clearly labeled DEMO / simulated.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {SCENARIOS.map((s) => (
          <button
            key={s.id}
            onClick={() => run(s.id)}
            disabled={loadingId !== null}
            className="text-left rounded-xl border border-slate-800 bg-slate-900/50 p-4 hover:border-brand-600 transition-colors disabled:opacity-50"
          >
            <div className="font-medium text-slate-100">{s.label}</div>
            <div className="text-xs text-slate-500 mt-1">{s.desc}</div>
            <div className="mt-3 text-xs text-brand-500">
              {loadingId === s.id ? "Running pipeline…" : "Simulate Failed Payment →"}
            </div>
          </button>
        ))}
      </div>

      {error && <div className="text-red-400 text-sm">{error}</div>}

      {result && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-3">
          <div className="flex items-center gap-2">
            <span className="text-xs px-2 py-0.5 rounded-md bg-brand-600/20 text-brand-500 font-medium">DEMO</span>
            <span className="text-sm text-slate-400">Scenario: {result.scenario}</span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div><div className="text-slate-500 text-xs">Recovery probability</div>{(result.recovery_probability * 100).toFixed(0)}%</div>
            <div><div className="text-slate-500 text-xs">Risk</div><Badge label={result.risk_level} /></div>
            <div><div className="text-slate-500 text-xs">Approved action</div>{result.approved_action}</div>
            <div><div className="text-slate-500 text-xs">Policy result</div><Badge label={result.policy_result} /></div>
          </div>
          <div className="text-sm text-slate-300">{result.reasoning}</div>
          <div className="text-xs text-slate-500">{result.policy_notes}</div>
          <div className="pt-2 border-t border-slate-800 flex items-center gap-4">
            <div className="text-sm text-slate-400">Status: <Badge label={result.status} /></div>
            <div className="text-sm text-slate-100 font-medium">
              Recovered: {formatINR(result.amount_recovered)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
