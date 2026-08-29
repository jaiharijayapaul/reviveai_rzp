# Demo Guide

## 90-second setup for judges

```bash
# terminal 1
cd backend && uvicorn app.main:app --reload

# terminal 2
cd frontend && npm run dev
```
Open http://localhost:5173 → **Demo** tab.

## Demo script (3 minutes)

1. **The problem (20s).** Open the Dashboard. "Every red number here is a
   customer who tried to pay and failed — today that just gets logged as
   'Payment Failed' and the merchant loses the revenue."

2. **Scenario 1 — Temporary Failure (30s).** Click *Temporary Failure*.
   Walk through the trace as it appears: ML scores this customer at ~85-90%
   recovery probability (4 prior successful payments, transient error) →
   agent recommends `PAYMENT_REMINDER` → policy engine approves instantly
   (low amount, low risk) → simulated result shows the amount recovered.

3. **Scenario 4 — High-Value Risky (30s).** Click *High-Value Risky
   Transaction*. Same pipeline, different outcome: risk level HIGH and
   amount above the automation ceiling → policy engine **overrides** the
   flow straight to `ESCALATE`, regardless of what the agent proposed.
   "This is the guardrail in action — the LLM never gets to auto-recover a
   ₹75,000 transaction on its own."

4. **AI Agent tab (30s).** Show the activity feed: every decision, its
   confidence, the policy verdict (`APPROVED`/`MODIFIED`/`BLOCKED`), and the
   execution outcome — a full audit trail, no hidden chain-of-thought.

5. **Architecture close (30s).** One sentence: "Agent recommends, policy
   engine decides, tool layer executes — the LLM never touches Razorpay
   directly." Point at `docs/ARCHITECTURE.md` if asked for detail.

## Demo scenarios reference

| Scenario | Amount | Profile | Expected outcome |
|---|---|---|---|
| Temporary Failure | ₹999 | 4 prior successes, transient error | High probability → `PAYMENT_REMINDER`, recovered |
| Checkout Abandonment | ₹4,999 | abandoned recently, 2 prior successes | Moderate-high probability → `PAYMENT_LINK`, recovered |
| Repeated Failure | ₹2,499 | 3 prior failures | Lower probability → `ALTERNATIVE_PATH` or escalate |
| High-Value Risky | ₹75,000 | 4 prior failures, high amount | Policy engine forces `ESCALATE`, manual approval required |

All Demo Simulator data is clearly labeled `DEMO` end-to-end (backend
`is_demo` flag on the `RecoveryCase`, surfaced as a badge in the UI) and uses
a simulated execution outcome rather than a live Razorpay TEST API call, so
the demo is fast and deterministic for judging.

## One-line pitch

"ReviveAI doesn't just detect lost revenue — it safely, automatically
attempts to recover it, with an LLM that recommends and a deterministic
guardrail engine that decides."
