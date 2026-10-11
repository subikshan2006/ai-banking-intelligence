from typing import Any

class MockExternalService:
    """Mock adapters for illustrative third-party banking ecosystem integrations."""

    def query_credit_bureau(self, customer_id: str, pan: str = "") -> dict[str, Any]:
        # Deterministic simulation based on customer ID digit
        seed_val = int(customer_id[-1]) if customer_id[-1].isdigit() else 5
        score = 650 + (seed_val * 25)
        return {
            "bureau_name": "Simulated Credit Information Bureau (CIBIL/Experian)",
            "customer_id": customer_id,
            "credit_score": min(850, score),
            "score_band": "EXCELLENT" if score > 750 else ("GOOD" if score > 700 else "FAIR"),
            "active_credit_lines": 2 + (seed_val % 3),
            "delinquencies_last_24m": 1 if score < 700 else 0,
            "disclaimer": "Simulated Credit Bureau adapter response for MVP demonstration."
        }

    def verify_national_id(self, customer_id: str, id_number: str) -> dict[str, Any]:
        return {
            "authority": "Simulated National Identity Authority (UIDAI/NSDL)",
            "id_type": "AADHAAR_PAN_LINKED",
            "status": "VALID",
            "biometric_matched": True,
            "disclaimer": "Simulated Identity Authority adapter."
        }

    def verify_payment_route(self, routing_code: str, amount: float) -> dict[str, Any]:
        return {
            "network": "Simulated National Payment Gateway (UPI/NEFT/RTGS)",
            "route_status": "ONLINE",
            "clearing_speed": "IMMEDIATE",
            "estimated_settlement_seconds": 1.2
        }

mock_external_service = MockExternalService()
