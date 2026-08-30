from fastapi import APIRouter, Depends, Request, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import json

from app.db.database import get_db, SessionLocal
from app.services.webhook_service import process_webhook, WebhookVerificationError
from app.models import Payment, Order, RecoveryStatus
from app.services import recovery_service
from app.utils.logging import get_logger

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
logger = get_logger(__name__)


def background_handle_payment_failed(payload_entity: dict):
    db = SessionLocal()
    try:
        _handle_payment_failed(db, payload_entity)
    finally:
        db.close()


def background_handle_payment_captured(payload_entity: dict):
    db = SessionLocal()
    try:
        _handle_payment_captured(db, payload_entity)
    finally:
        db.close()


@router.post("/razorpay", summary="Razorpay webhook receiver")
async def razorpay_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    raw_body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    try:
        event_json = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail={"code": "INVALID_PAYLOAD", "message": "Malformed JSON"})

    try:
        event = process_webhook(db, raw_body, signature, event_json)
    except WebhookVerificationError:
        raise HTTPException(status_code=400, detail={"code": "INVALID_SIGNATURE", "message": "Signature verification failed"})

    if event is None:
        return {"success": True, "status": "duplicate_ignored"}

    event_type = event_json.get("event", "")
    payload_entity = event_json.get("payload", {})

    try:
        if event_type == "payment.failed":
            background_tasks.add_task(background_handle_payment_failed, payload_entity)
        elif event_type == "payment.captured":
            background_tasks.add_task(background_handle_payment_captured, payload_entity)
        # Other event types are stored for audit but not yet acted on.
    finally:
        event.processed = True
        db.commit()

    return {"success": True, "status": "processed"}


def _handle_payment_failed(db: Session, payload_entity: dict):
    entity = payload_entity.get("payment", {}).get("entity", {})
    if not entity:
        return

    order = db.query(Order).filter(Order.razorpay_order_id == entity.get("order_id")).first()
    payment = Payment(
        razorpay_payment_id=entity.get("id"),
        razorpay_order_id=entity.get("order_id"),
        order_id=order.id if order else None,
        customer_id=order.customer_id if order else None,
        amount=entity.get("amount", 0),
        currency=entity.get("currency", "INR"),
        status="failed",
        method=entity.get("method"),
        failure_reason=entity.get("error_description") or entity.get("error_reason"),
        error_code=entity.get("error_code"),
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    logger.info("payment.failed ingested -> payment %s, triggering recovery pipeline", payment.id)

    # Kick off the agentic loop automatically for the newly observed failure.
    case = recovery_service.analyze_payment(db, payment)
    action = recovery_service.decide_recovery(db, case)
    if case.status != RecoveryStatus.APPROVAL_REQUIRED:
        recovery_service.execute_action(db, case, action)


def _handle_payment_captured(db: Session, payload_entity: dict):
    entity = payload_entity.get("payment", {}).get("entity", {})
    if not entity:
        return
    payment = db.query(Payment).filter(Payment.razorpay_payment_id == entity.get("id")).first()
    if payment:
        payment.status = "captured"
        db.commit()
