import re
from typing import Any
from pydantic import BaseModel, Field

class ParsedIntent(BaseModel):
    intent: str
    confidence: float = 1.0
    entities: dict[str, Any] = Field(default_factory=dict)
    clarification_prompt: str | None = None
    is_clarification_needed: bool = False

class IntentRouter:
    def parse_message(self, text: str) -> ParsedIntent:
        cleaned = text.strip()
        lower = cleaned.lower()

        # 1. Extract Entities
        entities: dict[str, Any] = {}
        
        # Customer ID (CUST1001 to CUST9999)
        cust_match = re.search(r"\b(CUST\d{4})\b", cleaned, re.IGNORECASE)
        if cust_match:
            entities["customer_id"] = cust_match.group(1).upper()

        # Transaction ID (TXN4001 to TXN9999)
        txn_match = re.search(r"\b(TXN\d{4})\b", cleaned, re.IGNORECASE)
        if txn_match:
            entities["transaction_id"] = txn_match.group(1).upper()

        # Account ID (ACC2001 to ACC9999)
        acc_match = re.search(r"\b(ACC\d{4})\b", cleaned, re.IGNORECASE)
        if acc_match:
            entities["account_id"] = acc_match.group(1).upper()

        # Amounts (₹500000, 500,000, 500000, 300000, 50k, etc.)
        amt_matches = re.findall(r"(?:₹|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:k|lakh)?", cleaned, re.IGNORECASE)
        parsed_amounts = []
        for m in amt_matches:
            val_str = m.replace(",", "")
            if val_str and val_str.isdigit():
                val = float(val_str)
                # Ignore small numbers that are probably months, counts, or IDs
                if val >= 1000:
                    parsed_amounts.append(val)
        if parsed_amounts:
            entities["amounts"] = parsed_amounts
            entities["amount"] = parsed_amounts[0]

        # Tenure in months (24 months, 36 months, etc.)
        tenure_match = re.search(r"(\d+)\s*(?:month|mo|year|yr)", lower)
        if tenure_match:
            val = int(tenure_match.group(1))
            if "year" in lower or "yr" in lower:
                entities["tenure_months"] = val * 12
            else:
                entities["tenure_months"] = val

        # 2. Match Specific Intents

        # Intent 11: Combined 360 Investigation
        if (
            ("investigate" in lower and ("transaction" in lower or "loan" in lower or "credit" in lower or "spending" in lower))
            or "combined" in lower
            or ("360" in lower and "report" in lower)
            or ("compliance" in lower and "loan" in lower and "spending" in lower)
        ):
            if "customer_id" not in entities:
                return ParsedIntent(
                    intent="combined_investigation",
                    is_clarification_needed=True,
                    clarification_prompt="Which customer would you like to investigate? Please provide a Customer ID (e.g., CUST1001)."
                )
            return ParsedIntent(intent="combined_investigation", entities=entities)

        # Intent 5: Flagged Transaction Explanation
        if ("why" in lower and ("flagged" in lower or "flag" in lower or "alert" in lower or "suspicious" in lower)) or ("explain" in lower and "flagged" in lower):
            if "transaction_id" not in entities:
                return ParsedIntent(
                    intent="explain_flagged_transaction",
                    is_clarification_needed=True,
                    clarification_prompt="Which transaction would you like explained? Please specify a Transaction ID (e.g., TXN4008)."
                )
            return ParsedIntent(intent="explain_flagged_transaction", entities=entities)

        # Intent 4: Fraud Investigation / Suspicious Activity Check
        if "fraud" in lower or "suspicious" in lower or ("analyze" in lower and "suspicious" in lower):
            if "transaction_id" in entities:
                return ParsedIntent(intent="analyze_single_transaction", entities=entities)
            if "customer_id" not in entities:
                return ParsedIntent(
                    intent="fraud_investigation",
                    is_clarification_needed=True,
                    clarification_prompt="Which customer would you like to analyze for suspicious activity? Please provide a Customer ID (e.g., CUST1003)."
                )
            return ParsedIntent(intent="fraud_investigation", entities=entities)

        # Intent 7: Compare EMIs / Scenarios
        if "compare" in lower and ("emi" in lower or "loan" in lower or "scenario" in lower):
            amounts = entities.get("amounts", [300000.0, 500000.0])
            if len(amounts) < 2:
                amounts = [300000.0, 500000.0]
            entities["compare_amounts"] = amounts
            entities["tenure_months"] = entities.get("tenure_months", 24)
            return ParsedIntent(intent="compare_loan_scenarios", entities=entities)

        # Intent 6: Loan Eligibility Assessment
        if ("loan" in lower and ("eligib" in lower or "evaluat" in lower or "check" in lower or "apply" in lower)) or "emi" in lower:
            if "customer_id" not in entities and "principal" not in entities and "amount" not in entities:
                return ParsedIntent(
                    intent="loan_eligibility",
                    is_clarification_needed=True,
                    clarification_prompt="Which customer should I evaluate for a loan? Please provide a Customer ID (e.g., CUST1001) and requested amount."
                )
            entities["amount"] = entities.get("amount", 500000.0)
            entities["tenure_months"] = entities.get("tenure_months", 36)
            return ParsedIntent(intent="loan_eligibility", entities=entities)

        # Intent 8: Pending Loan Applications Lookup
        if "pending" in lower and ("loan" in lower or "application" in lower):
            return ParsedIntent(intent="pending_loans", entities=entities)

        # Intent 9: KYC Status Check
        if "kyc" in lower or "cdd" in lower or "verification status" in lower:
            if "customer_id" not in entities:
                return ParsedIntent(
                    intent="kyc_status",
                    is_clarification_needed=True,
                    clarification_prompt="Which customer's KYC status would you like to check? Please provide a Customer ID (e.g., CUST1004)."
                )
            return ParsedIntent(intent="kyc_status", entities=entities)

        # Intent 10: Banking Policy Question
        if "policy" in lower or "sop" in lower or "regulation" in lower or "rule" in lower or "limit" in lower:
            entities["query"] = cleaned
            return ParsedIntent(intent="banking_policy", entities=entities)

        # Intent 3: Spending Analysis
        if "spend" in lower or "expense" in lower or "category" in lower or "cash flow" in lower or "inflow" in lower:
            if "customer_id" not in entities:
                return ParsedIntent(
                    intent="spending_analysis",
                    is_clarification_needed=True,
                    clarification_prompt="Which customer's spending would you like to analyze? Please specify a Customer ID (e.g., CUST1001)."
                )
            return ParsedIntent(intent="spending_analysis", entities=entities)

        # Intent 2: Transaction History
        if "transaction" in lower or "history" in lower or "statement" in lower or "recent" in lower:
            if "customer_id" not in entities:
                return ParsedIntent(
                    intent="transaction_history",
                    is_clarification_needed=True,
                    clarification_prompt="Which customer's transaction history would you like to see? Please provide a Customer ID (e.g., CUST1002)."
                )
            entities["limit"] = 5 if "five" in lower or "5" in lower else 10
            return ParsedIntent(intent="transaction_history", entities=entities)

        # Intent 1: Customer Account & Balance Inquiry
        if "balance" in lower or "account" in lower or "profile" in lower or "who is" in lower:
            if "customer_id" not in entities and "account_id" not in entities:
                return ParsedIntent(
                    intent="customer_account_inquiry",
                    is_clarification_needed=True,
                    clarification_prompt="Which customer would you like to look up? Please provide a Customer ID (e.g., CUST1001)."
                )
            return ParsedIntent(intent="customer_account_inquiry", entities=entities)

        # General customer lookup if only customer ID mentioned
        if "customer_id" in entities:
            return ParsedIntent(intent="customer_account_inquiry", entities=entities)

        # Default: General banking policy search or clarification
        return ParsedIntent(
            intent="banking_policy",
            entities={"query": cleaned},
            confidence=0.5
        )

intent_router = IntentRouter()
