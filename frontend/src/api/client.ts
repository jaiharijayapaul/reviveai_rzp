const BASE = import.meta.env.VITE_API_URL || "/api";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.error?.message || `Request failed: ${res.status}`);
  }
  return res.json();
}

export interface DashboardOverview {
  revenue_at_risk: number;
  revenue_recovered: number;
  recovery_rate: number;
  failed_payments: number;
  abandoned_checkouts: number;
  active_recovery_cases: number;
  agent_actions_count: number;
  agent_success_rate: number;
  average_recovery_time_seconds: number | null;
  fraud_prevented: number;
  recovery_rate_trend: { day: string; rate: number }[];
}

export interface RecoveryCase {
  id: string;
  payment_id: string;
  amount_at_risk: number;
  recovery_probability: number | null;
  risk_level: string | null;
  recommended_action: string | null;
  approved_action: string | null;
  status: string;
  reason: string | null;
  is_demo: boolean;
  created_at: string;
  updated_at: string;
}

export interface AgentActivityItem {
  id: string;
  recovery_case_id: string;
  action_type: string;
  confidence: number | null;
  reasoning: string | null;
  policy_result: string;
  execution_status: string;
  created_at: string;
}

export const api = {
  overview: () => request<DashboardOverview>("/dashboard/overview"),
  activity: () => request<AgentActivityItem[]>("/dashboard/activity"),
  cases: () => request<RecoveryCase[]>("/recovery/cases"),
  simulate: (scenario: string) =>
    request<any>("/demo/simulate", { method: "POST", body: JSON.stringify({ scenario }) }),
};

export function formatINR(paise: number): string {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 })
    .format(paise / 100);
}
