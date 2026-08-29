"""
AI Recovery Agent.

Wraps an LLM call (Anthropic Messages API) constrained to structured JSON
output. If no API key is configured, or the call fails / returns malformed
output, falls back to a deterministic rule-based decision engine so the
product always works end-to-end for a demo.

CRITICAL: this module NEVER calls Razorpay or any financial API. Its only
output is an AgentDecision object, which the caller must pass through
app.ai.policy_engine before anything is executed.
"""
import json

from app.config import get_settings
from app.schemas.schemas import AgentDecision
from app.ai.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _deterministic_fallback(ctx: dict) -> AgentDecision:
    """
    Rule-based fallback used when the LLM is unavailable or misbehaves.
    Mirrors the spec's AI FALLBACK requirement so demos never break.
    """
    proba = ctx["recovery_probability"]
    amount = ctx["amount"]

    if ctx.get("risk_level") == "HIGH" or amount > 7_500_000:
        return AgentDecision(
            recommended_action="ESCALATE", confidence=0.6,
            reason="High risk or high value — needs human review.",
            expected_recovery=0, requires_approval=True,
        )
    if proba > 0.80:
        return AgentDecision(
            recommended_action="PAYMENT_REMINDER", confidence=round(proba, 2),
            reason="High recovery likelihood based on customer history.",
            expected_recovery=amount, requires_approval=False,
        )
    if proba > 0.50:
        return AgentDecision(
            recommended_action="PAYMENT_LINK", confidence=round(proba, 2),
            reason="Moderate recovery likelihood — offering a fresh payment link.",
            expected_recovery=int(amount * proba), requires_approval=False,
        )
    if proba > 0.20:
        return AgentDecision(
            recommended_action="ALTERNATIVE_PATH", confidence=round(proba, 2),
            reason="Lower likelihood — suggesting an alternative payment path.",
            expected_recovery=int(amount * proba), requires_approval=False,
        )
    return AgentDecision(
        recommended_action="NO_ACTION", confidence=round(1 - proba, 2),
        reason="Recovery probability too low to justify automated action.",
        expected_recovery=0, requires_approval=False,
    )


def decide(ctx: dict) -> AgentDecision:
    """
    ctx keys: amount, failure_reason, previous_attempts,
    previous_successful_payments, previous_failed_payments,
    checkout_abandonment_minutes, recovery_probability, risk_level,
    max_automated_amount
    """
    settings = get_settings()
    if not settings.ANTHROPIC_API_KEY:
        logger.info("No ANTHROPIC_API_KEY set — using deterministic fallback agent.")
        return _deterministic_fallback(ctx)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        user_prompt = USER_PROMPT_TEMPLATE.format(
            amount_rupees=ctx["amount"] / 100,
            failure_reason=ctx.get("failure_reason", "unknown"),
            previous_attempts=ctx.get("previous_attempts", 1),
            previous_successful_payments=ctx.get("previous_successful_payments", 0),
            previous_failed_payments=ctx.get("previous_failed_payments", 0),
            checkout_abandonment_minutes=ctx.get("checkout_abandonment_minutes", 0),
            recovery_probability=ctx["recovery_probability"],
            risk_level=ctx.get("risk_level", "MEDIUM"),
            max_automated_amount_rupees=ctx.get("max_automated_amount", 5_000_000) / 100,
        )

        response = client.messages.create(
            model=settings.AGENT_MODEL,
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = "".join(block.text for block in response.content if block.type == "text").strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(text)
        return AgentDecision(**data)

    except Exception as e:  # noqa: BLE001 — any LLM/parse failure falls back safely
        logger.warning("Agent LLM call failed (%s) — using deterministic fallback.", e)
        return _deterministic_fallback(ctx)
