import json
import pytest
from app.agents.supervisor import supervisor
from app.services.llm_service import llm_service


@pytest.mark.asyncio
async def test_llm_proposed_plan_is_validated_and_used(monkeypatch):
    plan = {
        "tasks": [
            {
                "task_id": "T1",
                "agent_name": "CustomerAgent",
                "action": "get_balance",
                "arguments": {"customer_id": "CUST1001"},
                "dependencies": [],
            }
        ]
    }

    async def fake_generate(system_prompt, user_message, temperature=0.2, max_tokens=1000):
        if "workflow planner" in system_prompt:
            return json.dumps(plan)
        return None

    monkeypatch.setattr(llm_service, "is_configured", True)
    monkeypatch.setattr(llm_service, "generate_response", fake_generate)

    resp = await supervisor.process_request("Show customer CUST1001's account balance.")

    planning = [t for t in resp.trace if t.phase == "PLANNING"][0]
    assert planning.output_data["plan_source"] == "llm"
    assert resp.execution_mode == "llm"
    assert "CustomerAgent" in resp.agents_involved


@pytest.mark.asyncio
async def test_invalid_llm_plan_falls_back_to_deterministic(monkeypatch):
    bad_plan = {
        "tasks": [
            {
                "task_id": "T1",
                "agent_name": "HackerAgent",
                "action": "steal_funds",
                "arguments": {},
                "dependencies": [],
            }
        ]
    }

    async def fake_generate(system_prompt, user_message, temperature=0.2, max_tokens=1000):
        if "workflow planner" in system_prompt:
            return json.dumps(bad_plan)
        return None

    monkeypatch.setattr(llm_service, "is_configured", True)
    monkeypatch.setattr(llm_service, "generate_response", fake_generate)

    resp = await supervisor.process_request("Show customer CUST1001's account balance.")

    planning = [t for t in resp.trace if t.phase == "PLANNING"][0]
    assert planning.output_data["plan_source"] == "deterministic"
    assert resp.intent == "customer_account_inquiry"
    assert "CustomerAgent" in resp.agents_involved


@pytest.mark.asyncio
async def test_llm_answer_synthesis_replaces_deterministic(monkeypatch):
    async def fake_generate(system_prompt, user_message, temperature=0.2, max_tokens=1000):
        if "workflow planner" in system_prompt:
            return None
        return "LLM SYNTHESIZED ANSWER"

    monkeypatch.setattr(llm_service, "is_configured", True)
    monkeypatch.setattr(llm_service, "generate_response", fake_generate)

    resp = await supervisor.process_request("Show customer CUST1001's account balance.")

    assert resp.execution_mode == "llm"
    assert resp.answer == "LLM SYNTHESIZED ANSWER"
