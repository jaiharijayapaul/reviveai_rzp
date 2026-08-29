from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import Order, Merchant, Customer
from app.schemas.schemas import OrderCreate, OrderOut
from app.services.razorpay_service import razorpay_service, RazorpayServiceError

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=OrderOut, summary="Create a Razorpay TEST MODE order")
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    merchant = db.query(Merchant).first()
    if not merchant:
        merchant = Merchant(name="Demo Merchant")
        db.add(merchant)
        db.commit()
        db.refresh(merchant)

    customer = None
    if payload.customer_email or payload.customer_contact:
        customer = Customer(
            merchant_id=merchant.id, email=payload.customer_email, contact=payload.customer_contact,
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

    try:
        rp_order = razorpay_service.create_order(
            amount=payload.amount, currency=payload.currency, receipt=payload.receipt,
        )
    except RazorpayServiceError as e:
        raise HTTPException(status_code=502, detail={"code": e.code, "message": e.message})

    order = Order(
        merchant_id=merchant.id,
        customer_id=customer.id if customer else None,
        razorpay_order_id=rp_order["id"],
        amount=payload.amount,
        currency=payload.currency,
        status=rp_order.get("status", "created"),
        receipt=payload.receipt,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.get("", response_model=list[OrderOut], summary="List orders")
def list_orders(db: Session = Depends(get_db), limit: int = 50):
    return db.query(Order).order_by(Order.created_at.desc()).limit(limit).all()


@router.get("/{order_id}", response_model=OrderOut, summary="Get an order")
def get_order(order_id: str, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail={"code": "ORDER_NOT_FOUND", "message": "Order not found"})
    return order
