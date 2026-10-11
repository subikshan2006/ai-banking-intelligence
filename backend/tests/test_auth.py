import json
from app.database import get_task_session
from app.models.approval import ApprovalRequest
from app.tools.approval_tools import compute_payload_hash


def test_login_success(client):
    response = client.post("/api/auth/login", json={"username": "manager", "password": "Manager@123"})
    assert response.status_code == 200
    body = response.json()
    assert body["token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["username"] == "manager"
    assert body["user"]["role"] == "manager"


def test_login_failure(client):
    response = client.post("/api/auth/login", json={"username": "manager", "password": "wrong-password"})
    assert response.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers("risk_analyst"))
    assert response.status_code == 200
    assert response.json()["role"] == "risk_analyst"


def test_me_requires_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_approve_requires_authentication(client):
    db = get_task_session()
    try:
        payload = {"account_id": "ACC2005", "customer_id": "CUST1003"}
        appr = ApprovalRequest(
            id="APPR-AUTH-01",
            request_id="REQ-AUTH-01",
            agent_name="FraudAgent",
            action_type="FREEZE_ACCOUNT",
            payload=json.dumps(payload),
            payload_hash=compute_payload_hash(payload),
            idempotency_key="IDEM-AUTH-01",
            risk_level="HIGH",
            reason="Requires auth test",
            status="PENDING",
        )
        db.merge(appr)
        db.commit()

        response = client.post(
            "/api/approvals/APPR-AUTH-01/approve",
            json={"decision": "APPROVED", "decision_reason": "No token present"},
        )
        assert response.status_code == 401
    finally:
        db.close()


def test_risk_analyst_cannot_approve_high_value_transfer(client, auth_headers):
    db = get_task_session()
    try:
        payload = {"account_id": "ACC2012", "amount": 100000.0, "beneficiary": "Test Beneficiary"}
        appr = ApprovalRequest(
            id="APPR-ROLE-02",
            request_id="REQ-ROLE-02",
            agent_name="CustomerAgent",
            action_type="HIGH_VALUE_TRANSFER",
            payload=json.dumps(payload),
            payload_hash=compute_payload_hash(payload),
            idempotency_key="IDEM-ROLE-02",
            risk_level="HIGH",
            reason="Role boundary test",
            status="PENDING",
        )
        db.merge(appr)
        db.commit()

        denied = client.post(
            "/api/approvals/APPR-ROLE-02/approve",
            json={"decision": "APPROVED", "decision_reason": "Risk analyst tries transfer"},
            headers=auth_headers("risk_analyst"),
        )
        assert denied.status_code == 403

        allowed = client.post(
            "/api/approvals/APPR-ROLE-02/approve",
            json={"decision": "APPROVED", "decision_reason": "Manager authorizes transfer"},
            headers=auth_headers("manager"),
        )
        assert allowed.status_code == 200
        assert allowed.json()["status"] == "APPROVED"
    finally:
        db.close()