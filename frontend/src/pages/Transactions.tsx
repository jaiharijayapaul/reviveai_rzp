import { useEffect, useState } from "react";
import { api, formatINR, RecoveryCase, AgentActivityItem } from "../api/client";
import Badge from "../components/Badge";

function CaseDrawer({ 
  rcase, 
  onClose,
  activities
}: { 
  rcase: RecoveryCase | null, 
  onClose: () => void,
  activities: AgentActivityItem[] 
}) {
  if (!rcase) return null;
  const caseActivities = activities.filter((a) => a.recovery_case_id === rcase.id);

  return (
    <>
      <div 
        className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm z-40 transition-opacity"
        onClick={onClose}
      />
      <div className="fixed inset-y-0 right-0 w-full max-w-md bg-slate-900 border-l border-slate-800 shadow-2xl z-50 p-6 overflow-y-auto transform transition-transform duration-300 translate-x-0">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-semibold text-white">Agent Insights</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white">&times;</button>
        </div>
        
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-800 bg-slate-800/30 p-4">
            <div className="text-xs text-slate-500 mb-1">Recovery Case</div>
            <div className="font-mono text-sm text-slate-300">{rcase.id}</div>
            
            <div className="grid grid-cols-2 gap-4 mt-4">
              <div>
                <div className="text-xs text-slate-500">Amount at Risk</div>
                <div className="text-sm font-medium">{formatINR(rcase.amount_at_risk)}</div>
              </div>
              <div>
                <div className="text-xs text-slate-500">Status</div>
                <div className="mt-1"><Badge label={rcase.status} /></div>
              </div>
              <div className="col-span-2 mt-2">
                <div className="flex items-center justify-between bg-slate-900/50 rounded-lg p-3 border border-slate-700/50">
                  <span className="text-xs text-slate-400">Customer LTV Score</span>
                  {/* Mock LTV display: if demo VIP, score is 95, else ~50 */}
                  <span className={`text-sm font-medium ${rcase.amount_at_risk === 500000 ? 'text-brand-400' : 'text-slate-300'}`}>
                    {rcase.amount_at_risk === 500000 ? '95 (VIP)' : '55 (Avg)'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-medium text-slate-300 mb-4">AI Thought Process</h3>
            <div className="relative pl-4 border-l border-slate-800 space-y-6">
              {/* Fake initial node */}
              <div className="relative">
                <div className="absolute -left-[21px] top-1 h-2 w-2 rounded-full bg-brand-500 shadow-[0_0_8px_rgba(99,102,241,0.6)]"></div>
                <div className="text-xs text-brand-400 font-medium">Risk Assessment</div>
                <div className="text-sm text-slate-300 mt-1">
                  Determined risk level: {rcase.risk_level ?? "Unknown"} 
                  {rcase.recovery_probability != null && ` (${(rcase.recovery_probability * 100).toFixed(0)}% recovery prob)`}
                </div>
              </div>

              {/* Real activities */}
              {caseActivities.length === 0 ? (
                <div className="text-xs text-slate-500 italic">No agent actions recorded yet.</div>
              ) : (
                caseActivities.map((act) => (
                  <div key={act.id} className="relative">
                    <div className="absolute -left-[21px] top-1 h-2 w-2 rounded-full bg-emerald-500"></div>
                    <div className="text-xs text-emerald-400 font-medium flex items-center gap-2">
                      Action Recommended: {act.action_type}
                      {act.action_type === "DYNAMIC_OFFER" && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] uppercase font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30 animate-pulse">
                          Offer Applied
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-slate-300 mt-1">{act.reasoning}</div>
                    <div className="text-xs text-slate-500 mt-2 flex gap-2 items-center">
                      <span>Policy:</span>
                      <Badge label={act.policy_result} />
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default function Transactions() {
  const [cases, setCases] = useState<RecoveryCase[]>([]);
  const [activities, setActivities] = useState<AgentActivityItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedCase, setSelectedCase] = useState<RecoveryCase | null>(null);

  useEffect(() => {
    Promise.all([api.cases(), api.activity()])
      .then(([c, a]) => {
        setCases(c);
        setActivities(a);
      })
      .catch((e) => setError(e.message))
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white">Recovery Cases</h1>
        <p className="text-sm text-slate-500 mt-1">Every failed payment ReviveAI has analyzed.</p>
      </div>

      {error && <div className="text-red-400 text-sm">{error}</div>}

      <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-900/40">
        <table className="w-full text-sm">
          <thead className="bg-slate-900/70 text-slate-500 text-xs uppercase">
            <tr>
              <th className="text-left px-4 py-3 font-medium">Case</th>
              <th className="text-left px-4 py-3 font-medium">Amount</th>
              <th className="text-left px-4 py-3 font-medium">Recovery Prob.</th>
              <th className="text-left px-4 py-3 font-medium">Risk</th>
              <th className="text-left px-4 py-3 font-medium">Action</th>
              <th className="text-left px-4 py-3 font-medium">Status</th>
              <th className="text-left px-4 py-3 font-medium">Demo</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              // Skeleton Loader
              [...Array(5)].map((_, i) => (
                <tr key={i} className="border-t border-slate-800 animate-pulse">
                  <td className="px-4 py-4"><div className="h-4 bg-slate-800 rounded w-20"></div></td>
                  <td className="px-4 py-4"><div className="h-4 bg-slate-800 rounded w-16"></div></td>
                  <td className="px-4 py-4"><div className="h-4 bg-slate-800 rounded w-12"></div></td>
                  <td className="px-4 py-4"><div className="h-5 bg-slate-800 rounded w-16"></div></td>
                  <td className="px-4 py-4"><div className="h-4 bg-slate-800 rounded w-24"></div></td>
                  <td className="px-4 py-4"><div className="h-5 bg-slate-800 rounded w-20"></div></td>
                  <td className="px-4 py-4"><div className="h-4 bg-slate-800 rounded w-8"></div></td>
                </tr>
              ))
            ) : cases.length > 0 ? (
              cases.map((c) => (
                <tr 
                  key={c.id} 
                  onClick={() => setSelectedCase(c)}
                  className="border-t border-slate-800 hover:bg-slate-800/50 cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3 font-mono text-xs text-slate-400">{c.id.slice(0, 8)}</td>
                  <td className="px-4 py-3">{formatINR(c.amount_at_risk)}</td>
                  <td className="px-4 py-3">
                    {c.recovery_probability != null ? `${(c.recovery_probability * 100).toFixed(0)}%` : "—"}
                  </td>
                  <td className="px-4 py-3">{c.risk_level && <Badge label={c.risk_level} />}</td>
                  <td className="px-4 py-3 text-slate-300">{c.approved_action ?? "—"}</td>
                  <td className="px-4 py-3"><Badge label={c.status} /></td>
                  <td className="px-4 py-3">{c.is_demo ? <span className="text-[10px] font-medium tracking-wider px-1.5 py-0.5 rounded border border-slate-700 text-slate-400">DEMO</span> : ""}</td>
                </tr>
              ))
            ) : (
              // Empty State
              <tr>
                <td colSpan={7} className="px-4 py-12 text-center">
                  <div className="max-w-sm mx-auto text-center">
                    <div className="w-12 h-12 bg-slate-800/50 rounded-full flex items-center justify-center mx-auto mb-4 border border-slate-700">
                      <span className="text-xl">✨</span>
                    </div>
                    <h3 className="text-sm font-medium text-white mb-1">No Failed Payments Yet</h3>
                    <p className="text-xs text-slate-400">
                      When a payment fails on your Razorpay account, ReviveAI will automatically intercept it and display the recovery case here.
                    </p>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <CaseDrawer 
        rcase={selectedCase} 
        onClose={() => setSelectedCase(null)} 
        activities={activities}
      />
    </div>
  );
}
