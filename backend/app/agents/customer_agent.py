from typing import Any
from sqlalchemy.orm import Session
from app.agents.base_agent import BaseAgent
from app.schemas.agents import ToolCallRecord

class CustomerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="CustomerAgent",
            description="Manages customer banking profiles, account balances, transaction records, and PII masking."
        )

    def get_profile(self, arguments: dict[str, Any], correlation_id: str, db: Session, tool_calls: list[ToolCallRecord]):
        cust_id = arguments.get("customer_id")
        if not cust_id:
            raise ValueError("customer_id is required.")
        output = self.execute_tool("get_customer", {"customer_id": cust_id}, correlation_id, db, tool_calls)
        return output, [{"type": "customer_profile", "source": "core_banking", "customer_id": cust_id}]

    def get_accounts(self, arguments: dict[str, Any], correlation_id: str, db: Session, tool_calls: list[ToolCallRecord]):
        cust_id = arguments.get("customer_id")
        if not cust_id:
            raise ValueError("customer_id is required.")
        output = self.execute_tool("get_customer_accounts", {"customer_id": cust_id}, correlation_id, db, tool_calls)
        return {"accounts": output}, [{"type": "account_listing", "account_count": len(output)}]

    def get_balance(self, arguments: dict[str, Any], correlation_id: str, db: Session, tool_calls: list[ToolCallRecord]):
        acc_id = arguments.get("account_id")
        cust_id = arguments.get("customer_id")
        
        # If customer_id provided but not account_id, look up first primary account
        if not acc_id and cust_id:
            accounts = self.execute_tool("get_customer_accounts", {"customer_id": cust_id}, correlation_id, db, tool_calls)
            if not accounts:
                raise ValueError(f"No accounts found for customer '{cust_id}'.")
            acc_id = accounts[0]["account_id"]

        if not acc_id:
            raise ValueError("Either account_id or customer_id is required to fetch balance.")

        output = self.execute_tool("get_account_balance", {"account_id": acc_id}, correlation_id, db, tool_calls)
        return output, [{"type": "ledger_balance", "account_id": acc_id, "balance": output.get("balance")}]

    def get_recent_transactions(self, arguments: dict[str, Any], correlation_id: str, db: Session, tool_calls: list[ToolCallRecord]):
        cust_id = arguments.get("customer_id")
        limit = arguments.get("limit", 5)
        category = arguments.get("category")
        if not cust_id:
            raise ValueError("customer_id is required.")

        output = self.execute_tool("get_transactions", {"customer_id": cust_id, "limit": limit, "category": category}, correlation_id, db, tool_calls)
        return {"transactions": output, "count": len(output)}, [{"type": "transaction_history", "count": len(output)}]

    def get_spending_summary(self, arguments: dict[str, Any], correlation_id: str, db: Session, tool_calls: list[ToolCallRecord]):
        cust_id = arguments.get("customer_id")
        period = arguments.get("period_days", 30)
        if not cust_id:
            raise ValueError("customer_id is required.")

        output = self.execute_tool("summarize_transactions", {"customer_id": cust_id, "period_days": period}, correlation_id, db, tool_calls)
        return output, [{"type": "spending_summary", "net_cashflow": output.get("net_cashflow")}]

    def customer_360(self, arguments: dict[str, Any], correlation_id: str, db: Session, tool_calls: list[ToolCallRecord]):
        cust_id = arguments.get("customer_id")
        if not cust_id:
            raise ValueError("customer_id is required.")

        profile = self.execute_tool("get_customer", {"customer_id": cust_id}, correlation_id, db, tool_calls)
        accounts = self.execute_tool("get_customer_accounts", {"customer_id": cust_id}, correlation_id, db, tool_calls)
        txs = self.execute_tool("get_transactions", {"customer_id": cust_id, "limit": 10}, correlation_id, db, tool_calls)
        summary = self.execute_tool("summarize_transactions", {"customer_id": cust_id, "period_days": 30}, correlation_id, db, tool_calls)

        return {
            "profile": profile,
            "accounts": accounts,
            "recent_transactions": txs,
            "spending_summary": summary
        }, [{"type": "customer_360", "customer_id": cust_id}]

customer_agent = CustomerAgent()
