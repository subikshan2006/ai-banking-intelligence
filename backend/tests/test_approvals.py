import json
from app.database import get_task_session
from app.models.approval import ApprovalRequest
from app.models.account import Account
from app.tools.approval_tools import compute_payload_hash

def test_list_approvals(client):
    response = client.get("/api/approvals")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["approvals"]) >= 1

def test_approve_pending_freeze_account(client):
    db = get_task_session()
    try:
        # Create a fresh pending approval request
        payload = {"account_id": "ACC2003", "customer_id": "CUST1002"}
        p_hash = compute_payload_hash(payload)
        appr = ApprovalRequest(
            id="APPR-TEST-01",
            request_id="REQ-TEST-APPR-01",
            agent_name="FraudAgent",
            action_type="FREEZE_ACCOUNT",
            payload=json.dumps(payload),
            payload_hash=p_hash,
            idempotency_key="IDEM-TEST-FREEZE-ACC2003",
            risk_level="HIGH",
            reason="Test freeze",
            status="PENDING"
        )
        db.merge(appr)
        db.commit()

        # Approve it via endpoint
        response = client.post(
            f"/api/approvals/{appr.id}/approve",
            json={"decision": "APPROVED", "decision_reason": "Verified suspicious activity with cardholder", "approver_role": "compliance_manager"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "APPROVED"

        # Verify account was actually FROZEN in database
        acc = db.query(Account).filter(Account.id == "ACC2003").first()
        assert acc.status == "FROZEN"
    finally:
        db.close()

def test_tamper_payload_hash_rejected(client):
    db = get_task_session()
    try:
        payload = {"account_id": "ACC2004", "customer_id": "CUST1003"}
        # Deliberately store wrong hash
        appr = ApprovalRequest(
            id="APPR-TAMPER-01",
            request_id="REQ-TAMPER-01",
            agent_name="FraudAgent",
            action_type="FREEZE_ACCOUNT",
            payload=json.dumps(payload),
            payload_hash="invalid_tampered_hash_00000000000000000000000000000000000000",
            idempotency_key="IDEM-TAMPER-01",
            risk_level="HIGH",
            reason="Tampered request test",
            status="PENDING"
        )
        db.merge(appr)
        db.commit()

        response = client.post(
            f"/api/approvals/{appr.id}/approve",
            json={"decision": "APPROVED", "decision_reason": "Attempting approval", "approver_role": "manager"}
        )
        assert response.status_code == 400
        assert "hash does not match" in response.json()["detail"].lower()
    finally:
        db.close()
