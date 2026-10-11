import json
import uuid
import hashlib
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.tools.registry import registry
from app.models.approval import ApprovalRequest
from app.models.account import Account
from app.models.loan import LoanApplication
from app.services.audit_service import audit_service

def compute_payload_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

class RequestApprovalArgs(BaseModel):
    action_type: str = Field(..., description="Action to request: FREEZE_ACCOUNT, HIGH_VALUE_TRANSFER, OVERRIDE_LOAN, POLICY_EXCEPTION")
    payload: dict[str, Any] = Field(..., description="Action payload parameters")
    reason: str = Field(..., description="Detailed business and risk rationale")
    risk_level: str = Field(default="HIGH", description="LOW, MEDIUM, HIGH, CRITICAL")
    idempotency_key: str | None = Field(default=None, description="Unique key for duplicate prevention")

@registry.register(
    name="request_simulated_approval",
    description="Submit a sensitive simulated banking action to the Human-in-the-Loop Approval Queue.",
    permission="STATE_CHANGING_APPROVAL_REQUIRED",
    is_state_changing=True,
    args_schema=RequestApprovalArgs
)
def request_simulated_approval(
    db: Session,
    action_type: str,
    payload: dict[str, Any],
    reason: str,
    risk_level: str = "HIGH",
    idempotency_key: str | None = None
) -> dict[str, Any]:
    idem_key = idempotency_key or f"IDEM-{uuid.uuid4().hex[:12].upper()}"
    
    # Check if duplicate key exists
    existing = db.query(ApprovalRequest).filter(ApprovalRequest.idempotency_key == idem_key).first()
    if existing:
        return {
            "approval_id": existing.id,
            "status": existing.status,
            "message": "Approval request already exists with this idempotency key.",
            "payload_hash": existing.payload_hash
        }

    payload_hash = compute_payload_hash(payload)
    appr_id = f"APPR{uuid.uuid4().hex[:8].upper()}"
    req_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"

    approval = ApprovalRequest(
        id=appr_id,
        request_id=req_id,
        agent_name="MultiAgentSupervisor",
        action_type=action_type,
        payload=json.dumps(payload),
        payload_hash=payload_hash,
        idempotency_key=idem_key,
        risk_level=risk_level,
        reason=reason,
        status="PENDING"
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)

    audit_service.log_event(
        correlation_id=req_id,
        actor="SupervisorAgent",
        event_type="APPROVAL_REQUESTED",
        tool_name="request_simulated_approval",
        details={"approval_id": appr_id, "action_type": action_type, "payload_hash": payload_hash, "risk_level": risk_level},
        db=db
    )

    return {
        "approval_id": appr_id,
        "request_id": req_id,
        "action_type": action_type,
        "risk_level": risk_level,
        "payload_hash": payload_hash,
        "status": "PENDING",
        "message": "Action routed to Approval Center. Awaiting human manager confirmation."
    }

def execute_action_by_type(db: Session, action_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Execute the actual simulated database mutation upon approval."""
    if action_type == "FREEZE_ACCOUNT":
        acc_id = payload.get("account_id")
        account = db.query(Account).filter(Account.id == acc_id.upper()).first()
        if not account:
            raise ValueError(f"Account '{acc_id}' not found.")
        account.status = "FROZEN"
        db.commit()
        return {"status": "SUCCESS", "message": f"Account {account.id} successfully FROZEN in core ledger simulation."}
    
    elif action_type == "UNFREEZE_ACCOUNT":
        acc_id = payload.get("account_id")
        account = db.query(Account).filter(Account.id == acc_id.upper()).first()
        if not account:
            raise ValueError(f"Account '{acc_id}' not found.")
        account.status = "ACTIVE"
        db.commit()
        return {"status": "SUCCESS", "message": f"Account {account.id} restored to ACTIVE status."}

    elif action_type == "HIGH_VALUE_TRANSFER":
        acc_id = payload.get("account_id")
        amount = float(payload.get("amount", 0.0))
        account = db.query(Account).filter(Account.id == acc_id.upper()).first()
        if not account:
            raise ValueError(f"Account '{acc_id}' not found.")
        if account.balance < amount:
            raise ValueError(f"Insufficient funds: Balance ₹{account.balance:,.2f} < ₹{amount:,.2f}.")
        account.balance -= amount
        db.commit()
        return {
            "status": "SUCCESS",
            "message": f"Simulated high-value transfer of ₹{amount:,.2f} completed.",
            "remaining_balance": account.balance
        }

    elif action_type == "OVERRIDE_LOAN":
        loan_id = payload.get("loan_id")
        loan = db.query(LoanApplication).filter(LoanApplication.id == loan_id.upper()).first()
        if not loan:
            raise ValueError(f"Loan application '{loan_id}' not found.")
        loan.approval_status = "APPROVED"
        loan.assessment_notes += " [Exception override approved by management]."
        db.commit()
        return {"status": "SUCCESS", "message": f"Loan {loan.id} approved under committee policy override."}

    else:
        return {"status": "SUCCESS", "message": f"Simulated action '{action_type}' recorded and validated."}
