from datetime import datetime
from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, gen_uuid

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

    max_automated_amount: Mapped[int] = mapped_column(Integer, default=5000000)
    max_recovery_attempts: Mapped[int] = mapped_column(Integer, default=2)
    allowed_actions: Mapped[str] = mapped_column(String, default="RETRY_RECOVERY,PAYMENT_REMINDER,PAYMENT_LINK,ALTERNATIVE_PATH,ESCALATE,NO_ACTION")
    high_risk_requires_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    approval_threshold: Mapped[int] = mapped_column(Integer, default=5000000)

    merchant: Mapped["Merchant"] = relationship(back_populates="policy")
