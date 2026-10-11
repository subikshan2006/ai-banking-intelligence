import time
import uuid
import json
import inspect
import logging
from datetime import datetime
from typing import Any
from sqlalchemy.orm import Session

from app.config import settings
from app.schemas.agents import AgentResult, TaskStep, WorkflowPlan, ToolCallRecord
from app.schemas.chat import ChatResponse, ExecutionTraceItem
from app.services.intent_router import intent_router, ParsedIntent
from app.services.llm_service import llm_service
from app.services.audit_service import audit_service
from app.database import get_task_session

# Import specialized agents
from app.agents.customer_agent import customer_agent
from app.agents.transaction_agent import transaction_agent
from app.agents.fraud_agent import fraud_agent
from app.agents.credit_agent import credit_agent
from app.agents.compliance_agent import compliance_agent
from app.agents.investigation_agent import investigation_agent
from app.agents.notification_agent import notification_agent
from app.services.knowledge_service import knowledge_service

logger = logging.getLogger(__name__)

class SupervisorAgent:
    """Central orchestrator coordinating specialized banking agents and synthesizing grounded responses."""

    def __init__(self):
        self.agents_map = {
            "CustomerAgent": customer_agent,
            "TransactionAgent": transaction_agent,
            "FraudAgent": fraud_agent,
            "CreditAgent": credit_agent,
            "ComplianceAgent": compliance_agent,
            "InvestigationAgent": investigation_agent,
            "NotificationAgent": notification_agent,
        }

    async def process_request(self, message: str, correlation_id: str | None = None, demo_role: str = "manager") -> ChatResponse:
        corr_id = correlation_id or f"REQ-{uuid.uuid4().hex[:8].upper()}"
        start_time = time.perf_counter()
        trace: list[ExecutionTraceItem] = []
        all_tool_calls: list[ToolCallRecord] = []
        errors: list[str] = []
        agents_involved: list[str] = []

        # Step 1: Intent Classification
        step_start = time.perf_counter()
        parsed: ParsedIntent = intent_router.parse_message(message)
        trace.append(ExecutionTraceItem(
            step_id=f"STEP-{len(trace)+1}",
            phase="INTENT_CLASSIFICATION",
            agent_name="SupervisorAgent",
            input_data={"message": message},
            output_data={"intent": parsed.intent, "entities": parsed.entities, "confidence": parsed.confidence},
            status="SUCCESS",
            duration_ms=round((time.perf_counter() - step_start) * 1000.0, 2),
            timestamp=datetime.utcnow().isoformat()
        ))

        # Check if clarification is required
        if parsed.is_clarification_needed and parsed.clarification_prompt:
            return ChatResponse(
                correlation_id=corr_id,
                intent=parsed.intent,
                execution_mode="deterministic_fallback",
                status="clarification_needed",
                answer=parsed.clarification_prompt,
                agents_involved=["SupervisorAgent"],
                tool_results=[],
                trace=trace,
                errors=[],
                structured_data={"clarification_prompt": parsed.clarification_prompt}
            )

        # Step 2: Build Workflow Plan (LLM-proposed & validated when configured, else deterministic)
        plan_start = time.perf_counter()
        tasks = await self._propose_plan_via_llm(message, corr_id)
        plan_source = "llm" if tasks is not None else "deterministic"
        if tasks is None:
            tasks = self._build_workflow_plan(parsed, corr_id)
        trace.append(ExecutionTraceItem(
            step_id=f"STEP-{len(trace)+1}",
            phase="PLANNING",
            agent_name="SupervisorAgent",
            input_data={"intent": parsed.intent, "entities": parsed.entities, "llm_configured": llm_service.is_configured},
            output_data={"plan_source": plan_source, "task_count": len(tasks), "tasks": [f"{t.task_id} -> {t.agent_name}.{t.action}" for t in tasks]},
            status="SUCCESS",
            duration_ms=round((time.perf_counter() - plan_start) * 1000.0, 2),
            timestamp=datetime.utcnow().isoformat()
        ))

        # Step 3: Execute Tasks according to DAG dependencies
        results_by_task: dict[str, AgentResult] = {}
        for task in tasks:
            # Validate dependencies
            deps_met = all(results_by_task.get(dep, None) and results_by_task[dep].status != "error" for dep in task.dependencies)
            if not deps_met:
                task.status = "skipped"
                trace.append(ExecutionTraceItem(
                    step_id=f"STEP-{len(trace)+1}",
                    phase="AGENT_EXECUTION",
                    agent_name=task.agent_name,
                    input_data=task.arguments,
                    output_data={"reason": "Prerequisite task failed or skipped"},
                    status="SKIPPED",
                    duration_ms=0.0,
                    timestamp=datetime.utcnow().isoformat()
                ))
                continue

            agent = self.agents_map.get(task.agent_name)
            if not agent:
                task.status = "failed"
                errors.append(f"Agent '{task.agent_name}' not recognized.")
                continue

            if task.agent_name not in agents_involved:
                agents_involved.append(task.agent_name)

            # Inject outputs from dependent tasks if needed (e.g. for InvestigationAgent)
            task_args = dict(task.arguments)
            if task.agent_name == "InvestigationAgent" and task.action == "synthesize_report":
                findings = {}
                for dep_id in task.dependencies:
                    dep_res = results_by_task.get(dep_id)
                    if dep_res and dep_res.status == "success":
                        key = dep_id.split("-")[0].lower()
                        findings[key] = dep_res.data
                task_args["findings"] = findings

            # Execute Agent with task-isolated session
            task_db = get_task_session()
            task_exec_start = time.perf_counter()
            try:
                res: AgentResult = agent.execute_task(
                    action=task.action,
                    arguments=task_args,
                    correlation_id=corr_id,
                    db=task_db
                )
                results_by_task[task.task_id] = res
                all_tool_calls.extend(res.tool_calls)
                if res.errors:
                    errors.extend(res.errors)

                trace.append(ExecutionTraceItem(
                    step_id=f"STEP-{len(trace)+1}",
                    phase="AGENT_EXECUTION",
                    agent_name=task.agent_name,
                    input_data=task_args,
                    output_data=res.data,
                    status="SUCCESS" if res.status == "success" else "ERROR",
                    duration_ms=res.duration_ms,
                    timestamp=datetime.utcnow().isoformat()
                ))
            except Exception as task_err:
                logger.error(f"Task {task.task_id} failed: {task_err}")
                errors.append(str(task_err))
                trace.append(ExecutionTraceItem(
                    step_id=f"STEP-{len(trace)+1}",
                    phase="AGENT_EXECUTION",
                    agent_name=task.agent_name,
                    input_data=task_args,
                    output_data={"error": str(task_err)},
                    status="ERROR",
                    duration_ms=round((time.perf_counter() - task_exec_start) * 1000.0, 2),
                    timestamp=datetime.utcnow().isoformat()
                ))
            finally:
                task_db.close()

        # Step 4: Synthesize Final Grounded Answer
        agg_start = time.perf_counter()
        final_answer, structured_out = self._aggregate_results(
            intent=parsed.intent,
            entities=parsed.entities,
            results=results_by_task,
            correlation_id=corr_id,
            errors=errors
        )
        trace.append(ExecutionTraceItem(
            step_id=f"STEP-{len(trace)+1}",
            phase="AGGREGATION",
            agent_name="SupervisorAgent",
            input_data={"task_results_count": len(results_by_task)},
            output_data={"answer_length": len(final_answer)},
            status="SUCCESS",
            duration_ms=round((time.perf_counter() - agg_start) * 1000.0, 2),
            timestamp=datetime.utcnow().isoformat()
        ))

        # Log completion audit event
        audit_service.log_event(
            correlation_id=corr_id,
            actor="SupervisorAgent",
            event_type="WORKFLOW_COMPLETED",
            tool_name="multi_agent_orchestration",
            details={
                "intent": parsed.intent,
                "agents_involved": agents_involved,
                "tool_calls_count": len(all_tool_calls),
                "errors_count": len(errors)
            },
            duration_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
            status="SUCCESS" if not errors else "PARTIAL_SUCCESS"
        )

        # Step 5: Optional LLM natural-language synthesis over grounded tool results
        execution_mode = "llm" if plan_source == "llm" else "deterministic_fallback"
        synth_start = time.perf_counter()
        llm_answer = await self._synthesize_answer_via_llm(message=message, intent=parsed.intent, structured=structured_out)
        if llm_answer:
            final_answer = llm_answer
            execution_mode = "llm"
        trace.append(ExecutionTraceItem(
            step_id=f"STEP-{len(trace)+1}",
            phase="AGGREGATION",
            agent_name="SupervisorAgent",
            input_data={"llm_configured": llm_service.is_configured, "structured_keys": list(structured_out.keys())},
            output_data={"answer_source": "llm" if llm_answer else "deterministic", "execution_mode": execution_mode},
            status="SUCCESS",
            duration_ms=round((time.perf_counter() - synth_start) * 1000.0, 2),
            timestamp=datetime.utcnow().isoformat()
        ))

        return ChatResponse(
            correlation_id=corr_id,
            intent=parsed.intent,
            execution_mode=execution_mode,
            status="completed" if not errors else "failed",
            answer=final_answer,
            agents_involved=agents_involved,
            tool_results=all_tool_calls,
            trace=trace,
            errors=errors,
            structured_data=structured_out
        )

    def _agent_action_map(self) -> dict[str, list[str]]:
        """Enumerate the callable actions each registered agent exposes (for plan validation)."""
        mapping: dict[str, list[str]] = {}
        for name, agent in self.agents_map.items():
            actions = [
                member for member, _ in inspect.getmembers(agent, predicate=inspect.ismethod)
                if not member.startswith("_") and member not in ("execute_tool", "execute_task")
            ]
            mapping[name] = sorted(actions)
        return mapping

    async def _propose_plan_via_llm(self, message: str, correlation_id: str) -> list[TaskStep] | None:
        """Ask the LLM for a JSON execution plan for complex requests; validate before use."""
        if not llm_service.is_configured:
            return None

        action_map = self._agent_action_map()
        system_prompt = (
            "You are a banking multi-agent workflow planner. Propose a JSON execution plan using ONLY "
            "the agents and actions listed below. Reply with strict JSON of the form "
            '{"tasks":[{"task_id":"T1","agent_name":"...","action":"...","arguments":{...},"dependencies":["T1"]}]}. '
            f"Available agents/actions: {json.dumps(action_map)}. "
            f"Use at most {settings.MAX_WORKFLOW_STEPS} tasks. Reference only task_ids declared earlier. "
            "Do not include commentary, markdown, or code fences."
        )
        raw = await llm_service.generate_response(system_prompt, message, temperature=0.0, max_tokens=800)
        return self._validate_llm_plan(raw, action_map)

    def _validate_llm_plan(self, raw: str | None, action_map: dict[str, list[str]]) -> list[TaskStep] | None:
        """Validate an LLM-proposed plan against the agent/action allow-list. Returns None if invalid."""
        if not raw or not raw.strip():
            return None

        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`").strip()
            if text.lower().startswith("json"):
                text = text[4:].strip()

        try:
            data = json.loads(text)
        except Exception:
            logger.warning("LLM plan rejected: response was not valid JSON.")
            return None

        tasks_raw = data.get("tasks") if isinstance(data, dict) else None
        if not isinstance(tasks_raw, list) or not tasks_raw:
            return None
        if len(tasks_raw) > settings.MAX_WORKFLOW_STEPS:
            logger.warning("LLM plan rejected: exceeds MAX_WORKFLOW_STEPS.")
            return None

        seen_ids: set[str] = set()
        tasks: list[TaskStep] = []
        for item in tasks_raw:
            if not isinstance(item, dict):
                return None
            task_id = item.get("task_id")
            agent_name = item.get("agent_name")
            action = item.get("action")
            arguments = item.get("arguments", {}) or {}
            dependencies = item.get("dependencies", []) or []

            if not task_id or task_id in seen_ids:
                return None
            if agent_name not in action_map or action not in action_map[agent_name]:
                logger.warning(f"LLM plan rejected: unsupported agent/action '{agent_name}.{action}'.")
                return None
            if not isinstance(dependencies, list) or any(dep not in seen_ids for dep in dependencies):
                return None
            if not isinstance(arguments, dict):
                return None

            seen_ids.add(task_id)
            tasks.append(TaskStep(
                task_id=task_id,
                agent_name=agent_name,
                action=action,
                arguments=arguments,
                dependencies=dependencies
            ))

        return tasks

    async def _synthesize_answer_via_llm(self, message: str, intent: str, structured: dict[str, Any]) -> str | None:
        """Produce a grounded natural-language answer from structured tool results, or None to fall back."""
        if not llm_service.is_configured or not structured:
            return None

        system_prompt = (
            "You are a professional banking operations assistant. Using ONLY the structured tool results "
            "provided, answer the user's request clearly in Markdown. Never invent customers, accounts, "
            "amounts, or policies. Omit fields that are absent. Be concise and factual."
        )
        context = json.dumps(structured, default=str)[:8000]
        user_message = f"User request: {message}\n\nStructured tool results (JSON):\n{context}"

        answer = await llm_service.generate_response(system_prompt, user_message, temperature=0.2, max_tokens=1000)
        if not answer or not answer.strip():
            return None
        answer = answer.strip()
        if len(answer) > 12000:
            logger.warning("LLM answer rejected: exceeds maximum length.")
            return None
        return answer

    def _build_workflow_plan(self, parsed: ParsedIntent, correlation_id: str) -> list[TaskStep]:
        intent = parsed.intent
        ent = parsed.entities
        tasks: list[TaskStep] = []

        if intent == "customer_account_inquiry":
            tasks.append(TaskStep(
                task_id="CUST-1", agent_name="CustomerAgent",
                action="get_balance" if "account_id" in ent else "customer_360",
                arguments=ent
            ))

        elif intent == "transaction_history":
            tasks.append(TaskStep(
                task_id="TXN-1", agent_name="CustomerAgent",
                action="get_recent_transactions",
                arguments=ent
            ))

        elif intent == "spending_analysis":
            tasks.append(TaskStep(
                task_id="SPEND-1", agent_name="CustomerAgent",
                action="get_spending_summary",
                arguments=ent
            ))
            tasks.append(TaskStep(
                task_id="SPEND-2", agent_name="TransactionAgent",
                action="analyze_categories",
                arguments=ent,
                dependencies=["SPEND-1"]
            ))

        elif intent == "fraud_investigation":
            tasks.append(TaskStep(
                task_id="FRAUD-1", agent_name="FraudAgent",
                action="analyze_customer",
                arguments=ent
            ))

        elif intent == "explain_flagged_transaction" or intent == "analyze_single_transaction":
            tasks.append(TaskStep(
                task_id="FRAUD-TXN-1", agent_name="FraudAgent",
                action="explain_flagged",
                arguments=ent
            ))

        elif intent == "loan_eligibility":
            tasks.append(TaskStep(
                task_id="LOAN-1", agent_name="CreditAgent",
                action="evaluate_loan",
                arguments=ent
            ))

        elif intent == "compare_loan_scenarios":
            scenarios = []
            for idx, a in enumerate(ent.get("compare_amounts", [300000.0, 500000.0])):
                scenarios.append({
                    "principal": a,
                    "tenure_months": ent.get("tenure_months", 24),
                    "interest_rate": 10.5
                })
            tasks.append(TaskStep(
                task_id="COMPARE-1", agent_name="CreditAgent",
                action="compare_scenarios",
                arguments={"scenarios": scenarios}
            ))

        elif intent == "pending_loans":
            tasks.append(TaskStep(
                task_id="LOAN-PENDING-1", agent_name="CreditAgent",
                action="get_applications",
                arguments=ent
            ))

        elif intent == "kyc_status":
            tasks.append(TaskStep(
                task_id="KYC-1", agent_name="ComplianceAgent",
                action="check_kyc",
                arguments=ent
            ))

        elif intent == "banking_policy":
            # Direct policy query using knowledge service
            pass

        elif intent == "combined_investigation":
            # Multi-agent 360 investigation workflow
            tasks.append(TaskStep(
                task_id="CUST-1", agent_name="CustomerAgent",
                action="customer_360",
                arguments={"customer_id": ent.get("customer_id")}
            ))
            tasks.append(TaskStep(
                task_id="SPEND-1", agent_name="TransactionAgent",
                action="analyze_categories",
                arguments={"customer_id": ent.get("customer_id")},
                dependencies=["CUST-1"]
            ))
            tasks.append(TaskStep(
                task_id="FRAUD-1", agent_name="FraudAgent",
                action="analyze_customer",
                arguments={"customer_id": ent.get("customer_id")},
                dependencies=["CUST-1"]
            ))
            tasks.append(TaskStep(
                task_id="CREDIT-1", agent_name="CreditAgent",
                action="evaluate_loan",
                arguments={"customer_id": ent.get("customer_id"), "amount": ent.get("amount", 500000.0), "tenure_months": ent.get("tenure_months", 36)},
                dependencies=["CUST-1"]
            ))
            tasks.append(TaskStep(
                task_id="COMPLIANCE-1", agent_name="ComplianceAgent",
                action="check_kyc",
                arguments={"customer_id": ent.get("customer_id")},
                dependencies=["CUST-1"]
            ))
            tasks.append(TaskStep(
                task_id="INV-1", agent_name="InvestigationAgent",
                action="synthesize_report",
                arguments={"customer_id": ent.get("customer_id")},
                dependencies=["CUST-1", "SPEND-1", "FRAUD-1", "CREDIT-1", "COMPLIANCE-1"]
            ))

        return tasks

    def _aggregate_results(
        self,
        intent: str,
        entities: dict[str, Any],
        results: dict[str, AgentResult],
        correlation_id: str,
        errors: list[str]
    ) -> tuple[str, dict[str, Any]]:
        structured: dict[str, Any] = {}

        if intent == "customer_account_inquiry":
            cust_res = results.get("CUST-1")
            if cust_res and cust_res.status == "success":
                data = cust_res.data
                structured = data
                if "balance" in data:
                    ans = f"### Account Balance for {data.get('account_id')}\n\n"
                    ans += f"- **Account Number**: `{data.get('masked_account_number')}`\n"
                    ans += f"- **Current Balance**: **₹{data.get('balance', 0):,.2f} {data.get('currency', 'INR')}**\n"
                    ans += f"- **Status**: `{data.get('status')}`"
                    return ans, structured
                elif "profile" in data:
                    p = data["profile"]
                    accs = data.get("accounts", [])
                    ans = f"### Customer Profile: {p.get('name')} ({p.get('customer_id')})\n\n"
                    ans += f"- **City / Employer**: {p.get('city')} | {p.get('employer')}\n"
                    ans += f"- **KYC Status**: `{p.get('kyc_status')}` | **Risk Rating**: `{p.get('risk_rating')}`\n"
                    ans += f"- **Monthly Income**: ₹{p.get('monthly_income', 0):,.2f}\n\n"
                    ans += "#### Associated Accounts\n"
                    for a in accs:
                        ans += f"- **{a.get('account_id')}** ({a.get('account_type')}): **₹{a.get('balance', 0):,.2f}** (`{a.get('account_number')}`)\n"
                    return ans, structured

        elif intent == "transaction_history":
            tx_res = results.get("TXN-1")
            if tx_res and tx_res.status == "success":
                txs = tx_res.data.get("transactions", [])
                structured = tx_res.data
                ans = f"### Recent Transactions for {entities.get('customer_id')}\n\n"
                if not txs:
                    ans += "No recent transactions found."
                else:
                    ans += "| ID | Category | Merchant | Amount | Type | Status |\n"
                    ans += "|---|---|---|---|---|---|\n"
                    for t in txs:
                        ans += f"| `{t['transaction_id']}` | {t['category']} | {t['merchant_name']} | ₹{t['amount']:,.2f} | {t['txn_type']} | `{t['status']}` |\n"
                return ans, structured

        elif intent == "spending_analysis":
            sp_res = results.get("SPEND-1")
            cat_res = results.get("SPEND-2")
            if sp_res and sp_res.status == "success":
                data = sp_res.data
                structured = data
                ans = f"### Spending Summary for {entities.get('customer_id')} (Last {data.get('period_days', 30)} Days)\n\n"
                ans += f"- **Total Inflow (Credits)**: ₹{data.get('total_inflow', 0):,.2f}\n"
                ans += f"- **Total Outflow (Debits)**: ₹{data.get('total_outflow', 0):,.2f}\n"
                ans += f"- **Net Cash Flow**: **₹{data.get('net_cashflow', 0):,.2f}**\n\n"
                ans += "#### Spending by Category\n"
                for c in data.get("categories", []):
                    ans += f"- **{c['category']}**: ₹{c['total_amount']:,.2f} ({c['percentage']}% of spend)\n"
                return ans, structured

        elif intent == "fraud_investigation":
            fr_res = results.get("FRAUD-1")
            if fr_res and fr_res.status == "success":
                data = fr_res.data
                structured = data
                ans = f"### Fraud Risk Assessment: {data.get('customer_id')}\n\n"
                ans += f"- **Overall Risk Level**: `{data.get('overall_risk')}` (Max Risk Score: **{data.get('max_risk_score')}/100**)\n"
                ans += f"- **Transactions Analyzed**: {data.get('analyzed_count')} | **Suspicious Count**: {data.get('suspicious_count')}\n\n"
                flagged = data.get("flagged_transactions", [])
                if flagged:
                    ans += "#### Flagged Transactions Requiring Review\n"
                    for f in flagged:
                        ans += f"- **`{f['transaction_id']}`** (₹{f['amount']:,.2f}): Risk Score **{f['risk_score']}** (`{f['risk_level']}`) — *{f['recommendation']}*\n"
                else:
                    ans += "No high-velocity bursts or abnormal deviations identified in recent activity.\n"
                return ans, structured

        elif intent == "explain_flagged_transaction" or intent == "analyze_single_transaction":
            fr_res = results.get("FRAUD-TXN-1")
            if fr_res and fr_res.status == "success":
                data = fr_res.data
                structured = data
                ans = f"### Analysis of Flagged Transaction: {data.get('transaction_id')}\n\n"
                ans += f"- **Amount**: ₹{data.get('amount', 0):,.2f} at *{data.get('merchant')}* ({data.get('location')})\n"
                ans += f"- **Risk Score**: **{data.get('risk_score')}/100** (`{data.get('risk_level')}`)\n"
                ans += f"- **Recommendation**: `{data.get('recommendation')}`\n\n"
                ans += "#### Triggered Rule Breakdown\n"
                for r in data.get("rule_analysis", []):
                    ans += f"- **[{r.get('severity')}] {r.get('rule')}**: {r.get('reason')}\n"
                ml = data.get("ml_anomaly_analysis", {})
                ans += f"\n#### Experimental ML Anomaly Output\n"
                ans += f"- **Model**: `{ml.get('model')}` | **Raw Score**: `{ml.get('raw_score')}` | **Anomaly**: `{ml.get('is_anomaly')}`\n"
                ans += f"> *{ml.get('disclaimer')}*"
                return ans, structured

        elif intent == "loan_eligibility":
            cr_res = results.get("LOAN-1")
            if cr_res and cr_res.status == "success":
                data = cr_res.data
                structured = data
                ans = f"### Loan Eligibility Evaluation for {data.get('customer_name')} ({data.get('customer_id')})\n\n"
                ans += f"- **Requested Principal**: ₹{data.get('requested_amount', 0):,.2f} for **{data.get('tenure_months')} months** @ {data.get('interest_rate')}% p.a.\n"
                ans += f"- **Estimated Monthly EMI**: **₹{data.get('estimated_emi', 0):,.2f}**\n"
                ans += f"- **Debt-to-Income (DTI)**: **{data.get('debt_to_income_ratio')}%**\n"
                ans += f"- **Assessment Result**: `{data.get('assessment_result')}`\n\n"
                ans += "#### Positive Factors\n"
                for p in data.get("positive_factors", []):
                    ans += f"- {p}\n"
                if data.get("caution_factors"):
                    ans += "\n#### Caution Factors\n"
                    for c in data.get("caution_factors", []):
                        ans += f"- {c}\n"
                ans += f"\n> *{data.get('disclaimer')}*"
                return ans, structured

        elif intent == "compare_loan_scenarios":
            cmp_res = results.get("COMPARE-1")
            if cmp_res and cmp_res.status == "success":
                data = cmp_res.data
                structured = data
                ans = "### Loan Scenarios Comparison\n\n"
                ans += "| Scenario | Principal | Tenure | Rate | Monthly EMI | Total Repayment | Total Interest |\n"
                ans += "|---|---|---|---|---|---|---|\n"
                for s in data.get("scenarios", []):
                    ans += f"| {s['scenario_id']} | ₹{s['principal']:,.2f} | {s['tenure_months']} mo | {s['interest_rate']}% | **₹{s['monthly_emi']:,.2f}** | ₹{s['total_repayment']:,.2f} | ₹{s['total_interest']:,.2f} |\n"
                ans += f"\n**Summary**: {data.get('comparison_summary')}\n"
                return ans, structured

        elif intent == "pending_loans":
            p_res = results.get("LOAN-PENDING-1")
            if p_res and p_res.status == "success":
                apps = p_res.data.get("applications", [])
                structured = p_res.data
                ans = "### Simulated Loan Applications\n\n"
                if not apps:
                    ans += "No loan applications currently on record."
                else:
                    ans += "| ID | Customer | Requested | EMI | DTI | Assessment | Status |\n"
                    ans += "|---|---|---|---|---|---|---|\n"
                    for a in apps:
                        ans += f"| `{a['application_id']}` | {a['customer_id']} | ₹{a['requested_amount']:,.2f} | ₹{a['estimated_emi']:,.2f} | {a['dti_ratio']}% | `{a['assessment_result']}` | `{a['approval_status']}` |\n"
                return ans, structured

        elif intent == "kyc_status":
            kyc_res = results.get("KYC-1")
            if kyc_res and kyc_res.status == "success":
                data = kyc_res.data
                structured = data
                ans = f"### KYC Verification Status: {data.get('name')} ({data.get('customer_id')})\n\n"
                ans += f"- **Overall Status**: `{data.get('kyc_status')}`\n"
                ans += f"- **Risk Rating**: `{data.get('risk_rating')}`\n\n"
                ans += "#### Checklist Verification\n"
                for doc, st in data.get("documents", {}).items():
                    ans += f"- **{doc.replace('_', ' ').title()}**: `{st}`\n"
                return ans, structured

        elif intent == "banking_policy":
            query = entities.get("query", "banking policies")
            db = get_task_session()
            try:
                rag_out = knowledge_service.search_policies(db, query, top_k=2)
                structured = rag_out
                ans = f"### Policy Knowledge Retrieval\n\n"
                if not rag_out.get("answer_supported"):
                    ans += rag_out.get("summary")
                else:
                    ans += f"**Primary Citation**: `{rag_out.get('primary_source')}`\n\n"
                    for m in rag_out.get("matches", []):
                        ans += f"#### [{m['document_id']}] {m['title']} ({m['version']})\n"
                        ans += f"> {m['supporting_passage']}\n\n"
                        ans += f"*Relevance Score: {m['relevance_score']}*\n\n"
                return ans, structured
            finally:
                db.close()

        elif intent == "combined_investigation":
            inv_res = results.get("INV-1")
            if inv_res and inv_res.status == "success":
                data = inv_res.data
                structured = data
                cid = data.get("customer_id")
                ans = f"## 360 Multi-Agent Investigation Report: {cid}\n\n"
                ans += f"**Investigation Reference**: `{data.get('investigation_id')}` | **Verdict**: `{data.get('risk_verdict')}`\n\n"
                ans += f"### Executive Summary\n{data.get('summary')}\n\n"

                findings = data.get("findings_by_agent", {})
                if "customer" in findings:
                    p = findings["customer"].get("profile", {})
                    ans += f"### 1. Customer Profile\n- Name: {p.get('name')} | City: {p.get('city')} | Income: ₹{p.get('monthly_income', 0):,.2f}\n\n"

                if "spend" in findings:
                    sp = findings["spend"]
                    ans += f"### 2. Transaction & Spending Insights\n- Monthly Outflow: ₹{sp.get('total_spend', 0):,.2f} across {sp.get('total_transactions', 0)} transactions.\n\n"

                if "fraud" in findings:
                    fr = findings["fraud"]
                    ans += f"### 3. Risk & Fraud Assessment\n- Risk Rating: `{fr.get('overall_risk')}` | Flagged Items: {fr.get('suspicious_count', 0)}\n\n"

                if "credit" in findings:
                    cr = findings["credit"]
                    ans += f"### 4. Credit & Loan Viability\n- Evaluated Amount: ₹{cr.get('requested_amount', 0):,.2f} | EMI: ₹{cr.get('estimated_emi', 0):,.2f} | DTI: {cr.get('debt_to_income_ratio')}%\n- Assessment: `{cr.get('assessment_result')}`\n\n"

                if "compliance" in findings:
                    comp = findings["compliance"]
                    ans += f"### 5. Regulatory Compliance\n- KYC Status: `{comp.get('kyc_status')}`\n\n"

                ans += "---\n*This report has been automatically saved to the enterprise investigations database.*"
                return ans, structured

        # Generic Fallback
        default_ans = f"Processed request for intent `{intent}`. "
        if errors:
            default_ans += f"Encountered {len(errors)} error(s): {', '.join(errors)}"
        return default_ans, structured

supervisor = SupervisorAgent()
