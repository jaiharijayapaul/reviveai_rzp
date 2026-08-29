"""
Deterministic Policy / Guardrail Engine.

This is the ONLY component allowed to turn an AI recommendation into an
approved action. It is pure, rule-based Python — no LLM calls here.
The LLM agent's output is treated as an untrusted suggestion until it
passes every rule below.
"""
from dataclasses import dataclass

from app.schemas.schemas import AgentDecision

ALL_ACTIONS = {
    "RETRY_RECOVERY", "PAYMENT_REMINDER", "PAYMENT_LINK",
    "ALTERNATIVE_PATH", "ESCALATE", "NO_ACTION",
}


@dataclass
class PolicyContext:
    amount: int  # paise
    risk_level: str  # LOW/MEDIUM/HIGH
    previous_attempts: int
    max_automated_amount: int
    max_recovery_attempts: int
    allowed_actions: set[str]
    high_risk_requires_approval: bool
    approval_threshold: int
    is_suspicious: bool = False


@dataclass
class PolicyResult:
    result: str  # APPROVED / BLOCKED / MODIFIED
    approved_action: str
    requires_approval: bool
    notes: str


def evaluate(decision: AgentDecision, ctx: PolicyContext) -> PolicyResult:
    """
    Applies deterministic guardrails to an agent decision.
    The agent NEVER executes anything directly — this function is the sole
    authority for what action (if any) is allowed to proceed.
    """
    notes: list[str] = []
    action = decision.recommended_action
    requires_approval = decision.requires_approval

    # Rule: action must be in the allowed action set (structural safety).
    if action not in ALL_ACTIONS:
        return PolicyResult("BLOCKED", "ESCALATE", True, "Unknown action type — escalated for safety.")

    if action not in ctx.allowed_actions:
        notes.append(f"{action} not enabled by merchant policy; escalating.")
        return PolicyResult("MODIFIED", "ESCALATE", True, " ".join(notes))

    # Rule: suspicious activity is never automated.
    if ctx.is_suspicious:
        notes.append("Suspicious activity detected — automation blocked.")
        return PolicyResult("MODIFIED", "ESCALATE", True, " ".join(notes))

    # Rule: max transaction amount eligible for automation.
    if ctx.amount > ctx.max_automated_amount and action not in ("ESCALATE", "NO_ACTION"):
        notes.append(
            f"Amount ₹{ctx.amount/100:.2f} exceeds automated limit "
            f"₹{ctx.max_automated_amount/100:.2f} — requires manual approval."
        )
        requires_approval = True

    # Rule: high-value transactions require approval regardless of action.
    if ctx.amount > ctx.approval_threshold:
        requires_approval = True
        notes.append("Above merchant approval threshold.")

    # Rule: HIGH risk cannot be auto-recovered.
    if ctx.risk_level == "HIGH" and action not in ("ESCALATE", "NO_ACTION"):
        notes.append("HIGH risk transactions must be escalated, not auto-recovered.")
        return PolicyResult("MODIFIED", "ESCALATE", ctx.high_risk_requires_approval, " ".join(notes))

    # Rule: max retry/recovery attempts.
    if ctx.previous_attempts >= ctx.max_recovery_attempts and action == "RETRY_RECOVERY":
        notes.append(f"Max recovery attempts ({ctx.max_recovery_attempts}) reached — escalating.")
        return PolicyResult("MODIFIED", "ESCALATE", True, " ".join(notes))

    # Rule: confidence floor — very low-confidence automation gets escalated.
    if decision.confidence < 0.3 and action not in ("ESCALATE", "NO_ACTION"):
        notes.append("Agent confidence too low for automated action — escalating.")
        return PolicyResult("MODIFIED", "ESCALATE", True, " ".join(notes))

    result = "APPROVED" if not requires_approval else "APPROVED"  # still approved; just flagged
    if requires_approval:
        notes.append("Flagged for merchant approval before execution.")
    else:
        notes.append("Passed all guardrails.")

    return PolicyResult(result, action, requires_approval, " ".join(notes))
