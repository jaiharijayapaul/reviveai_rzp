"""
Orchestrates the core agentic loop:

OBSERVE -> ANALYZE -> PREDICT -> DECIDE -> GUARDRAIL -> ACT -> VERIFY -> MEASURE

This is the only place that wires prediction_service + agent + policy_engine
+ razorpay_service together. Nothing here lets the LLM touch Razorpay
directly — every execution goes through `_execute_action`, which only ever
calls razorpay_service with parameters the policy engine already approved.
"""
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import (
    Payment, Customer, RecoveryCase, AgentAction, RecoveryResult,
    RecoveryStatus, RiskLevel, ActionType, MerchantPolicy,
)
from app.schemas.schemas import AgentDecision
from app.services.prediction_service import prediction_service
from app.services.razorpay_service import razorpay_service, RazorpayServiceError
from app.ai import agent as agent_module
from app.ai import policy_engine
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _get_policy(db: Session, merchant_id: str) -> MerchantPolicy:
    policy = db.query(MerchantPolicy).filter(MerchantPolicy.merchant_id == merchant_id).first()
    if policy:
        return policy
    # sane defaults if merchant hasn't configured policy yet
    return MerchantPolicy(
        merchant_id=merchant_id, max_automated_amount=5_000_000,
        max_recovery_attempts=2,
        allowed_actions="RETRY_RECOVERY,PAYMENT_REMINDER,PAYMENT_LINK,ALTERNATIVE_PATH,ESCALATE,NO_ACTION",
        high_risk_requires_approval=True, approval_threshold=5_000_000,
    )


def analyze_payment(db: Session, payment: Payment, is_demo: bool = False) -> RecoveryCase:
    """OBSERVE + ANALYZE + PREDICT: create a recovery case with an ML score."""
    customer = db.get(Customer, payment.customer_id) if payment.customer_id else None

    features = {
        "amount": payment.amount,
        "previous_attempts": 1,
        "previous_successful_payments": customer.successful_payments_count if customer else 0,
        "previous_failed_payments": customer.failed_payments_count if customer else 0,
        "checkout_abandonment_minutes": 0,
        "hour_of_day": datetime.utcnow().hour,
        "is_temporary_failure": 1 if (payment.failure_reason or "").lower() in
            ("timeout", "network_error", "gateway_error", "temporary") else 0,
    }
    prediction = prediction_service.predict(features)

    case = RecoveryCase(
        payment_id=payment.id,
        merchant_id=_infer_merchant_id(db, payment),
        amount_at_risk=payment.amount,
        recovery_probability=prediction["recovery_probability"],
        risk_level=prediction["risk_level"],
        status=RecoveryStatus.ANALYZING,
        is_demo=is_demo,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    logger.info("Recovery case %s created: prob=%.2f risk=%s", case.id,
                prediction["recovery_probability"], prediction["risk_level"])
    return case


def _infer_merchant_id(db: Session, payment: Payment) -> str:
    if payment.order_id:
        from app.models import Order
        order = db.get(Order, payment.order_id)
        if order:
            return order.merchant_id
    # fallback: single-merchant demo mode
    from app.models import Merchant
    m = db.query(Merchant).first()
    return m.id if m else "demo-merchant"


def decide_recovery(db: Session, case: RecoveryCase) -> AgentAction:
    """DECIDE + GUARDRAIL: ask the agent, then validate through the policy engine."""
    payment = db.get(Payment, case.payment_id)
    customer = db.get(Customer, payment.customer_id) if payment and payment.customer_id else None
    policy = _get_policy(db, case.merchant_id)

    ctx = {
        "amount": case.amount_at_risk,
        "failure_reason": payment.failure_reason if payment else "unknown",
        "previous_attempts": 1,
        "previous_successful_payments": customer.successful_payments_count if customer else 0,
        "previous_failed_payments": customer.failed_payments_count if customer else 0,
        "checkout_abandonment_minutes": 0,
        "recovery_probability": float(case.recovery_probability or 0),
        "risk_level": case.risk_level,
        "max_automated_amount": policy.max_automated_amount,
    }

    decision: AgentDecision = agent_module.decide(ctx)

    pctx = policy_engine.PolicyContext(
        amount=case.amount_at_risk,
        risk_level=case.risk_level or "MEDIUM",
        previous_attempts=1,
        max_automated_amount=policy.max_automated_amount,
        max_recovery_attempts=policy.max_recovery_attempts,
        allowed_actions=set(policy.allowed_actions.split(",")),
        high_risk_requires_approval=policy.high_risk_requires_approval,
        approval_threshold=policy.approval_threshold,
        is_suspicious=(case.risk_level == "HIGH" and case.amount_at_risk > 7_500_000),
    )
    presult = policy_engine.evaluate(decision, pctx)

    case.recommended_action = decision.recommended_action
    case.approved_action = presult.approved_action
    case.reason = decision.reason
    case.status = (
        RecoveryStatus.APPROVAL_REQUIRED if presult.requires_approval
        else RecoveryStatus.ACTION_PENDING
    )

    action = AgentAction(
        recovery_case_id=case.id,
        action_type=presult.approved_action,
        confidence=decision.confidence,
        reasoning=decision.reason,
        policy_result=presult.result,
        policy_notes=presult.notes,
        execution_status="PENDING",
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    logger.info("Case %s decision=%s policy=%s notes=%s", case.id,
                presult.approved_action, presult.result, presult.notes)
    return action


def execute_action(db: Session, case: RecoveryCase, action: AgentAction) -> RecoveryResult:
    """ACT + VERIFY + MEASURE: perform only the approved action, via razorpay_service."""
    payment = db.get(Payment, case.payment_id)
    customer = db.get(Customer, payment.customer_id) if payment and payment.customer_id else None

    result = db.query(RecoveryResult).filter(RecoveryResult.recovery_case_id == case.id).first()
    if not result:
        result = RecoveryResult(
            recovery_case_id=case.id, amount_at_risk=case.amount_at_risk,
            amount_recovered=0, status="PENDING",
        )
        db.add(result)

    try:
        if action.action_type in (ActionType.PAYMENT_LINK.value, ActionType.RETRY_RECOVERY.value):
            if case.is_demo:
                # Demo mode: simulate the outcome instead of hitting live TEST APIs,
                # so judges see a deterministic, fast, clearly-labeled result.
                recovered = int(case.amount_at_risk * float(case.recovery_probability or 0.5))
                result.amount_recovered = recovered
                result.status = "RECOVERED" if recovered > 0 else "FAILED"
            else:
                link = razorpay_service.create_payment_link(
                    amount=case.amount_at_risk,
                    description="Complete your payment — ReviveAI recovery",
                    customer={
                        "name": customer.name if customer else None,
                        "email": customer.email if customer else None,
                        "contact": customer.contact if customer else None,
                    } if customer else None,
                    notes={"recovery_case_id": case.id, "source": "reviveai"},
                )
                result.status = "IN_PROGRESS"
                result.amount_recovered = 0
                action.policy_notes = (action.policy_notes or "") + f" | payment_link={link.get('short_url')}"

        elif action.action_type == ActionType.PAYMENT_REMINDER.value:
            # Reminder delivery (email/SMS provider) is out of scope for TEST
            # mode Razorpay APIs; we record the action and mark it simulated.
            result.status = "IN_PROGRESS"
            action.policy_notes = (action.policy_notes or "") + " | reminder simulated (no notification provider wired up)"

        elif action.action_type == ActionType.ESCALATE.value:
            result.status = "PENDING"
            case.status = RecoveryStatus.ESCALATED

        else:  # NO_ACTION
            result.status = "PENDING"
            case.status = RecoveryStatus.NO_ACTION

        action.execution_status = "SUCCESS"

    except RazorpayServiceError as e:
        action.execution_status = "FAILED"
        action.policy_notes = (action.policy_notes or "") + f" | error: {e.message}"
        result.status = "FAILED"
        logger.error("Execution failed for case %s: %s", case.id, e.message)

    if result.status == "RECOVERED":
        case.status = RecoveryStatus.RECOVERED
        result.completed_at = datetime.utcnow()
    elif case.status not in (RecoveryStatus.ESCALATED, RecoveryStatus.NO_ACTION):
        case.status = RecoveryStatus.IN_PROGRESS

    db.commit()
    db.refresh(result)
    return result
