import time
import uuid
import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.agents.supervisor import supervisor
from app.models.evaluation import EvaluationRun
from app.schemas.evaluation import EvaluationCaseResult, EvaluationResponse

logger = logging.getLogger(__name__)

EVALUATION_TEST_CASES = [
    {
        "case_id": "CASE-01",
        "prompt": "Show customer CUST1001's account balance.",
        "expected_intent": "customer_account_inquiry",
        "expected_agent": "CustomerAgent"
    },
    {
        "case_id": "CASE-02",
        "prompt": "Show the latest five transactions for CUST1002.",
        "expected_intent": "transaction_history",
        "expected_agent": "CustomerAgent"
    },
    {
        "case_id": "CASE-03",
        "prompt": "Summarize CUST1001's spending this month.",
        "expected_intent": "spending_analysis",
        "expected_agent": "CustomerAgent"
    },
    {
        "case_id": "CASE-04",
        "prompt": "Analyze CUST1003 for suspicious transactions.",
        "expected_intent": "fraud_investigation",
        "expected_agent": "FraudAgent"
    },
    {
        "case_id": "CASE-05",
        "prompt": "Explain why transaction TXN4008 was flagged.",
        "expected_intent": "explain_flagged_transaction",
        "expected_agent": "FraudAgent"
    },
    {
        "case_id": "CASE-06",
        "prompt": "Evaluate a simulated ₹500000 loan for CUST1001 over 36 months.",
        "expected_intent": "loan_eligibility",
        "expected_agent": "CreditAgent"
    },
    {
        "case_id": "CASE-07",
        "prompt": "Compare EMIs for ₹300000 and ₹500000 over 24 months.",
        "expected_intent": "compare_loan_scenarios",
        "expected_agent": "CreditAgent"
    },
    {
        "case_id": "CASE-08",
        "prompt": "Show pending loan applications.",
        "expected_intent": "pending_loans",
        "expected_agent": "CreditAgent"
    },
    {
        "case_id": "CASE-09",
        "prompt": "Check the simulated KYC status of CUST1004.",
        "expected_intent": "kyc_status",
        "expected_agent": "ComplianceAgent"
    },
    {
        "case_id": "CASE-10",
        "prompt": "Find the policy related to unusual transactions.",
        "expected_intent": "banking_policy",
        "expected_agent": "SupervisorAgent"
    },
    {
        "case_id": "CASE-11",
        "prompt": "Investigate CUST1001's transactions and loan eligibility.",
        "expected_intent": "combined_investigation",
        "expected_agent": "InvestigationAgent"
    }
]

class EvaluationService:
    async def run_suite(self, db: Session) -> EvaluationResponse:
        results: list[EvaluationCaseResult] = []
        passed_count = 0
        total_count = len(EVALUATION_TEST_CASES)

        for case in EVALUATION_TEST_CASES:
            t_start = time.perf_counter()
            resp = await supervisor.process_request(case["prompt"])
            t_dur = round((time.perf_counter() - t_start) * 1000.0, 2)

            intent_match = (resp.intent == case["expected_intent"])
            agent_match = (case["expected_agent"] in resp.agents_involved) or (resp.intent == "banking_policy")
            
            passed = intent_match and (resp.status == "completed")
            if passed:
                passed_count += 1

            details = f"Intent match: {intent_match} ({resp.intent}). Agents: {resp.agents_involved}."
            if not passed:
                details += f" Failure reason: Expected {case['expected_intent']} vs {resp.intent}."

            results.append(EvaluationCaseResult(
                case_id=case["case_id"],
                prompt=case["prompt"],
                expected_intent=case["expected_intent"],
                actual_intent=resp.intent,
                expected_agents=[case["expected_agent"]],
                actual_agents=resp.agents_involved,
                status="PASSED" if passed else "FAILED",
                grounded=bool(resp.answer and len(resp.answer) > 20),
                execution_time_ms=t_dur,
                details=details
            ))

        accuracy = round((passed_count / total_count) * 100.0, 1) if total_count > 0 else 0.0
        eval_id = f"EVAL{uuid.uuid4().hex[:6].upper()}"

        # Persist run to database
        run_record = EvaluationRun(
            id=eval_id,
            timestamp=datetime.utcnow(),
            total_cases=total_count,
            passed_cases=passed_count,
            accuracy_rate=accuracy,
            mode="deterministic_fallback" if not supervisor.agents_map else "deterministic_fallback",
            case_results=json.dumps([r.model_dump() for r in results])
        )
        db.add(run_record)
        db.commit()

        return EvaluationResponse(
            evaluation_id=eval_id,
            timestamp=datetime.utcnow().isoformat(),
            total_cases=total_count,
            passed_cases=passed_count,
            accuracy_rate=accuracy,
            mode=run_record.mode,
            results=results
        )

    def get_runs(self, db: Session, limit: int = 10) -> list[dict]:
        runs = db.query(EvaluationRun).order_by(EvaluationRun.timestamp.desc()).limit(limit).all()
        return [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat(),
                "total_cases": r.total_cases,
                "passed_cases": r.passed_cases,
                "accuracy_rate": r.accuracy_rate,
                "mode": r.mode,
                "case_results": json.loads(r.case_results)
            }
            for r in runs
        ]

evaluation_service = EvaluationService()
