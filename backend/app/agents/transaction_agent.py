from typing import Any
from sqlalchemy.orm import Session
from app.agents.base_agent import BaseAgent
from app.schemas.agents import ToolCallRecord

class TransactionAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="TransactionAgent",
            description="Analyzes category spending breakdowns, period-over-period trends, and cash flow velocity."
        )

    def analyze_categories(self, arguments: dict[str, Any], correlation_id: str, db: Session, tool_calls: list[ToolCallRecord]):
        cust_id = arguments.get("customer_id")
        period = arguments.get("period_days", 30)
        if not cust_id:
            raise ValueError("customer_id is required.")

        output = self.execute_tool("analyze_spending_categories", {"customer_id": cust_id, "period_days": period}, correlation_id, db, tool_calls)
        return output, [{"type": "category_analysis", "categories_count": len(output.get("categories", []))}]

    def compare_periods(self, arguments: dict[str, Any], correlation_id: str, db: Session, tool_calls: list[ToolCallRecord]):
        cust_id = arguments.get("customer_id")
        curr = arguments.get("current_days", 30)
        prior = arguments.get("prior_days", 30)
        if not cust_id:
            raise ValueError("customer_id is required.")

        output = self.execute_tool("compare_spending_periods", {"customer_id": cust_id, "current_days": curr, "prior_days": prior}, correlation_id, db, tool_calls)
        return output, [{"type": "trend_comparison", "trend": output.get("trend")}]

    def cash_flow(self, arguments: dict[str, Any], correlation_id: str, db: Session, tool_calls: list[ToolCallRecord]):
        cust_id = arguments.get("customer_id")
        period = arguments.get("period_days", 30)
        if not cust_id:
            raise ValueError("customer_id is required.")

        output = self.execute_tool("calculate_cash_flow", {"customer_id": cust_id, "period_days": period}, correlation_id, db, tool_calls)
        return output, [{"type": "cash_flow", "savings_rate": output.get("savings_rate_percentage")}]

transaction_agent = TransactionAgent()
