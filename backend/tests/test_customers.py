def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["registered_tools"] > 10

def test_get_customers_list(client):
    response = client.get("/api/customers")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 15
    assert len(data["customers"]) >= 15
    assert data["customers"][0]["id"] == "CUST1001"

def test_get_customer_details(client):
    response = client.get("/api/customers/CUST1001")
    assert response.status_code == 200
    data = response.json()
    assert data["customer"]["name"] == "Aarav Sharma"
    assert len(data["accounts"]) >= 1
    # Check that account number is masked
    assert data["accounts"][0]["masked_account_number"].startswith("****-****-")

def test_get_unknown_customer_returns_404(client):
    response = client.get("/api/customers/CUST9999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_get_customer_accounts(client):
    response = client.get("/api/customers/CUST1001/accounts")
    assert response.status_code == 200
    accounts = response.json()
    assert len(accounts) >= 1
    assert accounts[0]["currency"] == "INR"

def test_get_customer_transactions(client):
    response = client.get("/api/customers/CUST1001/transactions?limit=5")
    assert response.status_code == 200
    txs = response.json()
    assert len(txs) <= 5
    assert all("amount" in t for t in txs)
