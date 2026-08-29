# ReviveAI

**Turn failed payments into recovered revenue.**

Built for the **Razorpay AI Buildathon 2026** — Track: *AI Revenue Recovery*.

## Problem

Merchants lose revenue when customers abandon checkout, hit a bank decline,
or fail to complete payment. Traditional systems stop at "Payment Failed."
ReviveAI asks the next question: *what's the safest action we can take to
recover this revenue?*

## Solution

ReviveAI runs every failed/abandoned payment through a bounded, auditable
agentic loop:

```
OBSERVE → ANALYZE → PREDICT → DECIDE → GUARDRAIL → ACT → VERIFY → MEASURE
```

1. **OBSERVE** — a Razorpay webhook (`payment.failed`) or a demo scenario creates a `Payment`.
2. **ANALYZE / PREDICT** — an ML model scores `recovery_probability` and `risk_level` from transaction + customer features.
3. **DECIDE** — an LLM agent recommends one action from a *closed* set, as structured JSON, with no execution power.
4. **GUARDRAIL** — a deterministic Policy Engine validates or overrides the recommendation (amount limits, risk rules, attempt caps, merchant policy).
5. **ACT** — only the approved action is executed, via a single Razorpay-SDK wrapper (`razorpay_service.py`).
6. **VERIFY / MEASURE** — the outcome is recorded and rolled up into recovery-rate analytics on the merchant dashboard.

## Why this is safe

The LLM never touches money directly:

```
LLM Agent → Structured Decision → Policy/Guardrail Engine → Allowed Action → Tool/API Layer → Razorpay TEST MODE
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and [`docs/SECURITY.md`](docs/SECURITY.md) for details.

## Tech stack

- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy, PostgreSQL (Alembic-ready)
- **ML:** scikit-learn (RandomForest) recovery-probability model, trained on a synthetic/demo dataset
- **Agent:** Anthropic Messages API with a deterministic rule-based fallback (works with zero API keys)
- **Frontend:** React + TypeScript + Tailwind CSS + Recharts
- **Payments:** Razorpay TEST MODE (Orders, Payments, Payment Links, Webhooks)

## Project layout

```
reviveai/
  backend/
    app/            FastAPI app (api/, models/, schemas/, services/, ai/, db/, utils/)
    ml/              dataset generator, training script, prediction CLI, artifacts/
    tests/           pytest unit tests (policy engine, webhook security, prediction)
    requirements.txt
    .env.example
  frontend/
    src/             React + TS dashboard (pages/, components/, api/)
  docs/
    ARCHITECTURE.md
    API.md
    DEMO.md
    SECURITY.md
```

## Setup

### 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET (TEST MODE) and a Postgres URL

# generate synthetic training data + train the recovery model (already included as an artifact,
# but you can regenerate it):
python ml/generate_dataset.py
python ml/train.py

uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs (FastAPI Swagger/OpenAPI, auto-generated).

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard: http://localhost:5173

### 3. Environment variables

See `backend/.env.example`. Never commit a real `.env`. `ANTHROPIC_API_KEY` is optional —
if unset, the agent uses a transparent deterministic fallback (see `docs/ARCHITECTURE.md#ai-fallback`)
so the demo always works.

## Testing

```bash
cd backend
pytest
```

Covers: policy engine guardrail rules, webhook signature verification + idempotency, and the
ML prediction service's fallback heuristic.

## Demo scenarios

Four one-click scenarios exercise the full pipeline without needing a live Razorpay TEST payment.
See [`docs/DEMO.md`](docs/DEMO.md) for the buildathon demo script and 3-minute pitch.

## Important honesty notes

- The synthetic training dataset (`backend/ml/data/synthetic_recovery_dataset.csv`) is **generated, not real merchant data** — clearly labeled as such in code and docs.
- Demo Simulator results are labeled `DEMO` end-to-end (backend `is_demo` flag → frontend badge) and use simulated outcomes instead of live TEST-mode API calls, so judges get fast, deterministic results.
- Only Razorpay operations that are actually documented (Orders, Payments, Payment Links, Webhooks) are implemented — nothing is invented.
- Reminder delivery (SMS/email) is not wired to a real notification provider in this MVP; actions of that type are recorded and explicitly marked "simulated" in `policy_notes`.

## Future roadmap

- Split `models/models.py` and `schemas/schemas.py` into the fully-separated per-entity files from the original spec.
- Wire a real notification provider (SMS/email) for `PAYMENT_REMINDER`.
- Alembic migrations instead of `create_all` at startup.
- Per-merchant multi-tenant auth (JWT/OAuth) — architecture is auth-ready but not yet wired.
- Replace the synthetic dataset with real (anonymized, consented) merchant recovery outcomes once available.
- A/B test agent recommendations against the deterministic fallback to quantify LLM lift.
