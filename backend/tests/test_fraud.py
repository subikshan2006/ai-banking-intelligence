def test_list_fraud_alerts(client):
    response = client.get("/api/fraud/alerts")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 4
    assert len(data["alerts"]) >= 4

def test_detect_spike_suspicious_transaction(client):
    # TXN4008 is the known spike transfer of ₹450,000
    response = client.post("/api/fraud/analyze", json={"transaction_id": "TXN4008"})
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] >= 75
    assert data["risk_level"] == "HIGH"
    assert any("HIGH_AMOUNT_VS_HISTORICAL_BASELINE" in r["rule_name"] for r in data["rule_hits"])
    # Verify ML output is populated
    assert "raw_anomaly_score" in data["ml_output"]
    assert "disclaimer" in data["ml_output"]

def test_normal_transaction_not_flagged_as_high_risk(client):
    # TXN4002 is routine groceries of ₹1,250
    response = client.post("/api/fraud/analyze", json={"transaction_id": "TXN4002"})
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] < 45
    assert data["risk_level"] == "LOW"
    assert data["recommendation"] == "Approve"

def test_explain_flagged_transaction(client):
    response = client.get("/api/fraud/transaction/TXN4008")
    assert response.status_code == 200
    data = response.json()
    assert data["transaction_id"] == "TXN4008"
    assert len(data["rule_analysis"]) > 0
    assert "verdict_summary" in data
