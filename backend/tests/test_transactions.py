def test_list_transactions(client):
    response = client.get("/api/transactions?limit=20")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 100
    assert len(data["transactions"]) == 20

def test_filter_transactions_by_category(client):
    response = client.get("/api/transactions?category=Salary")
    assert response.status_code == 200
    txs = response.json()["transactions"]
    assert len(txs) > 0
    assert all(t["category"] == "Salary" for t in txs)

def test_filter_transactions_by_flagged(client):
    response = client.get("/api/transactions?is_flagged=true")
    assert response.status_code == 200
    txs = response.json()["transactions"]
    assert len(txs) > 0
    assert all(t["is_flagged"] is True for t in txs)

def test_get_single_transaction(client):
    response = client.get("/api/transactions/TXN4001")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "TXN4001"
    assert data["customer_id"] == "CUST1001"

def test_get_nonexistent_transaction(client):
    response = client.get("/api/transactions/TXN9999")
    assert response.status_code == 404
