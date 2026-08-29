"""
Unit tests for the deterministic policy/guardrail engine.
Pure logic — no DB, no network — runs anywhere with `pytest`.
"""
from app.ai.policy_engine import evaluate, PolicyContext
from app.schemas.schemas import AgentDecision


def make_ctx(**overrides):
    defaults = dict(
        amount=99900, risk_level="LOW", previous_attempts=1,
        max_automated_amount=5_000_000, max_recovery_attempts=2,
        allowed_actions={"RETRY_RECOVERY", "PAYMENT_REMINDER", "PAYMENT_LINK",
                          "ALTERNATIVE_PATH", "ESCALATE", "NO_ACTION"},
        high_risk_requires_approval=True, approval_threshold=5_000_000,
        is_suspicious=False,
    )
    defaults.update(overrides)
    return PolicyContext(**defaults)


def test_low_risk_high_confidence_is_approved_without_approval():
    decision = AgentDecision(recommended_action="PAYMENT_REMINDER", confidence=0.9,
                              reason="likely to recover", expected_recovery=99900, requires_approval=False)
    result = evaluate(decision, make_ctx())
    assert result.result == "APPROVED"
    assert result.approved_action == "PAYMENT_REMINDER"
    assert result.requires_approval is False


def test_high_risk_action_is_forced_to_escalate():
    decision = AgentDecision(recommended_action="PAYMENT_REMINDER", confidence=0.7,
                              reason="looks fine", expected_recovery=100000, requires_approval=False)
    result = evaluate(decision, make_ctx(risk_level="HIGH"))
    assert result.approved_action == "ESCALATE"
    assert result.requires_approval is True


def test_amount_over_automated_limit_requires_approval():
    decision = AgentDecision(recommended_action="PAYMENT_LINK", confidence=0.8,
                              reason="moderate", expected_recovery=6_000_000, requires_approval=False)
    result = evaluate(decision, make_ctx(amount=6_000_000, max_automated_amount=5_000_000, approval_threshold=5_000_000))
    assert result.requires_approval is True


def test_suspicious_activity_is_never_automated():
    decision = AgentDecision(recommended_action="RETRY_RECOVERY", confidence=0.95,
                              reason="confident", expected_recovery=99900, requires_approval=False)
    result = evaluate(decision, make_ctx(is_suspicious=True))
    assert result.approved_action == "ESCALATE"


def test_max_retry_attempts_forces_escalation():
    decision = AgentDecision(recommended_action="RETRY_RECOVERY", confidence=0.8,
                              reason="retry", expected_recovery=99900, requires_approval=False)
    result = evaluate(decision, make_ctx(previous_attempts=2, max_recovery_attempts=2))
    assert result.approved_action == "ESCALATE"


def test_disallowed_action_for_merchant_is_blocked():
    decision = AgentDecision(recommended_action="ALTERNATIVE_PATH", confidence=0.7,
                              reason="alt path", expected_recovery=50000, requires_approval=False)
    result = evaluate(decision, make_ctx(allowed_actions={"ESCALATE", "NO_ACTION"}))
    assert result.approved_action == "ESCALATE"


def test_low_confidence_is_escalated():
    decision = AgentDecision(recommended_action="PAYMENT_LINK", confidence=0.1,
                              reason="unsure", expected_recovery=10000, requires_approval=False)
    result = evaluate(decision, make_ctx())
    assert result.approved_action == "ESCALATE"
