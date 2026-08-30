from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Payment, RecoveryCase
from app.schemas.schemas import (
    RecoveryAnalyzeRequest, RecoveryDecideRequest, RecoveryExecuteRequest, RecoveryCaseOut,
)
from app.services import recovery_service

router = APIRouter(prefix="/api/recovery", tags=["recovery"])


@router.post("/analyze", response_model=RecoveryCaseOut, summary="OBSERVE+ANALYZE+PREDICT a failed payment")
def analyze(payload: RecoveryAnalyzeRequest, db: Session = Depends(get_db)):
    payment = db.get(Payment, payload.payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail={"code": "PAYMENT_NOT_FOUND", "message": "Payment not found"})
    case = recovery_service.analyze_payment(db, payment)
    return case


@router.post("/decide", summary="DECIDE+GUARDRAIL: get agent recommendation validated by policy engine")
def decide(payload: RecoveryDecideRequest, db: Session = Depends(get_db)):
    case = db.get(RecoveryCase, payload.recovery_case_id)
    if not case:
        raise HTTPException(status_code=404, detail={"code": "CASE_NOT_FOUND", "message": "Recovery case not found"})
    action = recovery_service.decide_recovery(db, case)
    return {
        "recovery_case_id": case.id,
        "approved_action": action.action_type,
        "policy_result": action.policy_result,
        "policy_notes": action.policy_notes,
        "requires_approval": case.status == "APPROVAL_REQUIRED",
    }


@router.post("/execute", summary="ACT+VERIFY+MEASURE: execute the approved action")
def execute(payload: RecoveryExecuteRequest, db: Session = Depends(get_db)):
    case = db.get(RecoveryCase, payload.recovery_case_id)
    if not case:
        raise HTTPException(status_code=404, detail={"code": "CASE_NOT_FOUND", "message": "Recovery case not found"})
    action = case.actions[-1] if case.actions else None
    if not action:
        raise HTTPException(status_code=400, detail={"code": "NO_DECISION", "message": "Call /decide first"})
    result = recovery_service.execute_action(db, case, action)
    return {
        "recovery_case_id": case.id,
        "status": result.status,
        "amount_recovered": result.amount_recovered,
    }


@router.get("/cases", response_model=list[RecoveryCaseOut], summary="List recovery cases")
def list_cases(db: Session = Depends(get_db), status: str | None = None, limit: int = 100):
    q = db.query(RecoveryCase)
    if status:
        q = q.filter(RecoveryCase.status == status)
    return q.order_by(RecoveryCase.created_at.desc()).limit(limit).all()


@router.get("/cases/{case_id}", response_model=RecoveryCaseOut, summary="Get a recovery case")
def get_case(case_id: str, db: Session = Depends(get_db)):
    case = db.get(RecoveryCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail={"code": "CASE_NOT_FOUND", "message": "Recovery case not found"})
    return case
