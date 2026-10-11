from app.tools.loan_tools import compute_emi

def test_deterministic_emi_calculation():
    # Principal 500,000, 10.5% per annum, 36 months
    emi = compute_emi(principal=500000.0, annual_rate=10.5, tenure_months=36)
    # Amortization check: 500000 * 0.00875 * (1.00875^36) / (1.00875^36 - 1) approx 16254.83
    assert 16250.0 < emi < 16260.0

def test_zero_interest_rate_emi():
    emi = compute_emi(principal=120000.0, annual_rate=0.0, tenure_months=12)
    assert emi == 10000.0

def test_evaluate_loan_eligible_customer(client):
    payload = {
        "customer_id": "CUST1001",
        "requested_amount": 500000.0,
        "tenure_months": 36,
        "purpose": "Home Renovation"
    }
    response = client.post("/api/loans/evaluate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == "CUST1001"
    assert data["assessment_result"] == "ELIGIBLE"
    assert data["debt_to_income_ratio"] <= 40.0
    assert len(data["positive_factors"]) > 0

def test_compare_loan_scenarios(client):
    payload = {
        "scenarios": [
            {"principal": 300000.0, "tenure_months": 24, "interest_rate": 10.5},
            {"principal": 500000.0, "tenure_months": 24, "interest_rate": 10.5}
        ]
    }
    response = client.post("/api/loans/compare", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["scenarios"]) == 2
    assert data["scenarios"][1]["monthly_emi"] > data["scenarios"][0]["monthly_emi"]
    assert "comparison_summary" in data
