# 💸 ReviveAI

**Turn failed payments into recovered revenue.**

Built for the **Razorpay AI Buildathon 2026** — Track: *AI Revenue Recovery*.

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-8E75B2?style=for-the-badge&logo=googlebard&logoColor=white)

## 🚀 What is ReviveAI?

Merchants lose significant revenue when customers abandon checkout, hit a bank decline, or fail to complete a payment. Traditional systems usually stop at "Payment Failed." 

**ReviveAI** asks the next critical question: *what's the safest, most effective action we can take to recover this revenue right now?*

It is an AI-native agentic revenue recovery platform that intercepts failed transactions and intelligently decides the best course of action—whether that's sending a simple reminder, offering a dynamic discount, or locking out suspected fraud.

## 💡 The Solution

ReviveAI runs every failed or abandoned payment through a bounded, auditable agentic loop:

```text
OBSERVE → ANALYZE → PREDICT → DECIDE → GUARDRAIL → ACT → VERIFY → MEASURE
```

1. **OBSERVE 🔍**: A Razorpay webhook (`payment.failed`) or a demo scenario registers a failed `Payment`. 🔗 [*See webhook implementation*](./backend/app/api/routes/webhooks.py)
2. **ANALYZE / PREDICT 🧠**: A Machine Learning model scores the `recovery_probability` and `risk_level` based on transaction and customer features. 🔗 [*See ML integration*](./backend/ml/train.py)
3. **DECIDE 🤖**: A Gemini LLM agent evaluates the context and recommends one action from a strict *closed* set, formatted as structured JSON. **The LLM has no direct execution power.** 🔗 [*See Agent orchestration*](./backend/app/ai/agent.py)
4. **GUARDRAIL 🛡️**: A deterministic Policy Engine validates or overrides the AI's recommendation based on hardcoded merchant rules (e.g., amount limits, risk thresholds, attempt caps). 🔗 [*See Policy Engine*](./backend/app/ai/policy_engine.py)
5. **ACT ⚡**: Only the approved, policy-compliant action is executed via a safe Razorpay-SDK wrapper. 🔗 [*See Razorpay SDK wrapper*](./backend/app/services/razorpay_service.py)
6. **VERIFY / MEASURE 📊**: The outcome is recorded and aggregated into recovery-rate analytics on the merchant dashboard. 🔗 [*See Dashboard API*](./backend/app/api/routes/dashboard.py)

### Why this is safe
The LLM never touches money or external APIs directly. It is heavily sandboxed:
`LLM Agent → Structured Decision → Policy/Guardrail Engine → Allowed Action → Tool/API Layer → Razorpay TEST MODE`

## 🛠️ Tech Stack & Frameworks

**Backend** [📁 `./backend`](./backend)
*   **Framework:** Python 3, FastAPI (high-performance async REST API)
*   **Database:** PostgreSQL with SQLAlchemy (ORM) and Alembic (Migrations)
*   **Data Validation:** Pydantic & Pydantic-Settings
*   **Machine Learning:** scikit-learn (RandomForest), pandas, numpy for the recovery-probability model.
*   **Testing:** Pytest for policy engine, webhooks, and prediction logic.

**AI & Agent**
*   **LLM Provider:** Google Gemini (`gemini-2.5-pro` via `google-generativeai`)
*   **Agent Architecture:** Structured JSON outputs with a deterministic rule-based fallback (works even if API keys are missing).

**Frontend** [📁 `./frontend`](./frontend)
*   **Framework:** React 18, TypeScript, Vite
*   **Styling:** Tailwind CSS
*   **Routing:** React Router DOM
*   **Data Visualization:** Recharts (for dashboard analytics)
*   **Toast Notifications:** react-hot-toast

**Payments**
*   **Provider:** Razorpay (TEST MODE) utilizing Orders, Payments, Payment Links, and Webhooks.

## 🔑 API Keys Used

The following environment variables are required in the backend ([`backend/.env`](./backend/.env.example)):

*   `RAZORPAY_KEY_ID`: Your Razorpay Test Mode Key ID.
*   `RAZORPAY_KEY_SECRET`: Your Razorpay Test Mode Key Secret.
*   `RAZORPAY_WEBHOOK_SECRET`: A secret string used to verify the cryptographic signatures of incoming Razorpay webhooks.
*   `GEMINI_API_KEY`: Your Google Gemini API key to power the AI Agent decisions. *(Note: If unset, the system gracefully degrades to a deterministic rule-based fallback model).*

## 🚧 Issues Faced & How We Solved Them

1.  **Issue: LLM Hallucinations and Unsafe API Calls**
    *   *Problem:* LLMs are non-deterministic. Giving an LLM direct access to a payment API could result in hallucinated refunds, invalid endpoints, or dangerous financial actions.
    *   *Solution:* We implemented the **Guardrail Pattern**. The Gemini agent is forced to output a structured JSON response selecting from an enum of allowed actions (`PAYMENT_REMINDER`, `NEW_PAYMENT_LINK`, `FRAUD_LOCK`, etc.). This response is then piped through a deterministic **Policy Engine** which enforces hard rules. 🔗 [*Review the Policy logic*](./backend/app/ai/policy_engine.py)

2.  **Issue: Testing Webhook Flows Locally**
    *   *Problem:* Triggering real failed payments in Razorpay to test the end-to-end webhook-to-agent pipeline is tedious and slow during active development.
    *   *Solution:* We built a comprehensive **Demo Simulator** route. It mocks Razorpay webhook payloads and injects them directly into the processing pipeline, allowing us to test edge cases instantly. 🔗 [*Review the Demo endpoints*](./backend/app/api/routes/demo.py)

3.  **Issue: ML Cold Start Problem**
    *   *Problem:* We didn't have access to real merchant failure data to train our `recovery_probability` model.
    *   *Solution:* We wrote a Python script to generate a synthetic dataset with plausible distributions of amounts, error codes, and customer histories. This allowed us to train a baseline RandomForest model. 🔗 [*Review the ML Dataset Generator*](./backend/ml/generate_dataset.py)

## 💻 Frontend: How it Works & What it Has

The frontend is a modern Single Page Application (SPA) built with React and Vite. It communicates asynchronously with the FastAPI backend.

**Key Features & Pages:**
*   **Dashboard (`/`):** High-level overview of revenue recovery metrics using `Recharts`. 🔗 [*`src/pages/Dashboard.tsx`*](./frontend/src/pages/)
*   **Transactions (`/transactions`):** Detailed table view of all failed payments, risk levels, and agent actions.
*   **AI Agent View (`/agent`):** Deep dives into the "brain" of the system, showing Gemini's reasoning trace.
*   **Demo Simulator (`/demo`):** Control panel with one-click scenarios to exercise the backend.
*   **Policy Co-Pilot (`/policy`):** Interface to define and tweak the hard rules of the Policy Engine.

## ⚙️ Backend: What it Does & What it Has

The backend is the core intelligence and execution engine of ReviveAI.

**What it does:**
It exposes REST APIs for the frontend, securely listens for Razorpay webhooks, runs transactions through the Scikit-Learn ML model, prompts the Gemini LLM for a recovery strategy, filters that strategy through the Policy Engine, and safely communicates with the Razorpay API to generate new payment links.

**What it has ([`backend/`](./backend)):**
*   [`app/api/routes/`](./backend/app/api/routes/): FastAPI routers for different domains (`orders`, `payments`, `webhooks`, `agent`, `dashboard`, `demo`).
*   [`app/services/`](./backend/app/services/): Core business logic, including `razorpay_service.py` and `recovery_service.py`.
*   [`app/db/`](./backend/app/db/): Database configuration, SQLAlchemy models, and session management.
*   [`app/ai/`](./backend/app/ai/): The deterministic Policy Guardrail engine and Gemini AI agent orchestration.
*   [`ml/`](./backend/ml/): The Scikit-Learn machine learning pipeline.
*   [`tests/`](./backend/tests/): Comprehensive test suites.

## 🚀 Setup Instructions

### 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
# On Windows use: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env   # Fill in RAZORPAY & GEMINI keys and Postgres URL

# Generate training data & train model
python ml/generate_dataset.py
python ml/train.py

# Start server
uvicorn app.main:app --reload
```
API docs available at: `http://localhost:8000/docs`

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```
Dashboard available at: `http://localhost:5173`

---
*Note: This project is built as a proof-of-concept for the buildathon. Synthetic data is used for ML, and all actions are executed in Razorpay TEST mode.*
