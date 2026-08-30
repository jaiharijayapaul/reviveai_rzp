import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

interface Policy {
  max_automated_amount: number;
  max_recovery_attempts: number;
  allowed_actions: string;
  high_risk_requires_approval: boolean;
  approval_threshold: number;
}

export default function PolicySettings() {
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [loading, setLoading] = useState(true);
  const [prompt, setPrompt] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lastAgentMessage, setLastAgentMessage] = useState("");

  const fetchPolicy = async () => {
    try {
      const res = await fetch(`${API_BASE}/policy/`);
      const data = await res.json();
      setPolicy(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicy();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setIsSubmitting(true);
    setLastAgentMessage("");
    try {
      const res = await fetch(`${API_BASE}/policy/copilot`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: prompt }),
      });
      const data = await res.json();
      if (data.success) {
        setPolicy(data.policy);
        setLastAgentMessage(data.agent_message);
        setPrompt("");
        toast.success("ReviveAI Co-Pilot successfully updated your rules.");
      } else {
        toast.error(data.error?.message || "Update Failed");
      }
    } catch (e) {
      console.error(e);
      toast.error("Could not connect to Co-Pilot.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white">Policy Settings</h1>
        <p className="text-gray-400 mt-2">Manage your AI recovery rules with the ReviveAI Co-Pilot.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Co-Pilot Chat */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-emerald-400">
              <path d="M12 8V4H8"></path>
              <rect width="16" height="12" x="4" y="8" rx="2"></rect>
              <path d="M2 14h2"></path>
              <path d="M20 14h2"></path>
              <path d="M15 13v2"></path>
              <path d="M9 13v2"></path>
            </svg>
            <h2 className="text-lg font-semibold text-white">ReviveAI Co-Pilot</h2>
          </div>
          
          <div className="space-y-4">
            <p className="text-gray-300 text-sm">
              Use natural language to configure your recovery policies. For example, try saying: <i>"We are having a Diwali flash sale. Increase the automated recovery limit to ₹25,000."</i>
            </p>
            
            <form onSubmit={handleSubmit} className="flex flex-col gap-3">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Ask Co-Pilot to change a rule..."
                className="w-full min-h-[120px] bg-slate-950 border border-slate-800 rounded-md p-3 text-white placeholder-slate-500 focus:ring-brand-500 focus:border-brand-500 outline-none transition-colors"
              />
              <button 
                type="submit" 
                className="self-end bg-brand-600 hover:bg-brand-500 text-white font-medium py-2 px-4 rounded-md transition-colors disabled:opacity-50"
                disabled={isSubmitting}
              >
                {isSubmitting ? "Updating..." : "Update Policy"}
              </button>
            </form>

            {lastAgentMessage && (
              <div className="mt-4 p-4 bg-emerald-900/30 border border-emerald-500/50 rounded-lg flex items-start gap-3">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-emerald-400 mt-0.5 shrink-0">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                  <polyline points="22 4 12 14.01 9 11.01"></polyline>
                </svg>
                <p className="text-emerald-100 text-sm">{lastAgentMessage}</p>
              </div>
            )}
          </div>
        </div>

        {/* Current Policy View */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 shadow-sm">
          <div className="flex items-center gap-2 mb-6">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-400">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"></path>
            </svg>
            <h2 className="text-lg font-semibold text-white">Current Rules</h2>
          </div>
          
          {loading ? (
            <div className="text-slate-400">Loading policy...</div>
          ) : policy ? (
            <div className="space-y-6">
              <div className="space-y-1">
                <h3 className="text-sm font-medium text-slate-400">Max Automated Recovery Amount</h3>
                <p className="text-lg text-white font-mono">₹{(policy.max_automated_amount / 100).toLocaleString()}</p>
              </div>
              
              <div className="space-y-1">
                <h3 className="text-sm font-medium text-slate-400">Max Recovery Attempts</h3>
                <p className="text-lg text-white font-mono">{policy.max_recovery_attempts} attempts</p>
              </div>

              <div className="space-y-1">
                <h3 className="text-sm font-medium text-slate-400">High Risk Requires Approval</h3>
                <p className="text-lg text-white font-mono">{policy.high_risk_requires_approval ? "Yes" : "No"}</p>
              </div>

              {policy.high_risk_requires_approval && (
                <div className="space-y-1">
                  <h3 className="text-sm font-medium text-slate-400">Approval Threshold</h3>
                  <p className="text-lg text-white font-mono">₹{(policy.approval_threshold / 100).toLocaleString()}</p>
                </div>
              )}

              <div className="space-y-2">
                <h3 className="text-sm font-medium text-slate-400">Allowed Actions</h3>
                <div className="flex flex-wrap gap-2">
                  {policy.allowed_actions.split(',').map((action) => (
                    <span key={action} className="px-2 py-1 bg-slate-800 text-slate-300 rounded text-xs font-medium border border-slate-700">
                      {action}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-slate-400">Failed to load policy.</div>
          )}
        </div>
      </div>
    </div>
  );
}
