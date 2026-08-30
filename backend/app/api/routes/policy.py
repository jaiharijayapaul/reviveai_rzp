import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import anthropic

from app.config import get_settings
from app.db.database import get_db
from app.models import Merchant, MerchantPolicy
from app.utils.logging import get_logger
from app.ai.policy_engine import ALL_ACTIONS

logger = get_logger(__name__)

router = APIRouter(prefix="/api/policy", tags=["policy"])

class PolicyCopilotRequest(BaseModel):
    message: str

class PolicyCopilotResponse(BaseModel):
    success: bool
    policy: dict
    agent_message: str

SYSTEM_PROMPT = f"""You are the ReviveAI Policy Co-Pilot. 
Your job is to translate a merchant's natural language request into a strict JSON payload that updates their recovery policy.

The current available actions are: {', '.join(ALL_ACTIONS)}

You must return exactly ONE JSON object matching this schema, and NOTHING else (no prose, no markdown, no chain of thought).
{{
    "max_automated_amount": <integer, in paise (e.g., 500000 = ₹5000)>,
    "max_recovery_attempts": <integer>,
    "allowed_actions": "<comma separated string of allowed actions>",
    "high_risk_requires_approval": <boolean>,
    "approval_threshold": <integer, in paise>,
    "agent_message": "<A short, friendly message confirming the changes made>"
}}
"""

@router.get("/")
def get_policy(db: Session = Depends(get_db)):
    merchant = db.query(Merchant).first()
    if not merchant:
        raise HTTPException(status_code=400, detail="Demo merchant not found")
    policy = db.query(MerchantPolicy).filter(MerchantPolicy.merchant_id == merchant.id).first()
    if not policy:
        policy = MerchantPolicy(
            merchant_id=merchant.id,
            max_automated_amount=5000000,
            max_recovery_attempts=2,
            allowed_actions=",".join(ALL_ACTIONS),
            high_risk_requires_approval=True,
            approval_threshold=5000000
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
        
    return {
        "max_automated_amount": policy.max_automated_amount,
        "max_recovery_attempts": policy.max_recovery_attempts,
        "allowed_actions": policy.allowed_actions,
        "high_risk_requires_approval": policy.high_risk_requires_approval,
        "approval_threshold": policy.approval_threshold
    }

@router.post("/copilot", response_model=PolicyCopilotResponse)
def policy_copilot(req: PolicyCopilotRequest, db: Session = Depends(get_db)):
    settings = get_settings()
    merchant = db.query(Merchant).first()
    if not merchant:
        raise HTTPException(status_code=400, detail="Demo merchant not found")

    policy = db.query(MerchantPolicy).filter(MerchantPolicy.merchant_id == merchant.id).first()
    if not policy:
        # Create a default one if it doesn't exist
        policy = MerchantPolicy(
            merchant_id=merchant.id,
            max_automated_amount=5000000,
            max_recovery_attempts=2,
            allowed_actions=",".join(ALL_ACTIONS),
            high_risk_requires_approval=True,
            approval_threshold=5000000
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)

    current_policy_json = {
        "max_automated_amount": policy.max_automated_amount,
        "max_recovery_attempts": policy.max_recovery_attempts,
        "allowed_actions": policy.allowed_actions,
        "high_risk_requires_approval": policy.high_risk_requires_approval,
        "approval_threshold": policy.approval_threshold
    }

    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Key not set. Cannot use Co-Pilot.")

    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    
    user_prompt = f"""
Current Policy:
{json.dumps(current_policy_json, indent=2)}

Merchant Request: "{req.message}"

Update the policy based on the request and return the JSON.
    """

    try:
        generation_config = {"response_mime_type": "application/json"}
        model = genai.GenerativeModel(
            model_name=settings.AGENT_MODEL,
            system_instruction=SYSTEM_PROMPT,
            generation_config=generation_config
        )
        
        response = model.generate_content(user_prompt)
        text = response.text.strip()
        new_data = json.loads(text)
        
        agent_message = new_data.pop("agent_message", "Policy updated successfully.")

        # Update DB
        if "max_automated_amount" in new_data:
            policy.max_automated_amount = new_data["max_automated_amount"]
        if "max_recovery_attempts" in new_data:
            policy.max_recovery_attempts = new_data["max_recovery_attempts"]
        if "allowed_actions" in new_data:
            policy.allowed_actions = new_data["allowed_actions"]
        if "high_risk_requires_approval" in new_data:
            policy.high_risk_requires_approval = new_data["high_risk_requires_approval"]
        if "approval_threshold" in new_data:
            policy.approval_threshold = new_data["approval_threshold"]

        db.commit()
        db.refresh(policy)

        return PolicyCopilotResponse(
            success=True,
            policy={
                "max_automated_amount": policy.max_automated_amount,
                "max_recovery_attempts": policy.max_recovery_attempts,
                "allowed_actions": policy.allowed_actions,
                "high_risk_requires_approval": policy.high_risk_requires_approval,
                "approval_threshold": policy.approval_threshold
            },
            agent_message=agent_message
        )
    except Exception as e:
        logger.error(f"Policy copilot failed: {e}")
        # Send the exact error to the frontend so we can debug it immediately
        raise HTTPException(status_code=500, detail=f"AI Co-pilot failed: {str(e)}")
