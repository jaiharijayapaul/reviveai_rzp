"""
SQLAlchemy ORM models for ReviveAI.

Consolidated into one module for buildathon velocity; splitting into
merchant.py / customer.py / order.py / payment.py / recovery_case.py /
agent_action.py / webhook_event.py (per the original spec) is a
straightforward follow-up refactor once schemas stabilize.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    String, Integer, Numeric, Boolean, DateTime, ForeignKey, Text, Enum, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class RecoveryStatus(str, enum.Enum):
    OPEN = "OPEN"
    ANALYZING = "ANALYZING"
    ACTION_PENDING = "ACTION_PENDING"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    IN_PROGRESS = "IN_PROGRESS"
    RECOVERED = "RECOVERED"
    FAILED = "FAILED"
    ESCALATED = "ESCALATED"
    NO_ACTION = "NO_ACTION"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ActionType(str, enum.Enum):
    RETRY_RECOVERY = "RETRY_RECOVERY"
    PAYMENT_REMINDER = "PAYMENT_REMINDER"
    PAYMENT_LINK = "PAYMENT_LINK"
    ALTERNATIVE_PATH = "ALTERNATIVE_PATH"
    ESCALATE = "ESCALATE"
    NO_ACTION = "NO_ACTION"


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String, nullable=False)
    razorpay_key_id: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    policy: Mapped["MerchantPolicy"] = relationship(back_populates="merchant", uselist=False)


class MerchantPolicy(Base):
    __tablename__ = "merchant_policies"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    merchant_id: Mapped[str] = mapped_column(ForeignKey("merchants.id"), nullable=False)

    max_automated_amount: Mapped[int] = mapped_column(Integer, default=5000000)  # paise
    max_recovery_attempts: Mapped[int] = mapped_column(Integer, default=2)
    allowed_actions: Mapped[str] = mapped_column(
        String, default="RETRY_RECOVERY,PAYMENT_REMINDER,PAYMENT_LINK,ALTERNATIVE_PATH,ESCALATE,NO_ACTION"
    )
    high_risk_requires_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    approval_threshold: Mapped[int] = mapped_column(Integer, default=5000000)  # paise

    merchant: Mapped["Merchant"] = relationship(back_populates="policy")


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    merchant_id: Mapped[str] = mapped_column(ForeignKey("merchants.id"), nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=True)
    contact: Mapped[str] = mapped_column(String, nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=True)
    successful_payments_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_payments_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    merchant_id: Mapped[str] = mapped_column(ForeignKey("merchants.id"), nullable=False)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), nullable=True)
    razorpay_order_id: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # paise
    currency: Mapped[str] = mapped_column(String, default="INR")
    status: Mapped[str] = mapped_column(String, default="created")
    receipt: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    razorpay_payment_id: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    razorpay_order_id: Mapped[str] = mapped_column(String, nullable=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), nullable=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), nullable=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # paise
    currency: Mapped[str] = mapped_column(String, default="INR")
    status: Mapped[str] = mapped_column(String, nullable=False)  # created/authorized/captured/failed
    method: Mapped[str] = mapped_column(String, nullable=True)
    failure_reason: Mapped[str] = mapped_column(String, nullable=True)
    error_code: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), nullable=False)
    payment_id: Mapped[str] = mapped_column(ForeignKey("payments.id"), nullable=True)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    payment_id: Mapped[str] = mapped_column(ForeignKey("payments.id"), nullable=False)
    merchant_id: Mapped[str] = mapped_column(ForeignKey("merchants.id"), nullable=False)

    amount_at_risk: Mapped[int] = mapped_column(Integer, nullable=False)  # paise
    recovery_probability: Mapped[float] = mapped_column(Numeric(4, 3), nullable=True)
    risk_level: Mapped[str] = mapped_column(Enum(RiskLevel), nullable=True)

    recommended_action: Mapped[str] = mapped_column(Enum(ActionType), nullable=True)
    approved_action: Mapped[str] = mapped_column(Enum(ActionType), nullable=True)

    status: Mapped[str] = mapped_column(Enum(RecoveryStatus), default=RecoveryStatus.OPEN)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    actions: Mapped[list["AgentAction"]] = relationship(back_populates="recovery_case")
    result: Mapped["RecoveryResult"] = relationship(back_populates="recovery_case", uselist=False)


class AgentAction(Base):
    __tablename__ = "agent_actions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    recovery_case_id: Mapped[str] = mapped_column(ForeignKey("recovery_cases.id"), nullable=False)

    action_type: Mapped[str] = mapped_column(Enum(ActionType), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), nullable=True)
    reasoning: Mapped[str] = mapped_column(Text, nullable=True)  # short user-facing reason only
    policy_result: Mapped[str] = mapped_column(String, nullable=False)  # APPROVED / BLOCKED / MODIFIED
    policy_notes: Mapped[str] = mapped_column(Text, nullable=True)
    execution_status: Mapped[str] = mapped_column(String, default="PENDING")  # PENDING/SUCCESS/FAILED
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    recovery_case: Mapped["RecoveryCase"] = relationship(back_populates="actions")


class RecoveryResult(Base):
    __tablename__ = "recovery_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    recovery_case_id: Mapped[str] = mapped_column(ForeignKey("recovery_cases.id"), unique=True, nullable=False)
    amount_at_risk: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_recovered: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, default="PENDING")
    recovery_time_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    recovery_case: Mapped["RecoveryCase"] = relationship(back_populates="result")


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    __table_args__ = (UniqueConstraint("event_id", name="uq_webhook_event_id"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    event_id: Mapped[str] = mapped_column(String, nullable=False)  # razorpay event id or derived hash
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
