import pytest
from app.agents.supervisor import supervisor

@pytest.mark.asyncio
async def test_assistant_customer_balance_query():
    resp = await supervisor.process_request("Show customer CUST1001's account balance.")
    assert resp.status == "completed"
    assert resp.intent == "customer_account_inquiry"
    assert "CustomerAgent" in resp.agents_involved
    assert "₹" in resp.answer
    assert resp.correlation_id.startswith("REQ-")

@pytest.mark.asyncio
async def test_assistant_explain_flagged_transaction():
    resp = await supervisor.process_request("Explain why transaction TXN4008 was flagged.")
    assert resp.status == "completed"
    assert resp.intent == "explain_flagged_transaction"
    assert "FraudAgent" in resp.agents_involved
    assert "TXN4008" in resp.answer

@pytest.mark.asyncio
async def test_assistant_missing_customer_clarification():
    # Prompt without customer ID asks for clarification
    resp = await supervisor.process_request("Show customer account balance.")
    assert resp.status == "clarification_needed"
    assert "CUST1001" in resp.answer

@pytest.mark.asyncio
async def test_assistant_multi_agent_combined_investigation():
    resp = await supervisor.process_request("Investigate CUST1001, summarize monthly spending, identify suspicious transactions, and check loan eligibility.")
    assert resp.status == "completed"
    assert resp.intent == "combined_investigation"
    # Verify multiple specialized agents coordinated
    assert "CustomerAgent" in resp.agents_involved
    assert "FraudAgent" in resp.agents_involved
    assert "CreditAgent" in resp.agents_involved
    assert "InvestigationAgent" in resp.agents_involved
    assert "360 Multi-Agent Investigation Report" in resp.answer

@pytest.mark.asyncio
async def test_assistant_fallback_mode_label():
    resp = await supervisor.process_request("Show the latest five transactions for CUST1002.")
    assert resp.status == "completed"
    assert resp.execution_mode == "deterministic_fallback"
    assert len(resp.trace) >= 3
