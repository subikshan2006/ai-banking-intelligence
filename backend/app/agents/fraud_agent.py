from typing import Any
from sqlalchemy.orm import Session
from app.agents.base_agent import BaseAgent
from app.schemas.agents import ToolCallRecord

class FraudAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="FraudAgent",
            description="Evaluates transactions for fraudulent anomalies, velocity spikes, duplicate charges, and explains risk scores."
        )

    def analyze_transaction(self, arguments: dict[str, Any], correlation_id: str, db: Session, tool_calls: list[ToolCallRecord]):
        tx_id = arguments.get("transaction_id")
        if not tx_id:
            raise ValueError("transaction_id is required.")

        output = self.execute_tool("analyze_transaction", {"transaction_id": tx_id}, correlation_id, db, tool_calls)
        evidence = {
            "type": "fraud_evaluation",
            "transaction_id": tx_id,
            "risk_score": output.get("risk_score"),
            "risk_level": output.get("risk_level"),
            "triggered_rules_count": len(output.get("rule_hits", []))
        }
        return output, [evidence]

    def analyze_customer(self, arguments: dict[str, Any], correlation_id: str, db: Session, tool_calls: list[ToolCallRecord]):
        cust_id = arguments.get("customer_id")
        if not cust_id:
            raise ValueError("customer_id is required.")

        output = self.execute_tool("analyze_customer_transactions", {"customer_id": cust_id}, correlation_id, db, tool_calls)
        evidence = {
            "type": "customer_risk_profile",
            "customer_id": cust_id,
            "overall_risk": output.get("overall_risk"),
            "suspicious_count": output.get("suspicious_count")
        }
        return output, [evidence]

    def explain_flagged(self, arguments: dict[str, Any], correlation_id: str, db: Session, tool_calls: list[ToolCallRecord]):
        tx_id = arguments.get("transaction_id")
        if not tx_id:
            raise ValueError("transaction_id is required.")

        output = self.execute_tool("explain_flagged_transaction", {"transaction_id": tx_id}, correlation_id, db, tool_calls)
        evidence = {
            "type": "flag_explanation",
            "transaction_id": tx_id,
            "verdict": output.get("recommendation")
        }
        return output, [evidence]

    def get_alerts(self, arguments: dict[str, Any], correlation_id: str, db: Session, tool_calls: list[ToolCallRecord]):
        cust_id = arguments.get("customer_id")
        output = self.execute_tool("get_fraud_alerts", {"customer_id": cust_id}, correlation_id, db, tool_calls)
        return {"alerts": output}, [{"type": "fraud_alerts", "count": len(output)}]

fraud_agent = FraudAgent()
