import pytest
from app.database import get_task_session
from app.agents.customer_agent import customer_agent
from app.agents.fraud_agent import fraud_agent
from app.agents.credit_agent import credit_agent
from app.agents.compliance_agent import compliance_agent
from app.agents.investigation_agent import investigation_agent
from app.schemas.agents import AgentResult

def test_customer_agent_task_execution():
    db = get_task_session()
    try:
        res: AgentResult = customer_agent.execute_task(
            action="get_profile",
            arguments={"customer_id": "CUST1001"},
            correlation_id="TEST-CORR-01",
            db=db
        )
        assert res.agent_name == "CustomerAgent"
        assert res.status == "success"
        assert res.data["customer_id"] == "CUST1001"
        assert len(res.tool_calls) == 1
        assert res.duration_ms > 0
    finally:
        db.close()

def test_fraud_agent_task_execution():
    db = get_task_session()
    try:
        res: AgentResult = fraud_agent.execute_task(
            action="analyze_transaction",
            arguments={"transaction_id": "TXN4008"},
            correlation_id="TEST-CORR-02",
            db=db
        )
        assert res.agent_name == "FraudAgent"
        assert res.status == "success"
        assert res.data["risk_level"] == "HIGH"
        assert len(res.tool_calls) == 1
    finally:
        db.close()

def test_credit_agent_task_execution():
    db = get_task_session()
    try:
        res: AgentResult = credit_agent.execute_task(
            action="evaluate_loan",
            arguments={"customer_id": "CUST1001", "amount": 500000.0, "tenure_months": 36},
            correlation_id="TEST-CORR-03",
            db=db
        )
        assert res.agent_name == "CreditAgent"
        assert res.status == "success"
        assert res.data["assessment_result"] == "ELIGIBLE"
    finally:
        db.close()

def test_compliance_agent_task_execution():
    db = get_task_session()
    try:
        res: AgentResult = compliance_agent.execute_task(
            action="check_kyc",
            arguments={"customer_id": "CUST1004"},
            correlation_id="TEST-CORR-04",
            db=db
        )
        assert res.agent_name == "ComplianceAgent"
        assert res.status == "success"
        assert res.data["kyc_status"] == "PENDING"
    finally:
        db.close()
