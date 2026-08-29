"""
Demo Simulation endpoint. Runs the REAL pipeline (prediction -> agent ->
policy engine -> execution) against synthetic, clearly-labeled scenarios so
judges can see the full agentic loop without a live Razorpay TEST payment.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import Merchant, Customer, Order, Payment
from app.schemas.schemas import DemoScenarioRequest
from app.services import recovery_service

router = APIRouter(prefix="/api/demo", tags=["demo"])

SCENARIOS = {
    "TEMPORARY_FAILURE": dict(
        amount=99900, failure_reason="temporary", successful=4, failed=0,
    ),
    "CHECKOUT_ABANDONMENT": dict(
        amount=499900, failure_reason="checkout_abandoned", successful=2, failed=0,
    ),
    "REPEATED_FAILURE": dict(
        amount=249900, failure_reason="card_declined", successful=0, failed=3,
    ),
    "HIGH_VALUE_RISKY": dict(
        amount=7500000, failure_reason="card_declined", successful=0, failed=4,
    ),
}


@router.post("/simulate", summary="Simulate a failed-payment scenario through the full agentic loop")
def simulate(payload: DemoScenarioRequest, db: Session = Depends(get_db)):
    cfg = SCENARIOS.get(payload.scenario)
    if not cfg:
        raise HTTPException(status_code=400, detail={"code": "UNKNOWN_SCENARIO", "message": "Unknown demo scenario"})

    merchant = db.query(Merchant).first()
    if not merchant:
        merchant = Merchant(name="Demo Merchant")
        db.add(merchant)
        db.commit()
        db.refresh(merchant)

    customer = Customer(
        merchant_id=merchant.id, name="Demo Customer", email="demo@example.com",
        successful_payments_count=cfg["successful"], failed_payments_count=cfg["failed"],
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    order = Order(merchant_id=merchant.id, customer_id=customer.id, amount=cfg["amount"], status="created")
    db.add(order)
    db.commit()
    db.refresh(order)

    payment = Payment(
        order_id=order.id, customer_id=customer.id, amount=cfg["amount"],
        currency="INR", status="failed", failure_reason=cfg["failure_reason"],
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    case = recovery_service.analyze_payment(db, payment, is_demo=True)
    action = recovery_service.decide_recovery(db, case)
    result = recovery_service.execute_action(db, case, action)

    return {
        "success": True,
        "demo": True,
        "scenario": payload.scenario,
        "payment_id": payment.id,
        "recovery_case_id": case.id,
        "recovery_probability": float(case.recovery_probability),
        "risk_level": case.risk_level,
        "recommended_action": case.recommended_action,
        "approved_action": action.action_type,
        "policy_result": action.policy_result,
        "policy_notes": action.policy_notes,
        "reasoning": action.reasoning,
        "amount_recovered": result.amount_recovered,
        "status": result.status,
    }
