import json
import uuid
from datetime import datetime
from typing import Any
from sqlalchemy.orm import Session
from app.agents.base_agent import BaseAgent
from app.schemas.agents import ToolCallRecord
from app.models.investigation import Investigation

class InvestigationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="InvestigationAgent",
            description="Synthesizes customer, fraud, transaction, credit, and compliance evidence into consolidated 360 investigation reports."
        )

    def synthesize_report(
        self,
        arguments: dict[str, Any],
        correlation_id: str,
        db: Session,
        tool_calls: list[ToolCallRecord]
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        customer_id = arguments.get("customer_id", "UNKNOWN")
        findings = arguments.get("findings", {})
        
        # Analyze findings across dimensions
        customer_info = findings.get("customer", {})
        fraud_info = findings.get("fraud", {})
        spending_info = findings.get("spending", {})
        credit_info = findings.get("credit", {})
        compliance_info = findings.get("compliance", {})

        # Risk Verdict Computation
        fraud_risk = fraud_info.get("overall_risk", "LOW")
        dti = credit_info.get("debt_to_income_ratio", 0.0)
        kyc = compliance_info.get("kyc_status", customer_info.get("kyc_status", "VERIFIED"))

        if fraud_risk == "HIGH" or dti > 60.0 or kyc == "REJECTED":
            verdict = "SUSPICIOUS_ACTIVITY"
            summary_statement = f"Comprehensive 360 review for {customer_id} identified high-severity risk indicators. "
        elif fraud_risk == "MEDIUM" or dti > 45.0 or kyc == "PENDING":
            verdict = "NEEDS_MONITORING"
            summary_statement = f"Comprehensive 360 review for {customer_id} identified moderate concerns requiring review. "
        else:
            verdict = "NORMAL"
            summary_statement = f"Comprehensive 360 review for {customer_id} confirms satisfactory operational health. "

        if fraud_risk != "LOW":
            summary_statement += f"Fraud monitoring detected {fraud_info.get('suspicious_count', 1)} anomalous item(s). "
        if credit_info:
            summary_statement += f"Projected loan eligibility assessed at {credit_info.get('assessment_result', 'N/A')} with DTI {dti}%. "
        if kyc != "VERIFIED":
            summary_statement += f"Compliance status is {kyc}. "

        inv_id = f"INV{uuid.uuid4().hex[:8].upper()}"
        report_data = {
            "investigation_id": inv_id,
            "correlation_id": correlation_id,
            "customer_id": customer_id,
            "risk_verdict": verdict,
            "summary": summary_statement,
            "findings_by_agent": findings,
            "created_at": datetime.utcnow().isoformat()
        }

        # Save to database
        inv_record = Investigation(
            id=inv_id,
            correlation_id=correlation_id,
            customer_id=customer_id,
            title=f"360 Multi-Agent Investigation - {customer_id}",
            summary=summary_statement,
            full_report=json.dumps(report_data),
            agents_involved=json.dumps(list(findings.keys())),
            risk_verdict=verdict,
            status="COMPLETED"
        )
        db.add(inv_record)
        db.commit()

        evidence = [{
            "type": "investigation_report",
            "investigation_id": inv_id,
            "verdict": verdict,
            "saved_to_db": True
        }]

        return report_data, evidence

investigation_agent = InvestigationAgent()
