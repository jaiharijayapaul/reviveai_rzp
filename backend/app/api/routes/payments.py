from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import Payment
from app.schemas.schemas import PaymentOut

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.get("", response_model=list[PaymentOut], summary="List payments")
def list_payments(db: Session = Depends(get_db), status: str | None = None, limit: int = 50):
    q = db.query(Payment)
    if status:
        q = q.filter(Payment.status == status)
    return q.order_by(Payment.created_at.desc()).limit(limit).all()


@router.get("/{payment_id}", response_model=PaymentOut, summary="Get a payment")
def get_payment(payment_id: str, db: Session = Depends(get_db)):
    payment = db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail={"code": "PAYMENT_NOT_FOUND", "message": "Payment not found"})
    return payment
