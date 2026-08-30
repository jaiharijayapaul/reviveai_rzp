import enum
from datetime import datetime
from sqlalchemy import String, Integer, Numeric, Boolean, ForeignKey, Text, Enum, UniqueConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, gen_uuid

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

class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=gen_uuid)
    payment_id: Mapped[str] = mapped_column(ForeignKey("payments.id"), nullable=False)
    merchant_id: Mapped[str] = mapped_column(ForeignKey("merchants.id"), nullable=False)

    amount_at_risk: Mapped[int] = mapped_column(Integer, nullable=False)
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
    reasoning: Mapped[str] = mapped_column(Text, nullable=True)
    policy_result: Mapped[str] = mapped_column(String, nullable=False)
    policy_notes: Mapped[str] = mapped_column(Text, nullable=True)
    execution_status: Mapped[str] = mapped_column(String, default="PENDING")
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
    event_id: Mapped[str] = mapped_column(String, nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
