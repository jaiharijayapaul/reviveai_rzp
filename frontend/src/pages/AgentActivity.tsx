import { useEffect, useState } from "react";
import { api, AgentActivityItem } from "../api/client";
import Badge from "../components/Badge";

export default function AgentActivity() {
  const [items, setItems] = useState<AgentActivityItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.activity().then(setItems).catch((e) => setError(e.message));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white">AI Recovery Agent</h1>
        <p className="text-sm text-slate-500 mt-1">
          Every recommendation is validated by a deterministic policy engine before anything executes.
        </p>
      </div>

      {error && <div className="text-red-400 text-sm">{error}</div>}

      <div className="space-y-3">
        {items.map((a) => (
          <div key={a.id} className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-medium text-slate-100">{a.action_type}</span>
                {a.confidence != null && (
                  <span className="text-xs text-slate-500">confidence {(a.confidence * 100).toFixed(0)}%</span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Badge label={a.policy_result} />
                <Badge label={a.execution_status} />
              </div>
            </div>
            {a.reasoning && <p className="mt-2 text-sm text-slate-400">{a.reasoning}</p>}
            <div className="mt-2 text-xs text-slate-600">{new Date(a.created_at).toLocaleString()}</div>
          </div>
        ))}
        {items.length === 0 && !error && (
          <div className="text-slate-500 text-sm">No agent actions yet — run a demo scenario to see the agent in action.</div>
        )}
      </div>
    </div>
  );
}
