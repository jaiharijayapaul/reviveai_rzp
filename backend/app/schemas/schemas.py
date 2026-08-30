"""
Pydantic request/response schemas.
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


# ---------- Orders ----------
class OrderCreate(BaseModel):
    amount: int = Field(..., gt=0, description="Amount in paise (e.g. 99900 = ₹999.00)")
    currency: str = "INR"
    receipt: Optional[str] = None
    customer_email: Optional[str] = None
    customer_contact: Optional[str] = None


class OrderOut(BaseModel):
    id: str
    razorpay_order_id: Optional[str]
    amount: int
    currency: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Payments ----------
class PaymentOut(BaseModel):
    id: str
    razorpay_payment_id: Optional[str]
    order_id: Optional[str]
    amount: int
    status: str
    method: Optional[str]
    failure_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Recovery ----------
class RecoveryAnalyzeRequest(BaseModel):
    payment_id: str


class RecoveryDecideRequest(BaseModel):
    recovery_case_id: str


class RecoveryExecuteRequest(BaseModel):
    recovery_case_id: str
    override_action: Optional[str] = None  # merchant/manual override (still passes policy engine)


class RecoveryCaseOut(BaseModel):
    id: str
    payment_id: str
    amount_at_risk: int
    recovery_probability: Optional[float]
    risk_level: Optional[str]
    recommended_action: Optional[str]
    approved_action: Optional[str]
    status: str
    reason: Optional[str]
    is_demo: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- Agent ----------
class AgentDecision(BaseModel):
    """Structured output the agent MUST produce. Never free-form / never executes anything."""
    recommended_action: Literal[
        "RETRY_RECOVERY", "PAYMENT_REMINDER", "PAYMENT_LINK",
        "ALTERNATIVE_PATH", "ESCALATE", "NO_ACTION",
        "DYNAMIC_OFFER", "RESTRICTED_LINK", "FRAUD_LOCK"
    ]
    confidence: float = Field(..., ge=0, le=1)
    reason: str  # short, user-facing, no chain-of-thought
    expected_recovery: int = Field(..., ge=0, description="Expected recovered amount in paise")
    requires_approval: bool = False


class AgentActionOut(BaseModel):
    id: str
    recovery_case_id: str
    action_type: str
    confidence: Optional[float]
    reasoning: Optional[str]
    policy_result: str
    policy_notes: Optional[str]
    execution_status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Demo ----------
class DemoScenarioRequest(BaseModel):
    scenario: Literal[
        "TEMPORARY_FAILURE", "CHECKOUT_ABANDONMENT",
        "REPEATED_FAILURE", "HIGH_VALUE_RISKY",
        "VIP_INSUFFICIENT_FUNDS", "HDFC_CARD_DOWNTIME", "FRAUD_ATTEMPT"
    ]


# ---------- Dashboard ----------
class DashboardOverview(BaseModel):
    revenue_at_risk: int
    revenue_recovered: int
    recovery_rate: float
    failed_payments: int
    abandoned_checkouts: int
    active_recovery_cases: int
    agent_actions_count: int
    agent_success_rate: float
    average_recovery_time_seconds: Optional[float]
    fraud_prevented: int


# ---------- Errors ----------
class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
