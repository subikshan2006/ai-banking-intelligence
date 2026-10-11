import pytest
import concurrent.futures
from app.database import get_task_session
from app.models.customer import Customer
from app.services.simulation_service import simulation_service

def read_customer_in_thread(customer_id: str):
    db = get_task_session()
    try:
        c = db.query(Customer).filter(Customer.id == customer_id).first()
        return c.name if c else None
    finally:
        db.close()

def test_concurrent_sessions_under_wal_mode():
    """Verify that multiple concurrent threads acquire independent sessions without SQLite locking errors."""
    customer_ids = ["CUST1001", "CUST1002", "CUST1003", "CUST1004", "CUST1005"] * 4
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(read_customer_in_thread, customer_ids))
    assert len(results) == 20
    assert all(r is not None for r in results)

@pytest.mark.asyncio
async def test_simulator_start_generate_stop_lifecycle():
    # Start simulator
    start_res = simulation_service.start_simulation()
    assert start_res["status"] in ("STARTED", "ALREADY_RUNNING")
    assert simulation_service.is_running is True

    # Generate one demo transaction
    tx = await simulation_service.generate_single_transaction()
    assert "id" in tx
    assert "amount" in tx

    # Stop simulator
    stop_res = simulation_service.stop_simulation()
    assert stop_res["status"] == "STOPPED"
    assert simulation_service.is_running is False
