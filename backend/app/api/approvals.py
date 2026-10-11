import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.approval import ApprovalRequest
from app.models.user import User
from app.schemas.approvals import ApprovalDecision, ApprovalResponse
from app.tools.approval_tools import compute_payload_hash, execute_action_by_type
from app.services.audit_service import audit_service

router = APIRouter(prefix="/approvals", tags=["Approval Center"])

# Role-based authorization matrix for sensitive state-changing actions.
ACTION_ROLE_PERMISSIONS: dict[str, set[str]] = {
    "FREEZE_ACCOUNT": {"compliance_officer", "compliance_manager", "manager"},
    "UNFREEZE_ACCOUNT": {"compliance_officer", "compliance_manager", "manager"},
    "HIGH_VALUE_TRANSFER": {"compliance_manager", "manager"},
    "OVERRIDE_LOAN": {"compliance_manager", "manager"},
    "POLICY_EXCEPTION": {"compliance_officer", "compliance_manager", "manager"},
}
DEFAULT_ALLOWED_ROLES: set[str] = {"compliance_manager", "manager"}


def is_role_authorized(role: str | None, action_type: str) -> bool:
    allowed = ACTION_ROLE_PERMISSIONS.get(action_type, DEFAULT_ALLOWED_ROLES)
    return bool(role) and role.strip().lower() in allowed


def get_pending_approval_or_error(db: Session, approval_id: str) -> ApprovalRequest:
    """Fetch a PENDING approval, enforcing existence, status, and expiry."""
    approval = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id.upper()).first()
    if not approval:
        raise HTTPException(status_code=404, detail=f"Approval request '{approval_id}' not found.")

    if approval.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Cannot act on request with status '{approval.status}'.")

    # Expiry enforcement: auto-expire stale requests before any decision is applied.
    if approval.expires_at and approval.expires_at < datetime.utcnow():
        approval.status = "EXPIRED"
        approval.decision_reason = "Auto-expired: approval window elapsed before human decision."
        approval.decision_at = datetime.utcnow()
        approval.execution_result = json.dumps({"status": "EXPIRED_NOT_EXECUTED"})
        db.commit()
        audit_service.log_event(
            correlation_id=approval.request_id,
            actor="System",
            event_type="APPROVAL_EXPIRED",
            tool_name="expiry_enforcement",
            details={"approval_id": approval.id, "action_type": approval.action_type, "expires_at": approval.expires_at.isoformat()},
            status="ERROR",
            db=db
        )
        raise HTTPException(status_code=410, detail="Approval request has expired and can no longer be actioned.")

    return approval

@router.get("")
def list_approvals(
    status: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(ApprovalRequest)
    if status:
        query = query.filter(ApprovalRequest.status == status.upper())

    total = query.count()
    items = query.order_by(ApprovalRequest.created_at.desc()).limit(limit).all()

    return {
        "total": total,
        "approvals": [
            {
                "id": a.id,
                "request_id": a.request_id,
                "agent_name": a.agent_name,
                "action_type": a.action_type,
                "payload": json.loads(a.payload),
                "payload_hash": a.payload_hash,
                "idempotency_key": a.idempotency_key,
                "risk_level": a.risk_level,
                "reason": a.reason,
                "status": a.status,
                "decision_by": a.decision_by,
                "decision_reason": a.decision_reason,
                "decision_at": a.decision_at.isoformat() if a.decision_at else None,
                "execution_result": json.loads(a.execution_result) if a.execution_result else None,
                "expires_at": a.expires_at.isoformat(),
                "created_at": a.created_at.isoformat()
            }
            for a in items
        ]
    }

@router.post("/{approval_id}/approve")
def approve_request(
    approval_id: str,
    decision: ApprovalDecision,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    approval = get_pending_approval_or_error(db, approval_id)

    # Cryptographic Hash & Tamper Validation
    payload_dict = json.loads(approval.payload)
    recalculated_hash = compute_payload_hash(payload_dict)
    if recalculated_hash != approval.payload_hash:
        audit_service.log_event(
            correlation_id=approval.request_id,
            actor=user.username,
            event_type="APPROVAL_TAMPER_DETECTED",
            tool_name="approve_request",
            details={"approval_id": approval.id, "error": "Payload hash mismatch"},
            status="ERROR",
            db=db
        )
        raise HTTPException(status_code=400, detail="Security violation: Action payload hash does not match stored snapshot.")

    # Role-based authorization: only privileged roles may approve sensitive actions.
    if not is_role_authorized(user.role, approval.action_type):
        audit_service.log_event(
            correlation_id=approval.request_id,
            actor=user.username,
            event_type="APPROVAL_PERMISSION_DENIED",
            tool_name="approve_request",
            details={"approval_id": approval.id, "action_type": approval.action_type, "role": user.role},
            status="ERROR",
            db=db
        )
        raise HTTPException(
            status_code=403,
            detail=f"Role '{user.role}' is not authorized to approve action '{approval.action_type}'."
        )

    # Execute simulated state-changing action
    try:
        execution_res = execute_action_by_type(db, approval.action_type, payload_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")

    approval.status = "APPROVED"
    approval.decision_by = user.role
    approval.decision_reason = decision.decision_reason
    approval.decision_at = datetime.utcnow()
    approval.execution_result = json.dumps(execution_res)
    db.commit()

    audit_service.log_event(
        correlation_id=approval.request_id,
        actor=user.username,
        event_type="APPROVAL_DECIDED",
        tool_name="approve_request",
        details={"approval_id": approval.id, "decision": "APPROVED", "result": execution_res},
        status="SUCCESS",
        db=db
    )

    return {
        "approval_id": approval.id,
        "status": "APPROVED",
        "decision_by": approval.decision_by,
        "execution_result": execution_res,
        "message": f"Action '{approval.action_type}' successfully approved and executed."
    }

@router.post("/{approval_id}/reject")
def reject_request(
    approval_id: str,
    decision: ApprovalDecision,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    approval = get_pending_approval_or_error(db, approval_id)

    approval.status = "REJECTED"
    approval.decision_by = user.role
    approval.decision_reason = decision.decision_reason
    approval.decision_at = datetime.utcnow()
    approval.execution_result = json.dumps({"status": "REJECTED_BY_APPROVER"})
    db.commit()

    audit_service.log_event(
        correlation_id=approval.request_id,
        actor=user.username,
        event_type="APPROVAL_DECIDED",
        tool_name="reject_request",
        details={"approval_id": approval.id, "decision": "REJECTED", "reason": decision.decision_reason},
        status="REJECTED",
        db=db
    )

    return {
        "approval_id": approval.id,
        "status": "REJECTED",
        "decision_by": approval.decision_by,
        "message": "Action rejected by human approver."
    }
