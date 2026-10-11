from typing import Any
from sqlalchemy.orm import Session
from app.agents.base_agent import BaseAgent
from app.schemas.agents import ToolCallRecord

class ComplianceAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ComplianceAgent",
            description="Verifies customer KYC compliance, document checklist status, and sample regulatory standards."
        )

    def check_kyc(self, arguments: dict[str, Any], correlation_id: str, db: Session, tool_calls: list[ToolCallRecord]):
        cust_id = arguments.get("customer_id")
        if not cust_id:
            raise ValueError("customer_id is required.")

        output = self.execute_tool("get_kyc_status", {"customer_id": cust_id}, correlation_id, db, tool_calls)
        evidence = {
            "type": "kyc_status",
            "customer_id": cust_id,
            "kyc_status": output.get("kyc_status")
        }
        return output, [evidence]

    def evaluate_compliance(self, arguments: dict[str, Any], correlation_id: str, db: Session, tool_calls: list[ToolCallRecord]):
        cust_id = arguments.get("customer_id")
        context = arguments.get("context", "retail_lending")
        if not cust_id:
            raise ValueError("customer_id is required.")

        output = self.execute_tool("evaluate_compliance", {"customer_id": cust_id, "context": context}, correlation_id, db, tool_calls)
        evidence = {
            "type": "compliance_evaluation",
            "verdict": output.get("compliance_verdict"),
            "policies": output.get("referenced_policies")
        }
        return output, [evidence]

compliance_agent = ComplianceAgent()
