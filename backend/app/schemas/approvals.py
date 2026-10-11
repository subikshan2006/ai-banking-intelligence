from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field

class ApprovalCreate(BaseModel):
    agent_name: str
    action_type: str
    payload: dict[str, Any]
    reason: str
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "HIGH"
    idempotency_key: str | None = None

class ApprovalDecision(BaseModel):
    decision: Literal["APPROVED", "REJECTED"]
    decision_reason: str = Field(..., min_length=3)
    approver_role: str = "compliance_manager"

class ApprovalResponse(BaseModel):
    id: str
    request_id: str
    agent_name: str
    action_type: str
    payload: dict[str, Any]
    payload_hash: str
    idempotency_key: str
    risk_level: str
    reason: str
    status: str
    decision_by: str | None = None
    decision_reason: str | None = None
    decision_at: datetime | None = None
    execution_result: dict[str, Any] | None = None
    expires_at: datetime
    created_at: datetime
