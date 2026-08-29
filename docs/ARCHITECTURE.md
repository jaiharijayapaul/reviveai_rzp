# Architecture

## Agentic loop

```
OBSERVE → ANALYZE → PREDICT → DECIDE → GUARDRAIL → ACT → VERIFY → MEASURE
```

| Stage | Module | What happens |
|---|---|---|
| OBSERVE | `api/routes/webhooks.py`, `api/routes/demo.py` | A `payment.failed` webhook (or a demo scenario) creates a `Payment` row. |
| ANALYZE / PREDICT | `services/recovery_service.analyze_payment` → `services/prediction_service.py` | Builds a feature vector, scores `recovery_probability` + `risk_level`, creates a `RecoveryCase`. |
| DECIDE | `ai/agent.py` | Calls the LLM (or deterministic fallback) with transaction context; returns a structured `AgentDecision` — recommendation only, no execution. |
| GUARDRAIL | `ai/policy_engine.py` | Pure, rule-based Python. Validates/overrides the recommendation against merchant policy, amount limits, risk level, retry caps, confidence floor. |
| ACT | `services/recovery_service.execute_action` → `services/razorpay_service.py` | Executes **only** the policy-approved action, through the single Razorpay SDK wrapper. |
| VERIFY / MEASURE | `RecoveryResult`, `services/analytics_service.py` | Records outcome; rolls up into dashboard metrics (recovery rate, agent success rate, avg recovery time). |

## Safety architecture

```
LLM Agent
    ↓ (structured JSON only — AgentDecision)
Policy / Guardrail Engine   (deterministic, cannot be influenced by the LLM)
    ↓ (approved action, from a closed enum)
Tool/API Layer               (razorpay_service.py — the only module that calls Razorpay)
    ↓
Razorpay TEST MODE
```

The LLM:
- never sees Razorpay credentials
- never constructs or sends HTTP requests
- never picks an action outside the fixed `ActionType` enum
- never changes a transaction amount
- has its `confidence` and `requires_approval` fields double-checked by the policy engine, not trusted at face value

## AI fallback

If `ANTHROPIC_API_KEY` is unset, or the LLM call fails / returns malformed JSON,
`ai/agent.py` falls back to a deterministic, threshold-based decision function
(`_deterministic_fallback`) so the product always demos reliably:

```python
if recovery_probability > 0.80: PAYMENT_REMINDER
elif recovery_probability > 0.50: PAYMENT_LINK
elif recovery_probability > 0.20: ALTERNATIVE_PATH
else: NO_ACTION
```
(risk_level == HIGH or amount > ₹75,000 always escalates first.)

## Data model

See `backend/app/models/models.py`. Core tables: `merchants`, `merchant_policies`,
`customers`, `orders`, `payments`, `payment_attempts`, `recovery_cases`,
`agent_actions`, `recovery_results`, `webhook_events`.

`recovery_cases` is the spine of the product — one row per revenue-at-risk event,
carrying the ML score, the agent's recommendation, the policy-approved action,
and a status machine (`OPEN → ANALYZING → ACTION_PENDING/APPROVAL_REQUIRED →
IN_PROGRESS → RECOVERED/FAILED/ESCALATED/NO_ACTION`).

## Webhook flow

```
Razorpay → POST /api/webhooks/razorpay → signature verification (HMAC-SHA256)
  → dedup by event_id/payload hash → WebhookEvent stored → payment.failed handler
  → Payment created → recovery_service.analyze_payment → decide_recovery
  → (execute immediately, unless APPROVAL_REQUIRED)
```

Idempotency: every event is hashed and stored with a unique `event_id`; a
duplicate delivery (Razorpay retries webhooks) is detected and ignored before
any side effects run.

## Note on module consolidation

The original spec lists one file per model/schema (`merchant.py`, `customer.py`, …).
For buildathon velocity these are consolidated into `models/models.py` and
`schemas/schemas.py`. Splitting them back out is a pure refactor with no
behavior change — tracked in the README's Future Roadmap.
