from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import RecoveryCase, AgentAction
from app.schemas.schemas import RecoveryAnalyzeRequest, AgentActionOut
from app.services import recovery_service
from app.models.models import Payment

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/analyze", summary="Convenience: run full OBSERVE->DECIDE loop for a payment")
def analyze(payload: RecoveryAnalyzeRequest, db: Session = Depends(get_db)):
    payment = db.get(Payment, payload.payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail={"code": "PAYMENT_NOT_FOUND", "message": "Payment not found"})
    case = recovery_service.analyze_payment(db, payment)
    action = recovery_service.decide_recovery(db, case)
    return {
        "recovery_case_id": case.id,
        "recovery_probability": float(case.recovery_probability),
        "risk_level": case.risk_level,
        "recommended_action": case.recommended_action,
        "approved_action": action.action_type,
        "policy_result": action.policy_result,
        "reasoning": action.reasoning,
    }


@router.get("/actions", response_model=list[AgentActionOut], summary="List recent agent actions")
def list_actions(db: Session = Depends(get_db), limit: int = 50):
    return db.query(AgentAction).order_by(AgentAction.created_at.desc()).limit(limit).all()
