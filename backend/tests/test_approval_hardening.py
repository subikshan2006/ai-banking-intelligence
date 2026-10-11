import json
from datetime import datetime, timedelta
from app.database import get_task_session
from app.models.approval import ApprovalRequest
from app.tools.approval_tools import compute_payload_hash


def test_expired_approval_cannot_be_approved(client, auth_headers):
    db = get_task_session()
    try:
        payload = {"account_id": "ACC2006", "customer_id": "CUST1004"}
        appr = ApprovalRequest(
            id="APPR-EXP-01",
            request_id="REQ-EXP-01",
            agent_name="FraudAgent",
            action_type="FREEZE_ACCOUNT",
            payload=json.dumps(payload),
            payload_hash=compute_payload_hash(payload),
            idempotency_key="IDEM-EXP-01",
            risk_level="HIGH",
            reason="Expiry enforcement test",
            status="PENDING",
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        db.merge(appr)
        db.commit()

        response = client.post(
            "/api/approvals/APPR-EXP-01/approve",
            json={
                "decision": "APPROVED",
                "decision_reason": "Late approval attempt",
                "approver_role": "compliance_manager",
            },
            headers=auth_headers("manager"),
        )
        assert response.status_code == 410

        refreshed = db.query(ApprovalRequest).filter(ApprovalRequest.id == "APPR-EXP-01").first()
        assert refreshed.status == "EXPIRED"
    finally:
        db.close()


def test_unauthorized_role_cannot_approve(client, auth_headers):
    db = get_task_session()
    try:
        payload = {"account_id": "ACC2003", "customer_id": "CUST1002"}
        appr = ApprovalRequest(
            id="APPR-ROLE-01",
            request_id="REQ-ROLE-01",
            agent_name="FraudAgent",
            action_type="FREEZE_ACCOUNT",
            payload=json.dumps(payload),
            payload_hash=compute_payload_hash(payload),
            idempotency_key="IDEM-ROLE-01",
            risk_level="HIGH",
            reason="Role permission test",
            status="PENDING",
        )
        db.merge(appr)
        db.commit()

        denied = client.post(
            "/api/approvals/APPR-ROLE-01/approve",
            json={
                "decision": "APPROVED",
                "decision_reason": "Risk analyst escalation attempt",
                "approver_role": "risk_analyst",
            },
            headers=auth_headers("risk_analyst"),
        )
        assert denied.status_code == 403

        allowed = client.post(
            "/api/approvals/APPR-ROLE-01/approve",
            json={
                "decision": "APPROVED",
                "decision_reason": "Compliance officer authorized freeze",
                "approver_role": "compliance_officer",
            },
            headers=auth_headers("compliance_officer"),
        )
        assert allowed.status_code == 200
        assert allowed.json()["status"] == "APPROVED"
    finally:
        db.close()
