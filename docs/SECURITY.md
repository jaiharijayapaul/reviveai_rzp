# Security

## Secrets

- All Razorpay and Anthropic credentials are loaded from environment variables
  (`app/config.py`, `pydantic-settings`). Nothing is hardcoded.
- `.env` is never committed; `.env.example` documents the required keys with
  placeholder values only.
- Secrets are never sent to the frontend — the React app only ever talks to
  `/api/*` on the FastAPI backend, which is the sole holder of Razorpay keys.

## Webhook integrity

- Every inbound webhook is verified with an HMAC-SHA256 signature check against
  `RAZORPAY_WEBHOOK_SECRET` (`utils/security.verify_razorpay_signature`).
  Requests with a missing or invalid signature are rejected with `400` before
  any processing happens.
- Idempotency: each event is deduplicated by `event_id` (or a payload hash
  fallback) in `webhook_events`, so retried deliveries never trigger the
  recovery pipeline twice.

## LLM containment

- The AI agent (`ai/agent.py`) can only return one of six fixed action types
  as structured JSON. It has no tool-calling ability, no network access, and
  no path to Razorpay.
- All agent output is re-validated by the deterministic Policy Engine
  (`ai/policy_engine.py`) before anything executes. The policy engine can
  downgrade, block, or force-escalate any recommendation — including
  overriding a `requires_approval: false` from the agent.
- The agent's `reason` field is a short, user-facing string — the system
  prompt explicitly forbids chain-of-thought, and the frontend never renders
  anything beyond that field.

## Guardrails enforced by the Policy Engine

- Maximum transaction amount eligible for full automation (`max_automated_amount`)
- Amounts above `approval_threshold` always require manual approval
- `risk_level == HIGH` can never be auto-recovered — forced to `ESCALATE`
- Suspicious activity is never automated
- Maximum recovery attempts (`max_recovery_attempts`) enforced per case
- Actions outside a merchant's `allowed_actions` are rejected
- Low agent confidence (`< 0.3`) is escalated instead of automated
- Every decision (agent recommendation + policy verdict + execution result) is persisted to `agent_actions` for audit

## What is never logged

`utils/logging.redact()` strips known-sensitive keys (webhook secret, API
secret, authorization headers, card numbers/CVV) before anything is logged.
No card numbers, full credentials, or unredacted secrets are ever written to
application logs.

## Input validation

All request/response bodies are typed with Pydantic (`schemas/schemas.py`),
which rejects malformed input at the API boundary (e.g. non-enum action
types, out-of-range confidence values, non-positive amounts).

## CORS

`CORS_ORIGINS` is configured explicitly per environment (`app/config.py` /
`app/main.py`) rather than left wide open.

## Known gaps (buildathon MVP)

- No authentication/authorization layer is wired yet (architecture is
  auth-ready: all routes go through FastAPI dependency injection, so a JWT
  dependency can be added to `get_db`-style deps without restructuring).
- Rate limiting is not yet implemented on public endpoints — flagged as a
  pre-production requirement.
