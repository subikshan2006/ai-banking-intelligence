from typing import Any
from sqlalchemy.orm import Session
from app.agents.base_agent import BaseAgent
from app.schemas.agents import ToolCallRecord

class CreditAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="CreditAgent",
            description="Performs loan eligibility assessments, deterministic EMI calculations, DTI analysis, and what-if scenarios."
        )

    def evaluate_loan(self, arguments: dict[str, Any], correlation_id: str, db: Session, tool_calls: list[ToolCallRecord]):
        cust_id = arguments.get("customer_id")
        amount = float(arguments.get("amount", arguments.get("requested_amount", 500000.0)))
        tenure = int(arguments.get("tenure_months", 36))
        purpose = arguments.get("purpose", "Personal")

        if not cust_id:
            raise ValueError("customer_id is required.")

        output = self.execute_tool(
            "evaluate_loan_eligibility",
            {"customer_id": cust_id, "requested_amount": amount, "tenure_months": tenure, "purpose": purpose},
            correlation_id,
            db,
            tool_calls
        )
        evidence = {
            "type": "loan_assessment",
            "customer_id": cust_id,
            "assessment_result": output.get("assessment_result"),
            "dti_ratio": output.get("debt_to_income_ratio"),
            "monthly_emi": output.get("estimated_emi")
        }
        return output, [evidence]

    def calculate_emi(self, arguments: dict[str, Any], correlation_id: str, db: Session, tool_calls: list[ToolCallRecord]):
        principal = float(arguments.get("principal", arguments.get("amount", 500000.0)))
        rate = float(arguments.get("interest_rate", 10.5))
        tenure = int(arguments.get("tenure_months", 36))

        output = self.execute_tool(
            "calculate_monthly_emi",
            {"principal": principal, "annual_interest_rate": rate, "tenure_months": tenure},
            correlation_id,
            db,
            tool_calls
        )
        return output, [{"type": "emi_calculation", "monthly_emi": output.get("monthly_emi")}]

    def compare_scenarios(self, arguments: dict[str, Any], correlation_id: str, db: Session, tool_calls: list[ToolCallRecord]):
        scenarios = arguments.get("scenarios", [])
        if not scenarios:
            raise ValueError("scenarios list is required.")

        output = self.execute_tool("compare_loan_scenarios", {"scenarios": scenarios}, correlation_id, db, tool_calls)
        return output, [{"type": "scenario_comparison", "scenarios_count": len(output.get("scenarios", []))}]

    def get_applications(self, arguments: dict[str, Any], correlation_id: str, db: Session, tool_calls: list[ToolCallRecord]):
        cust_id = arguments.get("customer_id")
        output = self.execute_tool("get_loan_applications", {"customer_id": cust_id}, correlation_id, db, tool_calls)
        return {"applications": output}, [{"type": "loan_applications", "count": len(output)}]

credit_agent = CreditAgent()
