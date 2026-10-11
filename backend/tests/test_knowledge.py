def test_search_loan_policy(client):
    response = client.get("/api/knowledge/search?query=loan%20eligibility%20DTI%20limits")
    assert response.status_code == 200
    data = response.json()
    assert data["answer_supported"] is True
    assert "POL-001" in data["primary_source"]
    assert len(data["matches"]) > 0

def test_search_fraud_policy(client):
    response = client.get("/api/knowledge/search?query=unusual%20transactions%20monitoring")
    assert response.status_code == 200
    data = response.json()
    assert data["answer_supported"] is True
    assert any(m["document_id"] == "POL-002" for m in data["matches"])

def test_unrelated_query_indicates_unsupported(client):
    response = client.get("/api/knowledge/search?query=quantum%20astrophysics%20black%20holes")
    assert response.status_code == 200
    data = response.json()
    assert data["answer_supported"] is False
    assert "not contain enough information" in data["summary"].lower()

def test_list_all_policies(client):
    response = client.get("/api/knowledge/policies")
    assert response.status_code == 200
    policies = response.json()
    assert len(policies) == 5
